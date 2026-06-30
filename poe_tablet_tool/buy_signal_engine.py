"""
Project-craft edge and buy signal evaluation for 2-mod magic tablets.
"""

import logging
from datetime import datetime, timezone

from poe_tablet_tool.config import settings
from poe_tablet_tool.db.connection import get_connection
from poe_tablet_tool.query_builder import MAGIC_MODE, RARE_MODE

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


def _pair_key(mod_a_id: str, mod_b_id: str) -> str:
    return "|".join(sorted([mod_a_id, mod_b_id]))


def _rare_prices_for_pair(
    conn, league_id: int, floor_snapshot_id: int, tablet_type: str, mod_a_id: str, mod_b_id: str
) -> list[float]:
    rows = conn.execute(
        """
        SELECT DISTINCT l.item_id, l.price_divine
        FROM listings l
        WHERE l.league_id = ?
          AND l.tablet_type = ?
          AND l.query_mode = ?
          AND l.snapshot_id >= ?
          AND l.affix_count IN (4, 5)
          AND l.price_divine IS NOT NULL
          AND l.status = 'likely_sold'
          AND EXISTS (
              SELECT 1 FROM affixes a
              WHERE a.listing_id = l.id AND a.mod_id = ?
          )
          AND EXISTS (
              SELECT 1 FROM affixes a
              WHERE a.listing_id = l.id AND a.mod_id = ?
          )
        """,
        (league_id, tablet_type, RARE_MODE, floor_snapshot_id, mod_a_id, mod_b_id),
    ).fetchall()
    return [float(r["price_divine"]) for r in rows if r["price_divine"] is not None]


def _live_magic_buy_price(
    conn, league_id: int, tablet_type: str, mod_a_id: str, mod_b_id: str
) -> float | None:
    row = conn.execute(
        """
        SELECT MIN(l.price_divine) AS min_price
        FROM listings l
        JOIN snapshots s ON l.snapshot_id = s.id
        WHERE l.league_id = ?
          AND l.tablet_type = ?
          AND l.query_mode = ?
          AND l.status = 'active'
          AND l.price_divine IS NOT NULL
          AND s.id = (
              SELECT MAX(id) FROM snapshots
              WHERE league_id = ? AND tablet_type = ? AND query_mode = ?
          )
          AND EXISTS (SELECT 1 FROM affixes a WHERE a.listing_id = l.id AND a.mod_id = ?)
          AND EXISTS (SELECT 1 FROM affixes a WHERE a.listing_id = l.id AND a.mod_id = ?)
        """,
        (
            league_id,
            tablet_type,
            MAGIC_MODE,
            league_id,
            tablet_type,
            MAGIC_MODE,
            mod_a_id,
            mod_b_id,
        ),
    ).fetchone()
    return float(row["min_price"]) if row and row["min_price"] is not None else None


def run_buy_signal_engine(league_id: int, floor_snapshot_id: int) -> int:
    conn = get_connection()
    now = _now()
    regal = settings.regal_cost_divine

    conn.execute("DELETE FROM crafting_edge WHERE league_id = ?", (league_id,))

    seeds = conn.execute(
        """
        SELECT tablet_type, mod_a_id, mod_b_id, mod_pair_key, magic_median_price_div,
               magic_sold_count
        FROM magic_seed_pairs
        WHERE league_id = ?
        """,
        (league_id,),
    ).fetchall()

    written = 0
    for seed in seeds:
        rare_prices = _rare_prices_for_pair(
            conn,
            league_id,
            floor_snapshot_id,
            seed["tablet_type"],
            seed["mod_a_id"],
            seed["mod_b_id"],
        )
        if len(rare_prices) < 2:
            continue

        rare_median = _median(rare_prices)
        if rare_median is None:
            continue

        magic_buy = _live_magic_buy_price(
            conn,
            league_id,
            seed["tablet_type"],
            seed["mod_a_id"],
            seed["mod_b_id"],
        )
        if magic_buy is None:
            magic_buy = seed["magic_median_price_div"]

        if magic_buy is None:
            continue

        profit_floor = magic_buy + regal
        below = sum(1 for p in rare_prices if p < profit_floor)
        junk_rate = below / len(rare_prices)
        expected_profit = rare_median - magic_buy - regal
        sample = seed["magic_sold_count"] + len(rare_prices)
        confidence = min(1.0, sample / 20.0)

        is_buy = int(
            expected_profit >= settings.buy_signal_min_profit_div
            and junk_rate <= settings.buy_signal_max_junk_rate
            and confidence >= settings.buy_signal_min_confidence
        )

        conn.execute(
            """
            INSERT INTO crafting_edge (
                league_id, tablet_type, mod_a_id, mod_b_id, mod_pair_key,
                magic_buy_price_div, magic_median_price_div, rare_median_price_div,
                regal_cost_div, expected_profit_div, junk_rate, confidence,
                is_buy_signal, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                league_id,
                seed["tablet_type"],
                seed["mod_a_id"],
                seed["mod_b_id"],
                seed["mod_pair_key"],
                magic_buy,
                seed["magic_median_price_div"],
                rare_median,
                regal,
                expected_profit,
                junk_rate,
                confidence,
                is_buy,
                now,
            ),
        )
        written += 1

    conn.commit()
    logger.info("buy_signal_engine wrote %d crafting_edge rows", written)
    return written
