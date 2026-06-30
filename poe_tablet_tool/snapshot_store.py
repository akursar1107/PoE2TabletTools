"""
Writes snapshots, listings, and affixes to the database.
Handles upserts for recurring item IDs (update last_seen_at, status).
"""

import logging
from datetime import datetime, timezone

from poe_tablet_tool.db.connection import get_connection
from poe_tablet_tool.parser import ParsedListing

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_snapshot(
    league_id: int,
    tablet_type: str,
    query_mode: str,
    query_hash: str,
    listing_count: int,
    total_count: int = 0,
    fetched_count: int = 0,
) -> int:
    conn = get_connection()

    # Check for duplicate snapshot (same league, tablet, mode, hash)
    existing = conn.execute(
        """
        SELECT id FROM snapshots
        WHERE league_id = ? AND tablet_type = ? AND query_mode = ? AND query_hash = ?
        ORDER BY id DESC LIMIT 1
        """,
        (league_id, tablet_type, query_mode, query_hash),
    ).fetchone()

    if existing:
        logger.debug(
            "Duplicate snapshot detected (league=%d, type=%s, mode=%s, hash=%s), "
            "returning existing id=%d",
            league_id,
            tablet_type,
            query_mode,
            query_hash[:8],
            existing["id"],
        )
        return existing["id"]

    cursor = conn.execute(
        """
        INSERT INTO snapshots (
            league_id, tablet_type, query_mode, taken_at, listing_count,
            query_hash, total_count, fetched_count
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            league_id,
            tablet_type,
            query_mode,
            _now(),
            listing_count,
            query_hash,
            total_count,
            fetched_count,
        ),
    )
    conn.commit()
    return cursor.lastrowid


def store_listings(
    snapshot_id: int,
    league_id: int,
    tablet_type: str,
    query_mode: str,
    listings: list[ParsedListing],
) -> None:
    if not listings:
        return

    conn = get_connection()
    now = _now()

    # Step 1: Bulk fetch existing first_seen_at for all item_ids
    item_ids = [l.item_id for l in listings]
    existing_rows = conn.execute(
        """
        SELECT item_id, first_seen_at FROM listings
        WHERE item_id IN ({})
          AND league_id = ?
        ORDER BY item_id, id DESC
        """.format(",".join("?" * len(item_ids))),
        item_ids + [league_id],
    ).fetchall()
    # Map item_id to first_seen_at (keep first occurrence per item)
    existing_map = {}
    for row in existing_rows:
        if row["item_id"] not in existing_map:
            existing_map[row["item_id"]] = row["first_seen_at"]

    # Step 2: Bulk insert all listings
    listing_data = [
        (
            snapshot_id,
            league_id,
            l.item_id,
            tablet_type,
            query_mode,
            l.affix_count,
            l.uses_remaining,
            l.price_amount,
            l.price_currency,
            l.price_divine,
            l.seller_name,
            existing_map.get(l.item_id, now),
            now,
            l.raw_json,
        )
        for l in listings
    ]

    conn.executemany(
        """
        INSERT INTO listings (
            snapshot_id, league_id, item_id, tablet_type, query_mode,
            affix_count, uses_remaining, price_amount, price_currency,
            price_divine, seller_name, first_seen_at, last_seen_at,
            disappeared_at, status, raw_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, 'active', ?)
        ON CONFLICT (item_id, snapshot_id) DO UPDATE SET
            last_seen_at = excluded.last_seen_at,
            price_amount = excluded.price_amount,
            price_currency = excluded.price_currency,
            price_divine = excluded.price_divine,
            status = 'active'
        """,
        listing_data,
    )

    # Step 3: Bulk fetch all new listing IDs
    new_listing_ids = conn.execute(
        """
        SELECT id, item_id FROM listings
        WHERE snapshot_id = ?
          AND item_id IN ({})
        """.format(",".join("?" * len(item_ids))),
        [snapshot_id] + item_ids,
    ).fetchall()
    # Map item_id to listing db id
    listing_id_map = {row["item_id"]: row["id"] for row in new_listing_ids}

    # Step 4: Find which listings need affixes (no existing affixes)
    listing_ids = [row["id"] for row in new_listing_ids]
    if listing_ids:
        affix_check = conn.execute(
            """
            SELECT listing_id FROM affixes
            WHERE listing_id IN ({})
            GROUP BY listing_id
            """.format(",".join("?" * len(listing_ids))),
            listing_ids,
        ).fetchall()
        needs_affixes = {row["listing_id"] for row in affix_check}

        # Step 5: Bulk insert affixes for listings that need them
        for listing in listings:
            db_id = listing_id_map.get(listing.item_id)
            if db_id and db_id not in needs_affixes:
                _store_affixes(conn, db_id, listing)

    conn.commit()
    logger.info(
        "Stored %d listings for %s/%s snapshot %d",
        len(listings),
        tablet_type,
        query_mode,
        snapshot_id,
    )


def _store_affixes(conn, listing_id: int, listing: ParsedListing) -> None:
    for affix in listing.affixes:
        conn.execute(
            """
            INSERT INTO affixes (
                listing_id, item_id, slot, mod_id, mod_text, mod_family,
                value_min, value_max, mod_index
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                listing_id,
                listing.item_id,
                affix.slot,
                affix.mod_id,
                affix.mod_text,
                affix.mod_family,
                affix.value_min,
                affix.value_max,
                affix.mod_index,
            ),
        )


def get_previous_snapshot_id(
    league_id: int, tablet_type: str, query_mode: str, before_snapshot_id: int
) -> int | None:
    conn = get_connection()
    row = conn.execute(
        """
        SELECT id FROM snapshots
        WHERE league_id = ? AND tablet_type = ? AND query_mode = ? AND id < ?
        ORDER BY id DESC LIMIT 1
        """,
        (league_id, tablet_type, query_mode, before_snapshot_id),
    ).fetchone()
    return row["id"] if row else None


def get_item_ids_in_snapshot(snapshot_id: int) -> set[str]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT item_id FROM listings WHERE snapshot_id = ?", (snapshot_id,)
    ).fetchall()
    return {r["item_id"] for r in rows}


def mark_disappeared(
    item_id: str,
    snapshot_id: int,
    disappeared_at: str,
    status: str = "uncertain",
) -> None:
    conn = get_connection()
    conn.execute(
        """
        UPDATE listings SET disappeared_at = ?, status = ?
        WHERE item_id = ? AND snapshot_id = ? AND disappeared_at IS NULL
        """,
        (disappeared_at, status, item_id, snapshot_id),
    )
    conn.commit()


def analysis_floor_snapshot_id(league_id: int) -> int:
    """First snapshot id to include in reports (skip initial bootstrap noise)."""
    conn = get_connection()
    row = conn.execute(
        "SELECT MIN(id) AS min_id, MAX(id) AS max_id FROM snapshots WHERE league_id = ?",
        (league_id,),
    ).fetchone()
    if not row or row["min_id"] is None:
        return 1
    span = int(row["max_id"]) - int(row["min_id"])
    # Skip first 5 snapshots or 1% of data (whichever is smaller, min 1)
    return int(row["min_id"]) + max(0, min(5, span // 100 or 1))
