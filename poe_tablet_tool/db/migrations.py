"""
Versioned database migration system.

Each migration is a plain function that receives an open connection and applies
exactly one schema change. Migrations are numbered sequentially and run in order.
Once applied, a migration is never re-run.

Usage (called automatically by init_db):
    from poe_tablet_tool.db.migrations import apply_migrations
    apply_migrations(conn)
"""

import logging
import sqlite3

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Baseline schema (v0 → v1): all original tables and indexes
# ---------------------------------------------------------------------------
_BASELINE_SQL = """
CREATE TABLE IF NOT EXISTS leagues (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,
    started_at  TEXT    NOT NULL,
    ended_at    TEXT,
    is_active   INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS snapshots (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    league_id       INTEGER NOT NULL REFERENCES leagues(id),
    tablet_type     TEXT    NOT NULL,
    query_mode      TEXT    NOT NULL CHECK (query_mode IN ('rare', 'magic', 'normal')),
    taken_at        TEXT    NOT NULL,
    listing_count   INTEGER NOT NULL DEFAULT 0,
    query_hash      TEXT    NOT NULL,
    total_count     INTEGER NOT NULL DEFAULT 0,
    fetched_count   INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS listings (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id      INTEGER NOT NULL REFERENCES snapshots(id),
    league_id        INTEGER NOT NULL REFERENCES leagues(id),
    item_id          TEXT    NOT NULL,
    tablet_type      TEXT    NOT NULL,
    query_mode       TEXT    NOT NULL,
    affix_count      INTEGER,
    uses_remaining   INTEGER,
    price_amount     REAL,
    price_currency   TEXT,
    price_divine     REAL,
    seller_name      TEXT,
    first_seen_at    TEXT    NOT NULL,
    last_seen_at     TEXT    NOT NULL,
    disappeared_at   TEXT,
    status           TEXT    NOT NULL DEFAULT 'active',
    raw_json         TEXT    NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_listings_item_snapshot
    ON listings (item_id, snapshot_id);

CREATE INDEX IF NOT EXISTS idx_listings_item_id      ON listings (item_id);
CREATE INDEX IF NOT EXISTS idx_listings_tablet_mode  ON listings (tablet_type, query_mode);
CREATE INDEX IF NOT EXISTS idx_listings_status       ON listings (status);
CREATE INDEX IF NOT EXISTS idx_listings_league_mode  ON listings (league_id, query_mode);

CREATE TABLE IF NOT EXISTS affixes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    listing_id  INTEGER NOT NULL REFERENCES listings(id),
    item_id     TEXT    NOT NULL,
    slot        TEXT    NOT NULL DEFAULT 'unknown',
    mod_id      TEXT    NOT NULL,
    mod_text    TEXT    NOT NULL,
    mod_family  TEXT    NOT NULL DEFAULT '',
    value_min   REAL,
    value_max   REAL,
    mod_index   INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_affixes_listing_id ON affixes (listing_id);
CREATE INDEX IF NOT EXISTS idx_affixes_mod_id     ON affixes (mod_id);
CREATE INDEX IF NOT EXISTS idx_affixes_item_id    ON affixes (item_id);

CREATE TABLE IF NOT EXISTS exchange_rates (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    league_id      INTEGER NOT NULL REFERENCES leagues(id),
    taken_at       TEXT    NOT NULL,
    base_currency  TEXT    NOT NULL,
    quote_currency TEXT    NOT NULL,
    rate           REAL    NOT NULL
);

CREATE TABLE IF NOT EXISTS listing_disappearances (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id         TEXT    NOT NULL,
    tablet_type     TEXT    NOT NULL,
    query_mode      TEXT    NOT NULL,
    old_snapshot_id INTEGER NOT NULL REFERENCES snapshots(id),
    new_snapshot_id INTEGER NOT NULL REFERENCES snapshots(id),
    classified_as   TEXT    NOT NULL,
    confidence      REAL    NOT NULL DEFAULT 0.0,
    reason          TEXT    NOT NULL DEFAULT '',
    created_at      TEXT    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_disappearances_item_id ON listing_disappearances (item_id);
CREATE INDEX IF NOT EXISTS idx_disappearances_class   ON listing_disappearances (classified_as);

CREATE TABLE IF NOT EXISTS job_health (
    job_key              TEXT PRIMARY KEY,
    last_success_at      TEXT,
    last_error_at        TEXT,
    last_error           TEXT,
    last_listing_count   INTEGER,
    last_total_count     INTEGER,
    last_fetched_count   INTEGER
);

CREATE TABLE IF NOT EXISTS rare_affix_stats (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    league_id                   INTEGER NOT NULL REFERENCES leagues(id),
    tablet_type                 TEXT    NOT NULL,
    mod_id                      TEXT    NOT NULL,
    slot                        TEXT    NOT NULL,
    mod_text                    TEXT    NOT NULL,
    mod_family                  TEXT    NOT NULL DEFAULT '',
    sold_count                  INTEGER NOT NULL DEFAULT 0,
    active_count                INTEGER NOT NULL DEFAULT 0,
    sold_frequency              REAL    NOT NULL DEFAULT 0,
    active_frequency            REAL    NOT NULL DEFAULT 0,
    lift                        REAL    NOT NULL DEFAULT 0,
    median_sold_price_div       REAL,
    avg_time_to_disappear_hours REAL,
    updated_at                  TEXT    NOT NULL,
    UNIQUE (league_id, tablet_type, mod_id, slot)
);

CREATE TABLE IF NOT EXISTS magic_seed_pairs (
    id                                INTEGER PRIMARY KEY AUTOINCREMENT,
    league_id                         INTEGER NOT NULL REFERENCES leagues(id),
    tablet_type                       TEXT    NOT NULL,
    mod_a_id                          TEXT    NOT NULL,
    mod_b_id                          TEXT    NOT NULL,
    mod_a_text                        TEXT    NOT NULL,
    mod_b_text                        TEXT    NOT NULL,
    mod_pair_key                      TEXT    NOT NULL,
    magic_sold_count                  INTEGER NOT NULL DEFAULT 0,
    magic_median_price_div            REAL,
    magic_avg_time_to_disappear_hours REAL,
    updated_at                        TEXT    NOT NULL,
    UNIQUE (league_id, tablet_type, mod_pair_key)
);

CREATE TABLE IF NOT EXISTS crafting_edge (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    league_id               INTEGER NOT NULL REFERENCES leagues(id),
    tablet_type             TEXT    NOT NULL,
    mod_a_id                TEXT    NOT NULL,
    mod_b_id                TEXT    NOT NULL,
    mod_pair_key            TEXT    NOT NULL,
    magic_buy_price_div     REAL,
    magic_median_price_div  REAL,
    rare_median_price_div   REAL,
    regal_cost_div          REAL    NOT NULL DEFAULT 0,
    expected_profit_div     REAL,
    junk_rate               REAL    NOT NULL DEFAULT 0,
    confidence              REAL    NOT NULL DEFAULT 0,
    is_buy_signal           INTEGER NOT NULL DEFAULT 0,
    updated_at              TEXT    NOT NULL,
    UNIQUE (league_id, tablet_type, mod_pair_key)
);

CREATE TABLE IF NOT EXISTS regex_outputs (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    league_id      INTEGER NOT NULL REFERENCES leagues(id),
    tablet_type    TEXT,
    regex_mode     TEXT    NOT NULL,
    label          TEXT    NOT NULL,
    regex_text     TEXT    NOT NULL,
    char_count     INTEGER NOT NULL DEFAULT 0,
    source_summary TEXT    NOT NULL DEFAULT '',
    updated_at     TEXT    NOT NULL
);
"""


