"""
Calls the PoE2 trade API: search endpoint then fetch endpoint in batches of 10.
Respects rate limits and retries on transient errors.
Supports dual-sort fetching (cheapest + most expensive) for better market coverage.
"""

import logging
import random
import time
from typing import Any

import httpx

from poe_tablet_tool.config import settings
from poe_tablet_tool.rate_limiter import get_fetch_limiter, get_search_limiter

logger = logging.getLogger(__name__)

FETCH_BATCH_SIZE = 10
MAX_FETCH_IDS = 100
MAX_RETRIES = 5  # Increased from 3 for better resilience
RETRY_BACKOFF_BASE = 2  # Exponential backoff: 2, 4, 8, 16, 32 seconds


def _make_client() -> httpx.Client:
    return httpx.Client(
        headers=settings.request_headers,
        timeout=30,
        follow_redirects=True,
    )


def _post_with_retry(
    client: httpx.Client, url: str, json_body: dict, limiter=None
) -> dict:
    last_exc = None
    for attempt in range(MAX_RETRIES):
        if limiter:
            limiter.wait_if_needed()
        try:
            resp = client.post(url, json=json_body)
            if limiter:
                limiter.update_from_headers(resp.headers)

            # Check for rate limiting or server errors
            if resp.status_code in (429, 503):
                retry_after = int(
                    resp.headers.get("retry-after", RETRY_BACKOFF_BASE**attempt)
                )
                if limiter and resp.status_code == 429:
                    limiter.handle_429(retry_after)
                sleep_time = retry_after + random.uniform(0, 1)  # Add jitter
                logger.warning(
                    "Rate limit/server error (%d) on %s, attempt %d/%d, retrying in %.1fs",
                    resp.status_code,
                    url,
                    attempt + 1,
                    MAX_RETRIES,
                    sleep_time,
                )
                time.sleep(sleep_time)
                continue

            resp.raise_for_status()
            data = resp.json()
            if "error" in data and data["error"]:
                raise RuntimeError(f"API error: {data['error']}")
            return data
        except httpx.HTTPStatusError as exc:
            last_exc = exc
            logger.warning(
                "HTTP error (%d) on attempt %d/%d: %s",
                exc.response.status_code if exc.response else 0,
                attempt + 1,
                MAX_RETRIES,
                exc,
            )
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_BACKOFF_BASE**attempt + random.uniform(0, 1))
        except httpx.TimeoutError as exc:
            last_exc = exc
            logger.warning(
                "Timeout on attempt %d/%d: %s", attempt + 1, MAX_RETRIES, exc
            )
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_BACKOFF_BASE**attempt + random.uniform(0, 1))
        except httpx.RequestError as exc:
            last_exc = exc
            logger.warning(
                "Request error on attempt %d/%d: %s", attempt + 1, MAX_RETRIES, exc
            )
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_BACKOFF_BASE**attempt + random.uniform(0, 1))

    raise RuntimeError(f"Failed after {MAX_RETRIES} attempts: POST {url}") from last_exc


