"""
Detects the current active PoE2 league from the official leagues API.
"""

import logging
from datetime import datetime, timezone

import httpx

from poe_tablet_tool.config import settings
from poe_tablet_tool.db.connection import get_connection

logger = logging.getLogger(__name__)

TRADE_LEAGUES_URL = "https://www.pathofexile.com/api/trade2/data/leagues"


def _fetch_trade_leagues() -> list[dict]:
    """
    Use the trade API's own leagues endpoint — this is the authoritative source
    for what league names the trade search endpoint accepts.
    """
    resp = httpx.get(
        TRADE_LEAGUES_URL,
        headers=settings.request_headers,
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json().get("result", [])


def _pick_current_league(leagues: list[dict]) -> str | None:
    """
    Return the softcore trade temp league (no HC/SSF/Ruthless modifier).
    The trade API leagues endpoint lists current leagues for PoE2 in order.
    """
    skip_substrings = ("Hardcore", "HC ", "HC$", "SSF", "Ruthless", "Standard")
    skip_exact = {"Standard", "Hardcore"}

    for league in leagues:
        name: str = league.get("id", "")
        if not name:
            continue
        if name in skip_exact:
            continue
        if any(s.rstrip("$") in name for s in skip_substrings):
            continue
        return name
    return None


def detect_league() -> str:
    """
    Return the current active league name. If auto-detection is disabled,
    return the configured league name.
    """
    if not settings.current_league_auto:
        if not settings.league_name:
            raise ValueError("CURRENT_LEAGUE_AUTO=false but LEAGUE_NAME is not set.")
        return settings.league_name

    leagues = _fetch_trade_leagues()
    name = _pick_current_league(leagues)
    if not name:
        raise RuntimeError("Could not detect a current temp league from the API.")
    logger.info("Detected current league: %s", name)
    return name


def ensure_league_in_db(league_name: str) -> int:
    """
    Upsert the league into the leagues table. Returns the league id.
    Marks all other leagues as inactive if this one is new.
    """
    conn = get_connection()
    now = datetime.now(timezone.utc).isoformat()

    row = conn.execute(
        "SELECT id, is_active FROM leagues WHERE name = ?", (league_name,)
    ).fetchone()

    if row:
        league_id = row["id"]
        if not row["is_active"]:
            conn.execute(
                "UPDATE leagues SET is_active = 1 WHERE id = ?", (league_id,)
            )
            conn.commit()
        return league_id

    # New league — deactivate old ones first
    conn.execute("UPDATE leagues SET is_active = 0, ended_at = ? WHERE is_active = 1", (now,))
    cursor = conn.execute(
        "INSERT INTO leagues (name, started_at, is_active) VALUES (?, ?, 1)",
        (league_name, now),
    )
    conn.commit()
    logger.info("Registered new league in DB: %s (id=%d)", league_name, cursor.lastrowid)
    return cursor.lastrowid
