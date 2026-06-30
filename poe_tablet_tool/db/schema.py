"""
Database schema creation and migration.
Run init_db() once at startup to ensure all tables exist.
"""

from poe_tablet_tool.db.connection import get_connection

SCHEMA_SQL = """
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
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    league_id                   INTEGER NOT NULL REFERENCES leagues(id),
    tablet_type                 TEXT    NOT NULL,
    mod_a_id                    TEXT    NOT NULL,
    mod_b_id                    TEXT    NOT NULL,
    mod_a_text                  TEXT    NOT NULL,
    mod_b_text                  TEXT    NOT NULL,
    mod_pair_key                TEXT    NOT NULL,
    magic_sold_count            INTEGER NOT NULL DEFAULT 0,
    magic_median_price_div      REAL,
    magic_avg_time_to_disappear_hours REAL,
    updated_at                  TEXT    NOT NULL,
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


def _column_exists(conn, table: str, column: str) -> bool:
    cols = {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
    return column in cols


def init_db() -> None:
    conn = get_connection()
    conn.executescript(SCHEMA_SQL)

    if not _column_exists(conn, "affixes", "mod_family"):
        conn.execute(
            "ALTER TABLE affixes ADD COLUMN mod_family TEXT NOT NULL DEFAULT ''"
        )

    for column, ddl in (
        (
            "total_count",
            "ALTER TABLE snapshots ADD COLUMN total_count INTEGER NOT NULL DEFAULT 0",
        ),
        (
            "fetched_count",
            "ALTER TABLE snapshots ADD COLUMN fetched_count INTEGER NOT NULL DEFAULT 0",
        ),
    ):
        if not _column_exists(conn, "snapshots", column):
            conn.execute(ddl)

    conn.commit()
