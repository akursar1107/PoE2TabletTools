"""
Currency conversion: normalizes listing prices to divine orbs and persists rates.
"""

import logging
from datetime import datetime, timezone

from poe_tablet_tool.config import settings
from poe_tablet_tool.db.connection import get_connection

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_divine_rate(currency: str | None) -> float | None:
    """Return how many units of `currency` equal one divine (for division)."""
    if not currency:
        return None
    key = currency.lower()
    if key == "divine":
        return 1.0
    if key == "chaos":
        return settings.chaos_per_divine
    if key in ("exalted", "exalt"):
        return 1.0 / settings.exalt_per_divine if settings.exalt_per_divine else None
    return None


def to_divine(amount: float | None, currency: str | None) -> float | None:
    if amount is None or currency is None:
        return None
    rate = get_divine_rate(currency)
    if rate is None or rate == 0:
        return None
    if currency.lower() == "divine":
        return float(amount)
    return float(amount) / rate


def refresh_rates(league_id: int) -> None:
    """Store configured exchange rates for the active league."""
    conn = get_connection()
    now = _now()
    pairs = [
        ("divine", "chaos", settings.chaos_per_divine),
        ("exalted", "divine", settings.exalt_per_divine),
    ]
    for base, quote, rate in pairs:
        conn.execute(
            """
            INSERT INTO exchange_rates (league_id, taken_at, base_currency, quote_currency, rate)
            VALUES (?, ?, ?, ?, ?)
            """,
            (league_id, now, base, quote, rate),
        )
    conn.commit()
    logger.debug("Refreshed exchange rates for league_id=%d", league_id)


def latest_chaos_per_divine(league_id: int) -> float:
    conn = get_connection()
    row = conn.execute(
        """
        SELECT rate FROM exchange_rates
        WHERE league_id = ? AND base_currency = 'divine' AND quote_currency = 'chaos'
        ORDER BY id DESC LIMIT 1
        """,
        (league_id,),
    ).fetchone()
    return float(row["rate"]) if row else settings.chaos_per_divine