# ---------------------------------------------------------------------------
# Migration functions — one per version step
# ---------------------------------------------------------------------------


def _migration_v1(conn: sqlite3.Connection) -> None:
    """Apply baseline schema (all original tables)."""
    conn.executescript(_BASELINE_SQL)


def _migration_v2(conn: sqlite3.Connection) -> None:
    """Add mod_family column to affixes if missing (backfill for old DBs)."""
    cols = {r[1] for r in conn.execute("PRAGMA table_info(affixes)")}
    if "mod_family" not in cols:
        conn.execute(
            "ALTER TABLE affixes ADD COLUMN mod_family TEXT NOT NULL DEFAULT ''"
        )


def _migration_v3(conn: sqlite3.Connection) -> None:
    """Add total_count and fetched_count to snapshots (backfill for old DBs)."""
    cols = {r[1] for r in conn.execute("PRAGMA table_info(snapshots)")}
    if "total_count" not in cols:
        conn.execute(
            "ALTER TABLE snapshots ADD COLUMN total_count INTEGER NOT NULL DEFAULT 0"
        )
    if "fetched_count" not in cols:
        conn.execute(
            "ALTER TABLE snapshots ADD COLUMN fetched_count INTEGER NOT NULL DEFAULT 0"
        )


# Ordered list of all migrations; append new ones here.
_MIGRATIONS: list[tuple[int, str, callable]] = [
    (1, "baseline schema", _migration_v1),
    (2, "affixes.mod_family column", _migration_v2),
    (3, "snapshots total/fetched_count columns", _migration_v3),
]


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def _ensure_version_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_version (
            version     INTEGER PRIMARY KEY,
            description TEXT    NOT NULL,
            applied_at  TEXT    NOT NULL
        )
        """
    )
    conn.commit()


def _current_version(conn: sqlite3.Connection) -> int:
    row = conn.execute(
        "SELECT MAX(version) AS v FROM schema_version"
    ).fetchone()
    return int(row["v"]) if row and row["v"] is not None else 0


def apply_migrations(conn: sqlite3.Connection) -> None:
    """Apply all pending migrations in order. Safe to call on every startup."""
    _ensure_version_table(conn)
    current = _current_version(conn)

    from datetime import datetime, timezone

    for version, description, fn in _MIGRATIONS:
        if version <= current:
            continue
        logger.info("Applying migration v%d: %s", version, description)
        fn(conn)
        conn.execute(
            "INSERT INTO schema_version (version, description, applied_at) VALUES (?, ?, ?)",
            (version, description, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
        logger.info("Migration v%d applied successfully.", version)
