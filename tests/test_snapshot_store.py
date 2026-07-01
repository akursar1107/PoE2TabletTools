"""Tests for snapshot_store: upsert behavior, affix dedup, and IN-clause chunking."""

import sqlite3
from dataclasses import dataclass, field
from unittest.mock import patch

import pytest

from poe_tablet_tool.parser import ParsedAffix, ParsedListing
from tests.conftest import LEAGUE_ID, SNAP1_ID


def _patch_conn(conn: sqlite3.Connection):
    return patch(
        "poe_tablet_tool.snapshot_store.get_connection", return_value=conn
    )


def _make_listing(
    item_id: str = "test_item",
    price_divine: float = 1.0,
    affixes: list | None = None,
    rarity: str = "Rare",
    affix_count: int = 4,
) -> ParsedListing:
    return ParsedListing(
        item_id=item_id,
        seller_name="TestSeller",
        price_amount=200.0,
        price_currency="chaos",
        price_divine=price_divine,
        affix_count=affix_count,
        uses_remaining=8,
        rarity=rarity,
        affixes=affixes or [],
        raw_json="{}",
    )


# ---------------------------------------------------------------------------
# create_snapshot
# ---------------------------------------------------------------------------


def test_create_snapshot_returns_id(mem_conn):
    from poe_tablet_tool.snapshot_store import create_snapshot

    # Insert a league first
    mem_conn.execute(
        "INSERT INTO leagues (id, name, started_at, is_active) VALUES (1, 'L', '2025-01-01', 1)"
    )
    mem_conn.commit()

    with _patch_conn(mem_conn):
        sid = create_snapshot(
            league_id=1,
            tablet_type="ritual",
            query_mode="rare",
            query_hash="abc123",
            listing_count=5,
        )

    assert isinstance(sid, int)
    assert sid > 0


def test_create_snapshot_dedup(mem_conn):
    """Same hash twice → same snapshot id returned."""
    from poe_tablet_tool.snapshot_store import create_snapshot

    mem_conn.execute(
        "INSERT INTO leagues (id, name, started_at, is_active) VALUES (1, 'L', '2025-01-01', 1)"
    )
    mem_conn.commit()

    with _patch_conn(mem_conn):
        sid1 = create_snapshot(1, "ritual", "rare", "samehash", 5)
        sid2 = create_snapshot(1, "ritual", "rare", "samehash", 5)

    assert sid1 == sid2


# ---------------------------------------------------------------------------
# store_listings — basic upsert
# ---------------------------------------------------------------------------


def test_store_listings_inserts_rows(mem_conn):
    from poe_tablet_tool.snapshot_store import create_snapshot, store_listings

    mem_conn.execute(
        "INSERT INTO leagues (id, name, started_at, is_active) VALUES (1, 'L', '2025-01-01', 1)"
    )
    mem_conn.commit()

    with _patch_conn(mem_conn):
        sid = create_snapshot(1, "ritual", "rare", "h1", 2)
        listings = [_make_listing("item_a", 1.0), _make_listing("item_b", 2.0)]
        store_listings(sid, 1, "ritual", "rare", listings)

    count = mem_conn.execute("SELECT COUNT(*) FROM listings").fetchone()[0]
    assert count == 2


def test_store_listings_stores_affixes(mem_conn):
    from poe_tablet_tool.snapshot_store import create_snapshot, store_listings

    mem_conn.execute(
        "INSERT INTO leagues (id, name, started_at, is_active) VALUES (1, 'L', '2025-01-01', 1)"
    )
    mem_conn.commit()

    affix = ParsedAffix(
        mod_id="mod_x",
        mod_text="10% Pack Size",
        mod_family="# Pack Size",
        slot="prefix",
    )

    with _patch_conn(mem_conn):
        sid = create_snapshot(1, "ritual", "rare", "h1", 1)
        store_listings(sid, 1, "ritual", "rare", [_make_listing("item_a", affixes=[affix])])

    count = mem_conn.execute("SELECT COUNT(*) FROM affixes").fetchone()[0]
    assert count == 1


