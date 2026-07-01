"""
Report queries shared by the API and dashboard.
"""

from poe_tablet_tool.db.connection import get_connection
from poe_tablet_tool.snapshot_store import analysis_floor_snapshot_id

MAX_DIV = 2000


def _rows_to_dicts(rows) -> list[dict]:
    return [dict(r) for r in rows]


def get_active_league_id() -> int | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT id FROM leagues WHERE is_active = 1 ORDER BY id DESC LIMIT 1"
    ).fetchone()
    return int(row["id"]) if row else None


def affix_frequency(league_id: int, limit: int = 40) -> list[dict]:
    floor = analysis_floor_snapshot_id(league_id)
    conn = get_connection()
    return _rows_to_dicts(
        conn.execute(
            """
            SELECT a.mod_family, a.slot, l.tablet_type,
                   COUNT(*) AS n,
                   ROUND(AVG(l.price_divine), 1) AS avg_div,
                   ROUND(MIN(l.price_divine), 1) AS min_div,
                   ROUND(MAX(l.price_divine), 1) AS max_div
            FROM affixes a
            JOIN listings l ON a.listing_id = l.id
            WHERE l.league_id = ?
              AND l.price_divine IS NOT NULL
              AND l.price_divine <= ?
              AND a.slot NOT IN ('implicit', 'crafted')
              AND l.snapshot_id >= ?
            GROUP BY a.mod_family, a.slot, l.tablet_type
            ORDER BY n DESC, avg_div DESC
            LIMIT ?
            """,
            (league_id, MAX_DIV, floor, limit),
        ).fetchall()
    )


def affix_price(league_id: int, limit: int = 20) -> list[dict]:
    floor = analysis_floor_snapshot_id(league_id)
    conn = get_connection()
    return _rows_to_dicts(
        conn.execute(
            """
            SELECT a.mod_family,
                   ROUND(AVG(l.price_divine), 1) AS avg_div,
                   ROUND(MIN(l.price_divine), 1) AS min_div,
                   ROUND(MAX(l.price_divine), 1) AS max_div,
                   COUNT(*) AS n
            FROM affixes a
            JOIN listings l ON a.listing_id = l.id
            WHERE l.league_id = ?
              AND l.price_divine IS NOT NULL
              AND l.price_divine <= ?
              AND a.slot NOT IN ('implicit', 'crafted')
              AND l.snapshot_id >= ?
            GROUP BY a.mod_family
            HAVING n >= 3
            ORDER BY avg_div DESC
            LIMIT ?
            """,
            (league_id, MAX_DIV, floor, limit),
        ).fetchall()
    )


def affix_velocity(league_id: int, limit: int = 20) -> list[dict]:
    floor = analysis_floor_snapshot_id(league_id)
    conn = get_connection()
    return _rows_to_dicts(
        conn.execute(
            """
            SELECT a.mod_family, l.tablet_type,
                   COUNT(DISTINCT l.item_id) AS total,
                   COUNT(DISTINCT ld.item_id) AS gone,
                   ROUND(
                       100.0 * COUNT(DISTINCT ld.item_id) / COUNT(DISTINCT l.item_id),
                       0
                   ) AS pct,
                   ROUND(AVG(l.price_divine), 1) AS avg_div
            FROM affixes a
            JOIN listings l ON a.listing_id = l.id
            LEFT JOIN listing_disappearances ld
              ON ld.item_id = l.item_id
             AND ld.tablet_type = l.tablet_type
             AND ld.classified_as = 'likely_sold'
            WHERE l.league_id = ?
              AND l.snapshot_id >= ?
              AND l.price_divine IS NOT NULL
              AND l.price_divine <= ?
              AND a.slot NOT IN ('implicit', 'crafted')
            GROUP BY a.mod_family, l.tablet_type
            HAVING total >= 3
            ORDER BY pct DESC, avg_div DESC
            LIMIT ?
            """,
            (league_id, floor, MAX_DIV, limit),
        ).fetchall()
    )


def price_over_time(league_id: int) -> list[dict]:
    floor = analysis_floor_snapshot_id(league_id)
    conn = get_connection()
    return _rows_to_dicts(
        conn.execute(
            """
            SELECT s.id AS snap, substr(s.taken_at, 1, 16) AS ts, l.tablet_type,
                   ROUND(AVG(l.price_divine), 1) AS avg_div
            FROM listings l
            JOIN snapshots s ON l.snapshot_id = s.id
            WHERE l.league_id = ?
              AND l.price_divine IS NOT NULL
              AND l.price_divine <= ?
              AND l.query_mode = 'rare'
              AND l.snapshot_id >= ?
            GROUP BY l.snapshot_id, l.tablet_type
            ORDER BY s.id
            """,
            (league_id, MAX_DIV, floor),
        ).fetchall()
    )


