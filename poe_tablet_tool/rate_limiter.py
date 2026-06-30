"""
Rate limiter that reads PoE trade API response headers and enforces limits.

The API communicates limits via:
  X-Rate-Limit-Rules: account,ip
  X-Rate-Limit-Account: 8:10:60,15:60:120   (max:window_sec:ban_sec per rule)
  X-Rate-Limit-Account-State: 1:10:0,1:60:0  (current:window_sec:active_ban)
  Retry-After: 30  (only when 429)
"""

import logging
import time
from dataclasses import dataclass, field
from threading import Lock

import httpx

logger = logging.getLogger(__name__)


@dataclass
class RuleState:
    max_hits: int
    window_sec: int
    ban_sec: int
    current_hits: int = 0
    active_ban: int = 0


class EndpointLimiter:
    """Tracks rate limit state for a single endpoint category (SEARCH or FETCH)."""

    def __init__(self, name: str) -> None:
        self.name = name
        self._lock = Lock()
        self._rules: list[RuleState] = []

    def update_from_headers(self, headers: httpx.Headers) -> None:
        rules_header = headers.get("x-rate-limit-rules")
        if not rules_header:
            return

        rule_names = [r.strip() for r in rules_header.split(",")]
        new_rules: list[RuleState] = []

        for rule_name in rule_names:
            limit_str = headers.get(f"x-rate-limit-{rule_name}", "")
            state_str = headers.get(f"x-rate-limit-{rule_name}-state", "")
            if not limit_str or not state_str:
                continue

            for limit_part, state_part in zip(limit_str.split(","), state_str.split(",")):
                try:
                    max_h, win, ban = (int(x) for x in limit_part.split(":"))
                    cur, _, active_ban = (int(x) for x in state_part.split(":"))
                    new_rules.append(RuleState(max_h, win, ban, cur, active_ban))
                except ValueError:
                    continue

        with self._lock:
            self._rules = new_rules

    def wait_if_needed(self) -> None:
        """Block until it's safe to make a request."""
        with self._lock:
            for rule in self._rules:
                if rule.active_ban > 0:
                    logger.warning(
                        "[%s] Rate limit ban active, sleeping %ds", self.name, rule.active_ban
                    )
                    time.sleep(rule.active_ban + 1)
                    rule.active_ban = 0

                if rule.current_hits >= rule.max_hits - 1:
                    sleep_for = rule.window_sec / rule.max_hits
                    logger.debug(
                        "[%s] Near rate limit (%d/%d), sleeping %.1fs",
                        self.name,
                        rule.current_hits,
                        rule.max_hits,
                        sleep_for,
                    )
                    time.sleep(sleep_for)

    def handle_429(self, retry_after: int) -> None:
        wait = max(retry_after, 10)
        logger.warning("[%s] 429 received, sleeping %ds", self.name, wait)
        time.sleep(wait)


_search_limiter = EndpointLimiter("SEARCH")
_fetch_limiter = EndpointLimiter("FETCH")


def get_search_limiter() -> EndpointLimiter:
    return _search_limiter


def get_fetch_limiter() -> EndpointLimiter:
    return _fetch_limiter
