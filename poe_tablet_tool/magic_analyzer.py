"""
Magic 2-mod seed pair analytics.
"""

import logging
from datetime import datetime, timezone

from poe_tablet_tool.db.connection import get_connection
from poe_tablet_tool.query_builder import MAGIC_MODE

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _pair_key(mod_a_id: str, mod_b_id: str) -> str:
    ordered = sorted([mod_a_id, mod_b_id])
    return f"{ordered[0]}|{ordered[1]}"


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2


def run_magic_analyzer(league_id: int, floor_snapshot_id: int) -> int:
    conn = get_connection()
    now = _now()
    conn.execute("DELETE FROM magic_seed_pairs WHERE league_id = ?", (league_id,))

    listings = conn.execute(
        """
        SELECT l.id, l.item_id, l.tablet_type, l.status, l.price_divine
        FROM listings l
        WHERE l.league_id = ?
          AND l.query_mode = ?
          AND l.snapshot_id >= ?
          AND l.affix_count = 2
        """,
        (league_id, MAGIC_MODE, floor_snapshot_id),
    ).fetchall()

    pairs: dict[tuple[str, str], dict] = {}
    for listing in listings:
        affixes = conn.execute(
            """
            SELECT mod_id, mod_text FROM affixes
            WHERE listing_id = ? AND slot NOT IN ('implicit', 'crafted')
            ORDER BY mod_index
            """,
            (listing["id"],),
        ).fetchall()
        if len(affixes) != 2:
            continue

        mod_a, mod_b = affixes[0], affixes[1]
        key = (listing["tablet_type"], _pair_key(mod_a["mod_id"], mod_b["mod_id"]))
        bucket = pairs.setdefault(
            key,
            {
                "mod_a_id": mod_a["mod_id"],
                "mod_b_id": mod_b["mod_id"],
                "mod_a_text": mod_a["mod_text"],
                "mod_b_text": mod_b["mod_text"],
                "sold_prices": [],
                "sold_count": 0,
            },
        )
        if listing["status"] == "likely_sold":
            bucket["sold_count"] += 1
            if listing["price_divine"] is not None:
                bucket["sold_prices"].append(float(listing["price_divine"]))

    written = 0
    for (tablet_type, pair_key), bucket in pairs.items():
        conn.execute(
            """
            INSERT INTO magic_seed_pairs (
                league_id, tablet_type, mod_a_id, mod_b_id, mod_a_text, mod_b_text,
                mod_pair_key, magic_sold_count, magic_median_price_div,
                magic_avg_time_to_disappear_hours, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?)
            """,
            (
                league_id,
                tablet_type,
                bucket["mod_a_id"],
                bucket["mod_b_id"],
                bucket["mod_a_text"],
                bucket["mod_b_text"],
                pair_key,
                bucket["sold_count"],
                _median(bucket["sold_prices"]),
                now,
            ),
        )
        written += 1

    conn.commit()
    logger.info("magic_analyzer wrote %d seed pair rows", written)
    return written
