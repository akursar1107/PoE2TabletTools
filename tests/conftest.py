"""
Shared pytest fixtures for poe_tablet_tool tests.

Provides an in-memory SQLite connection (via the migration system) pre-seeded
with a minimal but realistic dataset: one league, two snapshots, and a handful
of listings + affixes covering all three query modes.
"""

import sqlite3

import pytest

from poe_tablet_tool.db.migrations import apply_migrations


# ---------------------------------------------------------------------------
# Low-level in-memory connection
# ---------------------------------------------------------------------------


@pytest.fixture()
def mem_conn() -> sqlite3.Connection:
    """Bare in-memory connection with schema applied (no thread-local caching)."""
    conn = sqlite3.connect(
        ":memory:",
        detect_types=sqlite3.PARSE_DECLTYPES,
        check_same_thread=False,
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    apply_migrations(conn)
    return conn


# ---------------------------------------------------------------------------
# Seeded dataset
# ---------------------------------------------------------------------------

_LEAGUE_ID = 1
_SNAP1_ID = 1
_SNAP2_ID = 2

_NOW = "2025-01-01T12:00:00+00:00"
_LATER = "2025-01-01T13:00:00+00:00"


def _seed(conn: sqlite3.Connection) -> None:
    """Insert a minimal but complete dataset into the in-memory DB."""
    conn.execute(
        "INSERT INTO leagues (id, name, started_at, is_active) VALUES (?, ?, ?, 1)",
        (_LEAGUE_ID, "TestLeague", _NOW),
    )

    # Two snapshots: snap1 (older), snap2 (newer)
    for snap_id, taken_at in ((_SNAP1_ID, _NOW), (_SNAP2_ID, _LATER)):
        conn.execute(
            """
            INSERT INTO snapshots (id, league_id, tablet_type, query_mode, taken_at,
                                   listing_count, query_hash, total_count, fetched_count)
            VALUES (?, ?, 'ritual', 'rare', ?, 2, 'hash1', 10, 2)
            """,
            (snap_id, _LEAGUE_ID, taken_at),
        )

    # Extra snapshots for normal and magic modes
    conn.execute(
        """
        INSERT INTO snapshots (id, league_id, tablet_type, query_mode, taken_at,
                               listing_count, query_hash, total_count, fetched_count)
        VALUES (3, ?, 'ritual', 'normal', ?, 2, 'hash2', 5, 2)
        """,
        (_LEAGUE_ID, _NOW),
    )
    conn.execute(
        """
        INSERT INTO snapshots (id, league_id, tablet_type, query_mode, taken_at,
                               listing_count, query_hash, total_count, fetched_count)
        VALUES (4, ?, 'ritual', 'magic', ?, 2, 'hash3', 5, 2)
        """,
        (_LEAGUE_ID, _NOW),
    )

    # Rare listings (snap1) — 3 listings with varying prices
    rare_listings = [
        (1, _SNAP1_ID, _LEAGUE_ID, "item_r1", "ritual", "rare", 4, 8, 500.0, "divine", 2.5, "SellerA"),
        (2, _SNAP1_ID, _LEAGUE_ID, "item_r2", "ritual", "rare", 5, 8, 1000.0, "divine", 5.0, "SellerB"),
        (3, _SNAP1_ID, _LEAGUE_ID, "item_r3", "ritual", "rare", 3, 8, 300.0, "divine", 1.5, "SellerC"),
    ]
    # Rare listings (snap2) — item_r1 disappeared, item_r4 is new
    rare_listings += [
        (4, _SNAP2_ID, _LEAGUE_ID, "item_r2", "ritual", "rare", 5, 8, 1000.0, "divine", 5.0, "SellerB"),
        (5, _SNAP2_ID, _LEAGUE_ID, "item_r3", "ritual", "rare", 3, 8, 290.0, "divine", 1.45, "SellerC"),
        (6, _SNAP2_ID, _LEAGUE_ID, "item_r4", "ritual", "rare", 4, 8, 400.0, "divine", 2.0, "SellerD"),
    ]
    # Normal listings (snap 3)
    rare_listings += [
        (7, 3, _LEAGUE_ID, "item_n1", "ritual", "normal", 0, 8, 50.0, "divine", 0.25, "SellerA"),
        (8, 3, _LEAGUE_ID, "item_n2", "ritual", "normal", 0, 8, 60.0, "divine", 0.30, "SellerB"),
    ]
    # Magic listings (snap 4)
    rare_listings += [
        (9, 4, _LEAGUE_ID, "item_m1", "ritual", "magic", 2, 8, 200.0, "divine", 1.0, "SellerA"),
        (10, 4, _LEAGUE_ID, "item_m2", "ritual", "magic", 2, 8, 250.0, "divine", 1.25, "SellerB"),
    ]

    conn.executemany(
        """
        INSERT INTO listings (id, snapshot_id, league_id, item_id, tablet_type, query_mode,
                              affix_count, uses_remaining, price_amount, price_currency,
                              price_divine, seller_name, first_seen_at, last_seen_at,
                              disappeared_at, status, raw_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, 'active', '{}')
        """,
        [r + (_NOW, _NOW) for r in rare_listings],
    )

    # Mark item_r1 as likely_sold in snap1 after snap2 appeared
    conn.execute(
        "UPDATE listings SET status = 'likely_sold', disappeared_at = ? WHERE item_id = ?",
        (_LATER, "item_r1"),
    )

    # Affixes — mod_a on r1/r2/r4, mod_b on r2/r3
    affixes = [
        # listing_id, item_id, slot, mod_id, mod_text, mod_family
        (1, 1, "item_r1", "prefix", "mod_a", "10% Monster Pack Size", "# Monster Pack Size"),
        (2, 1, "item_r1", "suffix", "mod_b", "15% Ritual Monsters", "# Ritual Monsters"),
        (3, 2, "item_r2", "prefix", "mod_a", "12% Monster Pack Size", "# Monster Pack Size"),
        (4, 2, "item_r2", "suffix", "mod_b", "18% Ritual Monsters", "# Ritual Monsters"),
        (5, 3, "item_r3", "suffix", "mod_b", "10% Ritual Monsters", "# Ritual Monsters"),
        (6, 4, "item_r2", "prefix", "mod_a", "12% Monster Pack Size", "# Monster Pack Size"),
        (7, 4, "item_r2", "suffix", "mod_b", "18% Ritual Monsters", "# Ritual Monsters"),
        (8, 6, "item_r4", "prefix", "mod_a", "11% Monster Pack Size", "# Monster Pack Size"),
        (9, 9, "item_m1", "prefix", "mod_a", "10% Monster Pack Size", "# Monster Pack Size"),
        (10, 9, "item_m1", "suffix", "mod_b", "15% Ritual Monsters", "# Ritual Monsters"),
        (11, 10, "item_m2", "prefix", "mod_a", "12% Monster Pack Size", "# Monster Pack Size"),
        (12, 10, "item_m2", "suffix", "mod_b", "18% Ritual Monsters", "# Ritual Monsters"),
    ]
    conn.executemany(
        """
        INSERT INTO affixes (id, listing_id, item_id, slot, mod_id, mod_text, mod_family,
                             value_min, value_max, mod_index)
        VALUES (?, ?, ?, ?, ?, ?, ?, NULL, NULL, 0)
        """,
        affixes,
    )

    conn.commit()


@pytest.fixture()
def seeded_conn(mem_conn: sqlite3.Connection) -> sqlite3.Connection:
    """In-memory connection with a realistic seeded dataset."""
    _seed(mem_conn)
    return mem_conn


# Expose constants for use in tests
LEAGUE_ID = _LEAGUE_ID
SNAP1_ID = _SNAP1_ID
SNAP2_ID = _SNAP2_ID