def _get_with_retry(client: httpx.Client, url: str, limiter=None) -> dict:
    last_exc = None
    for attempt in range(MAX_RETRIES):
        if limiter:
            limiter.wait_if_needed()
        try:
            resp = client.get(url)
            if limiter:
                limiter.update_from_headers(resp.headers)
            
            # Check for rate limiting or server errors
            if resp.status_code in (429, 503):
                retry_after = int(resp.headers.get("retry-after", RETRY_BACKOFF_BASE ** attempt))
                if limiter and resp.status_code == 429:
                    limiter.handle_429(retry_after)
                sleep_time = retry_after + random.uniform(0, 1)  # Add jitter
                logger.warning(
                    "Rate limit/server error (%d) on %s, attempt %d/%d, retrying in %.1fs",
                    resp.status_code, url, attempt + 1, MAX_RETRIES, sleep_time
                )
                time.sleep(sleep_time)
                continue
            
            resp.raise_for_status()
            data = resp.json()
            if "error" in data and data["error"]:
                raise RuntimeError(f"API error: {data['error']}")
            return data
        except httpx.HTTPStatusError as exc:
            last_exc = exc
            logger.warning("HTTP error (%d) on attempt %d/%d: %s", 
                          exc.response.status_code if exc.response else 0,
                          attempt + 1, MAX_RETRIES, exc)
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_BACKOFF_BASE ** attempt + random.uniform(0, 1))
        except httpx.TimeoutError as exc:
            last_exc = exc
            logger.warning("Timeout on attempt %d/%d: %s", attempt + 1, MAX_RETRIES, exc)
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_BACKOFF_BASE ** attempt + random.uniform(0, 1))
        except httpx.RequestError as exc:
            last_exc = exc
            logger.warning("Request error on attempt %d/%d: %s", attempt + 1, MAX_RETRIES, exc)
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_BACKOFF_BASE ** attempt + random.uniform(0, 1))
    
    raise RuntimeError(f"Failed after {MAX_RETRIES} attempts: GET {url}") from last_exc


def search_trade(league: str, query_payload: dict) -> tuple[str, list[str], int]:
    """
    POST to trade search endpoint.
    Returns (query_id, result_ids, total_count).
    result_ids is capped at MAX_FETCH_IDS.
    """
    url = f"{settings.trade_base_url}/api/trade2/search/{league}"
    search_limiter = get_search_limiter()

    with _make_client() as client:
        data = _post_with_retry(client, url, query_payload, limiter=search_limiter)

    query_id: str = data["id"]
    result_ids: list[str] = data.get("result", [])[:MAX_FETCH_IDS]
    total: int = data.get("total", len(result_ids))

    logger.info(
        "Search returned %d results (total=%d), query_id=%s",
        len(result_ids),
        total,
        query_id,
    )
    return query_id, result_ids, total


def fetch_listings(query_id: str, result_ids: list[str]) -> list[dict[str, Any]]:
    """
    Fetch full item data for result_ids in batches of FETCH_BATCH_SIZE.
    Returns list of raw listing dicts from the API.
    """
    if not result_ids:
        return []

    fetch_limiter = get_fetch_limiter()
    all_results: list[dict] = []

    with _make_client() as client:
        for i in range(0, len(result_ids), FETCH_BATCH_SIZE):
            batch = result_ids[i : i + FETCH_BATCH_SIZE]
            ids_str = ",".join(batch)
            url = (
                f"{settings.trade_base_url}/api/trade2/fetch/{ids_str}?query={query_id}"
            )
            data = _get_with_retry(client, url, limiter=fetch_limiter)
            results = [r for r in data.get("result", []) if r is not None]
            all_results.extend(results)
            logger.debug(
                "Fetched batch %d-%d: %d items", i, i + len(batch), len(results)
            )

    return all_results


def search_and_fetch_dual(
    league: str,
    payload_asc: dict,
    payload_desc: dict,
) -> tuple[list[dict[str, Any]], int, int]:
    """
    Run two searches (price asc + desc), fetch both result sets, dedupe by item id.
    Returns (raw_results, total_count, fetched_count).
    """
    query_id_asc, ids_asc, total_asc = search_trade(league, payload_asc)
    raw_asc = fetch_listings(query_id_asc, ids_asc)

    seen_ids = {r.get("id") for r in raw_asc if r.get("id")}
    query_id_desc, ids_desc, total_desc = search_trade(league, payload_desc)
    new_ids = [i for i in ids_desc if i not in seen_ids]

    raw_desc = fetch_listings(query_id_desc, new_ids) if new_ids else []
    combined = raw_asc + raw_desc
    total_count = max(total_asc, total_desc)
    fetched_count = len(ids_asc) + len(new_ids)

    logger.info(
        "Dual fetch: total=%d, fetched=%d, unique_items=%d",
        total_count,
        fetched_count,
        len(combined),
    )
    return combined, total_count, fetched_count