def test_store_listings_no_duplicate_affixes(mem_conn):
    """Storing the same listing twice must not duplicate affixes."""
    from poe_tablet_tool.snapshot_store import create_snapshot, store_listings

    mem_conn.execute(
        "INSERT INTO leagues (id, name, started_at, is_active) VALUES (1, 'L', '2025-01-01', 1)"
    )
    mem_conn.commit()

    affix = ParsedAffix(mod_id="mod_x", mod_text="10% Pack Size", mod_family="# Pack Size", slot="prefix")
    listing = _make_listing("item_a", affixes=[affix])

    with _patch_conn(mem_conn):
        sid = create_snapshot(1, "ritual", "rare", "h1", 1)
        store_listings(sid, 1, "ritual", "rare", [listing])
        store_listings(sid, 1, "ritual", "rare", [listing])  # second call

    count = mem_conn.execute("SELECT COUNT(*) FROM affixes").fetchone()[0]
    assert count == 1


def test_store_listings_preserves_first_seen_at(mem_conn):
    """first_seen_at should not change on a second snapshot for the same item."""
    from poe_tablet_tool.snapshot_store import create_snapshot, store_listings

    mem_conn.execute(
        "INSERT INTO leagues (id, name, started_at, is_active) VALUES (1, 'L', '2025-01-01', 1)"
    )
    mem_conn.commit()

    with _patch_conn(mem_conn):
        sid1 = create_snapshot(1, "ritual", "rare", "h1", 1)
        store_listings(sid1, 1, "ritual", "rare", [_make_listing("item_a")])
        first_seen_1 = mem_conn.execute(
            "SELECT first_seen_at FROM listings WHERE item_id='item_a'"
        ).fetchone()[0]

        sid2 = create_snapshot(1, "ritual", "rare", "h2", 1)
        store_listings(sid2, 1, "ritual", "rare", [_make_listing("item_a")])
        first_seen_2 = mem_conn.execute(
            "SELECT first_seen_at FROM listings WHERE item_id='item_a' ORDER BY id LIMIT 1"
        ).fetchone()[0]

    assert first_seen_1 == first_seen_2


# ---------------------------------------------------------------------------
# _chunked_in_query
# ---------------------------------------------------------------------------


def test_chunked_in_query_small(mem_conn):
    """Chunk size larger than list — single query path."""
    from poe_tablet_tool.snapshot_store import _chunked_in_query

    mem_conn.execute(
        "INSERT INTO leagues (id, name, started_at, is_active) VALUES (1, 'L', '2025-01-01', 1)"
    )
    mem_conn.commit()

    # Insert 3 items to query back
    mem_conn.executemany(
        "INSERT INTO snapshots (id, league_id, tablet_type, query_mode, taken_at, "
        "listing_count, query_hash) VALUES (?, 1, 'ritual', 'rare', '2025-01-01', 0, ?)",
        [(i, f"h{i}") for i in range(1, 4)],
    )
    mem_conn.commit()

    rows = _chunked_in_query(
        mem_conn,
        "SELECT id FROM snapshots WHERE id IN ({})",
        [1, 2, 3],
    )
    assert len(rows) == 3


def test_chunked_in_query_chunked(mem_conn):
    """Chunk size smaller than list — multiple queries."""
    from poe_tablet_tool.snapshot_store import _chunked_in_query

    mem_conn.execute(
        "INSERT INTO leagues (id, name, started_at, is_active) VALUES (1, 'L', '2025-01-01', 1)"
    )
    mem_conn.commit()

    # Insert 5 snapshots
    mem_conn.executemany(
        "INSERT INTO snapshots (id, league_id, tablet_type, query_mode, taken_at, "
        "listing_count, query_hash) VALUES (?, 1, 'ritual', 'rare', '2025-01-01', 0, ?)",
        [(i, f"h{i}") for i in range(1, 6)],
    )
    mem_conn.commit()

    rows = _chunked_in_query(
        mem_conn,
        "SELECT id FROM snapshots WHERE id IN ({})",
        list(range(1, 6)),
        chunk_size=2,  # Force chunking: 3 queries for 5 items
    )
    assert len(rows) == 5


def test_chunked_in_query_empty(mem_conn):
    """Empty list returns empty results without error."""
    from poe_tablet_tool.snapshot_store import _chunked_in_query

    rows = _chunked_in_query(
        mem_conn,
        "SELECT id FROM snapshots WHERE id IN ({})",
        [],
    )
    assert rows == []