def normal_prices(league_id: int) -> list[dict]:
    """Get current normal (0-mod) tablet prices by type."""
    floor = analysis_floor_snapshot_id(league_id)
    conn = get_connection()
    return _rows_to_dicts(
        conn.execute(
            """
            SELECT l.tablet_type,
                   COUNT(*) AS count,
                   ROUND(MIN(l.price_divine), 2) AS min_div,
                   ROUND(MAX(l.price_divine), 2) AS max_div,
                   ROUND(AVG(l.price_divine), 2) AS avg_div
            FROM listings l
            JOIN snapshots s ON l.snapshot_id = s.id
            WHERE l.league_id = ?
              AND l.query_mode = 'normal'
              AND l.price_divine IS NOT NULL
              AND l.price_divine <= ?
              AND l.snapshot_id >= ?
            GROUP BY l.tablet_type
            ORDER BY avg_div DESC
            """,
            (league_id, MAX_DIV, floor),
        ).fetchall()
    )


def normal_price_history(league_id: int) -> list[dict]:
    """Get normal tablet price history over time by type."""
    floor = analysis_floor_snapshot_id(league_id)
    conn = get_connection()
    return _rows_to_dicts(
        conn.execute(
            """
            SELECT s.id AS snap, substr(s.taken_at, 1, 16) AS ts, l.tablet_type,
                   ROUND(AVG(l.price_divine), 2) AS avg_div,
                   COUNT(*) AS count
            FROM listings l
            JOIN snapshots s ON l.snapshot_id = s.id
            WHERE l.league_id = ?
              AND l.query_mode = 'normal'
              AND l.price_divine IS NOT NULL
              AND l.price_divine <= ?
              AND l.snapshot_id >= ?
            GROUP BY l.snapshot_id, l.tablet_type
            ORDER BY s.id, l.tablet_type
            """,
            (league_id, MAX_DIV, floor),
        ).fetchall()
    )


def price_distribution(league_id: int) -> list[dict]:
    floor = analysis_floor_snapshot_id(league_id)
    conn = get_connection()
    return _rows_to_dicts(
        conn.execute(
            """
            SELECT tablet_type,
                   CASE
                       WHEN price_divine < 100 THEN '50-100'
                       WHEN price_divine < 200 THEN '100-200'
                       WHEN price_divine < 500 THEN '200-500'
                       ELSE '500+'
                   END AS bucket,
                   COUNT(*) AS n
            FROM listings
            WHERE league_id = ?
              AND price_divine IS NOT NULL
              AND price_divine <= ?
              AND snapshot_id >= ?
            GROUP BY tablet_type, bucket
            ORDER BY tablet_type, bucket
            """,
            (league_id, MAX_DIV, floor),
        ).fetchall()
    )


def affix_combos(league_id: int, limit: int = 20) -> list[dict]:
    floor = analysis_floor_snapshot_id(league_id)
    conn = get_connection()
    return _rows_to_dicts(
        conn.execute(
            """
            SELECT a1.mod_family AS mod_a, a2.mod_family AS mod_b, l.tablet_type,
                   COUNT(*) AS n,
                   ROUND(AVG(l.price_divine), 1) AS avg_div
            FROM affixes a1
            JOIN affixes a2 ON a1.listing_id = a2.listing_id AND a1.id < a2.id
            JOIN listings l ON a1.listing_id = l.id
            WHERE l.league_id = ?
              AND l.snapshot_id >= ?
              AND l.price_divine <= ?
              AND l.price_divine IS NOT NULL
              AND a1.slot NOT IN ('implicit', 'crafted')
              AND a2.slot NOT IN ('implicit', 'crafted')
            GROUP BY a1.mod_family, a2.mod_family, l.tablet_type
            ORDER BY avg_div DESC, n DESC
            LIMIT ?
            """,
            (league_id, floor, MAX_DIV, limit),
        ).fetchall()
    )


def rare_affix_lift(league_id: int, limit: int = 30) -> list[dict]:
    conn = get_connection()
    return _rows_to_dicts(
        conn.execute(
            """
            SELECT tablet_type, mod_family, slot, lift, sold_count, active_count,
                   median_sold_price_div
            FROM rare_affix_stats
            WHERE league_id = ?
            ORDER BY lift DESC, sold_count DESC
            LIMIT ?
            """,
            (league_id, limit),
        ).fetchall()
    )


