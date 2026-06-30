"""
Sell-side affix analytics for 4–5 mod rare tablets.
"""

import logging
from datetime import datetime, timezone

from poe_tablet_tool.db.connection import get_connection
from poe_tablet_tool.query_builder import RARE_MODE

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2


def run_rare_analyzer(league_id: int, floor_snapshot_id: int) -> int:
    conn = get_connection()
    now = _now()

    conn.execute(
        "DELETE FROM rare_affix_stats WHERE league_id = ?",
        (league_id,),
    )

    affix_rows = conn.execute(
        """
        SELECT a.mod_id, a.slot, a.mod_text, a.mod_family, l.tablet_type,
               l.item_id, l.status, l.price_divine
        FROM affixes a
        JOIN listings l ON a.listing_id = l.id
        WHERE l.league_id = ?
          AND l.query_mode = ?
          AND l.snapshot_id >= ?
          AND a.slot NOT IN ('implicit', 'crafted')
          AND l.affix_count IN (4, 5)
        """,
        (league_id, RARE_MODE, floor_snapshot_id),
    ).fetchall()

    stats: dict[tuple[str, str, str], dict] = {}
    for row in affix_rows:
        key = (row["tablet_type"], row["mod_id"], row["slot"])
        bucket = stats.setdefault(
            key,
            {
                "mod_text": row["mod_text"],
                "mod_family": row["mod_family"],
                "sold_items": set(),
                "active_items": set(),
                "sold_prices": [],
            },
        )
        if row["status"] == "likely_sold":
            bucket["sold_items"].add(row["item_id"])
            if row["price_divine"] is not None:
                bucket["sold_prices"].append(float(row["price_divine"]))
        else:
            bucket["active_items"].add(row["item_id"])

    total_sold_items = len(
        {
            r["item_id"]
            for r in affix_rows
            if r["status"] == "likely_sold"
        }
    )
    total_active_items = len(
        {
            r["item_id"]
            for r in affix_rows
            if r["status"] != "likely_sold"
        }
    )

    written = 0
    for (tablet_type, mod_id, slot), bucket in stats.items():
        sold_count = len(bucket["sold_items"])
        active_count = len(bucket["active_items"])
        sold_freq = sold_count / total_sold_items if total_sold_items else 0.0
        active_freq = active_count / total_active_items if total_active_items else 0.0
        lift = sold_freq / active_freq if active_freq > 0 else 0.0

        conn.execute(
            """
            INSERT INTO rare_affix_stats (
                league_id, tablet_type, mod_id, slot, mod_text, mod_family,
                sold_count, active_count, sold_frequency, active_frequency,
                lift, median_sold_price_div, avg_time_to_disappear_hours, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?)
            """,
            (
                league_id,
                tablet_type,
                mod_id,
                slot,
                bucket["mod_text"],
                bucket["mod_family"],
                sold_count,
                active_count,
                sold_freq,
                active_freq,
                lift,
                _median(bucket["sold_prices"]),
                now,
            ),
        )
        written += 1

    conn.commit()
    logger.info("rare_analyzer wrote %d affix stat rows", written)
    return written
