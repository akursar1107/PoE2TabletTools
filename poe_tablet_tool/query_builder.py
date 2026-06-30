"""
Builds PoE2 trade API query payloads for rare and magic tablet searches.
"""

import hashlib
import json
from typing import Literal

from poe_tablet_tool.config import settings
from poe_tablet_tool.tablets import TabletType

RARE_MODE = "rare"
MAGIC_MODE = "magic"
NORMAL_MODE = "normal"

SortDirection = Literal["asc", "desc"]


def _base_query(
    tablet: TabletType,
    league: str,
    query_mode: str,
    sort: SortDirection = "asc",
) -> dict:
    if query_mode == RARE_MODE:
        price_min = settings.price_min_divine_rare
    elif query_mode == MAGIC_MODE:
        price_min = settings.price_min_divine_magic
    else:
        price_min = settings.price_min_divine_normal
    payload: dict = {
        "query": {
            "status": {"option": "online"},
            "type": tablet.ref_name,
            "stats": [{"type": "and", "filters": []}],
            "filters": {
                "trade_filters": {
                    "filters": {},
                }
            },
        },
        "sort": {"price": sort},
    }
    if price_min > 0:
        payload["query"]["filters"]["trade_filters"]["filters"]["price"] = {
            "min": price_min,
            "option": "divine",
        }
    return payload


def build_rare_query(
    tablet: TabletType,
    league: str,
    sort: SortDirection = "asc",
) -> tuple[dict, str]:
    """
    Query for rare tablets. Affix count (4–5) is enforced in the parser filter.
    Returns (payload, query_hash).
    """
    payload = _base_query(tablet, league, RARE_MODE, sort=sort)
    payload["query"]["filters"]["type_filters"] = {
        "filters": {"rarity": {"option": "rare"}}
    }
    return payload, _hash_query(payload)


def build_magic_query(
    tablet: TabletType,
    league: str,
    sort: SortDirection = "asc",
) -> tuple[dict, str]:
    """
    Query for magic tablets. Two-mod filter is enforced in the parser filter.
    Returns (payload, query_hash).
    """
    payload = _base_query(tablet, league, MAGIC_MODE, sort=sort)
    payload["query"]["filters"]["type_filters"] = {
        "filters": {"rarity": {"option": "magic"}}
    }
    return payload, _hash_query(payload)


def build_normal_query(
    tablet: TabletType,
    league: str,
    sort: SortDirection = "asc",
) -> tuple[dict, str]:
    """
    Query for normal (0-mod) tablets. Filter is enforced in the parser filter.
    Returns (payload, query_hash).
    """
    payload = _base_query(tablet, league, NORMAL_MODE, sort=sort)
    payload["query"]["filters"]["type_filters"] = {
        "filters": {"rarity": {"option": "normal"}}
    }
    return payload, _hash_query(payload)


def _hash_query(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]