def buy_signals(league_id: int, limit: int = 30) -> list[dict]:
    conn = get_connection()
    return _rows_to_dicts(
        conn.execute(
            """
            SELECT tablet_type, mod_a_id, mod_b_id, magic_buy_price_div,
                   rare_median_price_div, expected_profit_div, junk_rate, confidence
            FROM crafting_edge
            WHERE league_id = ? AND is_buy_signal = 1
            ORDER BY expected_profit_div DESC
            LIMIT ?
            """,
            (league_id, limit),
        ).fetchall()
    )


def regex_outputs(league_id: int) -> list[dict]:
    conn = get_connection()
    return _rows_to_dicts(
        conn.execute(
            """
            SELECT tablet_type, regex_mode, label, regex_text, char_count
            FROM regex_outputs
            WHERE league_id = ?
            ORDER BY regex_mode, tablet_type
            """,
            (league_id,),
        ).fetchall()
    )


def price_spread_analysis(league_id: int) -> list[dict]:
    """
    Calculate price spread between normal, magic, and rare tablets.
    Shows the markup for mods on each tablet type.
    """
    floor = analysis_floor_snapshot_id(league_id)
    conn = get_connection()
    return _rows_to_dicts(
        conn.execute(
            """
            SELECT
                l.tablet_type,
                l.query_mode,
                COUNT(*) as count,
                ROUND(MIN(l.price_divine), 2) as min_div,
                ROUND(MAX(l.price_divine), 2) as max_div,
                ROUND(AVG(l.price_divine), 2) as avg_div,
                ROUND(SQRT(MAX(AVG(l.price_divine * l.price_divine) - AVG(l.price_divine) * AVG(l.price_divine), 0)), 2) as stddev_div
            FROM listings l
            JOIN snapshots s ON l.snapshot_id = s.id
            WHERE l.league_id = ?
              AND l.price_divine IS NOT NULL
              AND l.price_divine <= ?
              AND l.snapshot_id >= ?
            GROUP BY l.tablet_type, l.query_mode
            ORDER BY l.tablet_type,
                     CASE l.query_mode
                         WHEN 'normal' THEN 1
                         WHEN 'magic' THEN 2
                         WHEN 'rare' THEN 3
                     END
            """,
            (league_id, MAX_DIV, floor),
        ).fetchall()
    )


def price_spread_summary(league_id: int) -> list[dict]:
    """
    Calculate spread multipliers: magic/normal and rare/normal price ratios.
    """
    floor = analysis_floor_snapshot_id(league_id)
    conn = get_connection()
    return _rows_to_dicts(
        conn.execute(
            """
            SELECT
                t.tablet_type,
                ROUND(AVG(CASE WHEN l.query_mode = 'normal' THEN l.price_divine END), 2) as normal_avg,
                ROUND(AVG(CASE WHEN l.query_mode = 'magic' THEN l.price_divine END), 2) as magic_avg,
                ROUND(AVG(CASE WHEN l.query_mode = 'rare' THEN l.price_divine END), 2) as rare_avg,
                ROUND(
                    AVG(CASE WHEN l.query_mode = 'magic' THEN l.price_divine END) /
                    NULLIF(AVG(CASE WHEN l.query_mode = 'normal' THEN l.price_divine END), 0),
                    2
                ) as magic_normal_ratio,
                ROUND(
                    AVG(CASE WHEN l.query_mode = 'rare' THEN l.price_divine END) /
                    NULLIF(AVG(CASE WHEN l.query_mode = 'normal' THEN l.price_divine END), 0),
                    2
                ) as rare_normal_ratio,
                COUNT(DISTINCT CASE WHEN l.query_mode = 'normal' THEN l.id END) as normal_count,
                COUNT(DISTINCT CASE WHEN l.query_mode = 'magic' THEN l.id END) as magic_count,
                COUNT(DISTINCT CASE WHEN l.query_mode = 'rare' THEN l.id END) as rare_count
            FROM listings l
            JOIN snapshots s ON l.snapshot_id = s.id
            JOIN (
                SELECT DISTINCT tablet_type FROM snapshots WHERE league_id = ?
            ) t ON l.tablet_type = t.tablet_type
            WHERE l.league_id = ?
              AND l.price_divine IS NOT NULL
              AND l.price_divine <= ?
              AND l.snapshot_id >= ?
            GROUP BY t.tablet_type
            ORDER BY rare_normal_ratio DESC
            """,
            (league_id, league_id, MAX_DIV, floor),
        ).fetchall()
    )


def crafting_profitability(league_id: int) -> list[dict]:
    """
    Calculate crafting profitability: normal + regal -> magic/rare.
    Assumes regal cost from config (REGAL_COST_DIVINE).
    """
    from poe_tablet_tool.config import settings

    floor = analysis_floor_snapshot_id(league_id)
    regal_cost = settings.regal_cost_divine
    conn = get_connection()

    return _rows_to_dicts(
        conn.execute(
            """
            WITH mode_prices AS (
                SELECT
                    l.tablet_type,
                    l.query_mode,
                    AVG(l.price_divine) as avg_price,
                    COUNT(*) as count
                FROM listings l
                JOIN snapshots s ON l.snapshot_id = s.id
                WHERE l.league_id = ?
                  AND l.price_divine IS NOT NULL
                  AND l.price_divine <= ?
                  AND l.snapshot_id >= ?
                GROUP BY l.tablet_type, l.query_mode
            )
            SELECT
                mp1.tablet_type,
                ROUND(mp1.avg_price, 2) as normal_price,
                ROUND(mp2.avg_price, 2) as magic_price,
                ROUND(mp3.avg_price, 2) as rare_price,
                ? as regal_cost,
                ROUND(mp2.avg_price - mp1.avg_price - ?, 2) as magic_profit,
                ROUND(mp3.avg_price - mp1.avg_price - ?, 2) as rare_profit,
                ROUND(
                    CASE
                        WHEN mp1.avg_price > 0
                        THEN (mp2.avg_price - mp1.avg_price - ?) / mp1.avg_price * 100
                        ELSE NULL
                    END,
                    1
                ) as magic_profit_pct,
                ROUND(
                    CASE
                        WHEN mp1.avg_price > 0
                        THEN (mp3.avg_price - mp1.avg_price - ?) / mp1.avg_price * 100
                        ELSE NULL
                    END,
                    1
                ) as rare_profit_pct,
                mp1.count as normal_count,
                mp2.count as magic_count,
                mp3.count as rare_count
            FROM mode_prices mp1
            LEFT JOIN mode_prices mp2 ON mp2.tablet_type = mp1.tablet_type AND mp2.query_mode = 'magic'
            LEFT JOIN mode_prices mp3 ON mp3.tablet_type = mp1.tablet_type AND mp3.query_mode = 'rare'
            WHERE mp1.query_mode = 'normal'
            ORDER BY rare_profit DESC NULLS LAST
            """,
            (
                league_id,
                MAX_DIV,
                floor,
                regal_cost,
                regal_cost,
                regal_cost,
                regal_cost,
                regal_cost,
            ),
        ).fetchall()
    )


def time_based_patterns(league_id: int) -> list[dict]:
    """
    Analyze price patterns by hour of day and day of week.
    """
    floor = analysis_floor_snapshot_id(league_id)
    conn = get_connection()
    return _rows_to_dicts(
        conn.execute(
            """
            SELECT
                l.tablet_type,
                l.query_mode,
                strftime('%H', s.taken_at) as hour_of_day,
                strftime('%w', s.taken_at) as day_of_week,
                COUNT(*) as count,
                ROUND(AVG(l.price_divine), 2) as avg_price,
                ROUND(MIN(l.price_divine), 2) as min_price,
                ROUND(MAX(l.price_divine), 2) as max_price
            FROM listings l
            JOIN snapshots s ON l.snapshot_id = s.id
            WHERE l.league_id = ?
              AND l.price_divine IS NOT NULL
              AND l.price_divine <= ?
              AND l.snapshot_id >= ?
            GROUP BY l.tablet_type, l.query_mode, hour_of_day, day_of_week
            ORDER BY l.tablet_type, l.query_mode, hour_of_day
            """,
            (league_id, MAX_DIV, floor),
        ).fetchall()
    )


def mod_reference_separated() -> list[dict]:
    """
    Get all tablet modifiers with prefixes and suffixes separated.
    Static data from wiki - does not require league_id.
    """
    from poe_tablet_tool.modifiers_data import get_modifiers_separated

    return get_modifiers_separated()


def mod_reference_detail(tablet_type: str) -> dict:
    """
    Get detailed modifiers (prefixes and suffixes) for a specific tablet type.
    """
    from poe_tablet_tool.modifiers_data import get_modifiers_by_tablet

    return get_modifiers_by_tablet(tablet_type) or {"error": "Tablet type not found"}
