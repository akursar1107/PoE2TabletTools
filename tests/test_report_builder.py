"""Tests for report_builder queries against an in-memory seeded DB."""

import sqlite3
from unittest.mock import patch

import pytest

from tests.conftest import LEAGUE_ID


def _patch_conn(seeded_conn: sqlite3.Connection):
    """Context manager: redirect get_connection() to the in-memory DB."""
    return patch(
        "poe_tablet_tool.report_builder.get_connection", return_value=seeded_conn
    )


def _patch_store(seeded_conn: sqlite3.Connection):
    return patch(
        "poe_tablet_tool.snapshot_store.get_connection", return_value=seeded_conn
    )


# ---------------------------------------------------------------------------
# affix_frequency
# ---------------------------------------------------------------------------


def test_affix_frequency_returns_list(seeded_conn):
    import poe_tablet_tool.report_builder as rb

    with _patch_conn(seeded_conn), _patch_store(seeded_conn):
        rows = rb.affix_frequency(LEAGUE_ID)

    assert isinstance(rows, list)
    # mod_b appears on r1, r2, r3 — should show up
    families = [r["mod_family"] for r in rows]
    assert any("Ritual Monsters" in f for f in families)


def test_affix_frequency_respects_limit(seeded_conn):
    import poe_tablet_tool.report_builder as rb

    with _patch_conn(seeded_conn), _patch_store(seeded_conn):
        rows = rb.affix_frequency(LEAGUE_ID, limit=1)

    assert len(rows) <= 1


# ---------------------------------------------------------------------------
# affix_price
# ---------------------------------------------------------------------------


def test_affix_price_returns_list(seeded_conn):
    import poe_tablet_tool.report_builder as rb

    with _patch_conn(seeded_conn), _patch_store(seeded_conn):
        rows = rb.affix_price(LEAGUE_ID)

    assert isinstance(rows, list)
    for row in rows:
        assert "mod_family" in row
        assert "avg_div" in row
        assert row["n"] >= 3  # HAVING clause


# ---------------------------------------------------------------------------
# affix_combos
# ---------------------------------------------------------------------------


def test_affix_combos_returns_pairs(seeded_conn):
    import poe_tablet_tool.report_builder as rb

    with _patch_conn(seeded_conn), _patch_store(seeded_conn):
        rows = rb.affix_combos(LEAGUE_ID)

    assert isinstance(rows, list)
    for row in rows:
        assert "mod_a" in row
        assert "mod_b" in row
        assert row["mod_a"] != row["mod_b"]


# ---------------------------------------------------------------------------
# price_over_time
# ---------------------------------------------------------------------------


def test_price_over_time(seeded_conn):
    import poe_tablet_tool.report_builder as rb

    with _patch_conn(seeded_conn), _patch_store(seeded_conn):
        rows = rb.price_over_time(LEAGUE_ID)

    assert isinstance(rows, list)
    for row in rows:
        assert row["avg_div"] is not None


# ---------------------------------------------------------------------------
# normal_prices
# ---------------------------------------------------------------------------


def test_normal_prices(seeded_conn):
    import poe_tablet_tool.report_builder as rb

    with _patch_conn(seeded_conn), _patch_store(seeded_conn):
        rows = rb.normal_prices(LEAGUE_ID)

    assert isinstance(rows, list)
    assert len(rows) >= 1
    row = rows[0]
    assert row["tablet_type"] == "ritual"
    assert row["min_div"] <= row["max_div"]


# ---------------------------------------------------------------------------
# price_distribution
# ---------------------------------------------------------------------------


def test_price_distribution_buckets(seeded_conn):
    import poe_tablet_tool.report_builder as rb

    with _patch_conn(seeded_conn), _patch_store(seeded_conn):
        rows = rb.price_distribution(LEAGUE_ID)

    assert isinstance(rows, list)
    # Verify bucket field is present and non-null
    for row in rows:
        assert "bucket" in row
        assert "n" in row
        assert row["n"] > 0


# ---------------------------------------------------------------------------
# price_spread_analysis — specifically tests the STDDEV fix
# ---------------------------------------------------------------------------


def test_price_spread_analysis_no_crash(seeded_conn):
    """Regression test: STDDEV() was not available in SQLite — must not crash."""
    import poe_tablet_tool.report_builder as rb

    with _patch_conn(seeded_conn), _patch_store(seeded_conn):
        rows = rb.price_spread_analysis(LEAGUE_ID)

    assert isinstance(rows, list)
    for row in rows:
        # stddev_div should be a number (or None for single-row groups), never an error
        assert "stddev_div" in row


# ---------------------------------------------------------------------------
# get_active_league_id
# ---------------------------------------------------------------------------


def test_get_active_league_id(seeded_conn):
    import poe_tablet_tool.report_builder as rb

    with _patch_conn(seeded_conn):
        lid = rb.get_active_league_id()

    assert lid == LEAGUE_ID


def test_get_active_league_id_none_on_empty(mem_conn):
    import poe_tablet_tool.report_builder as rb

    with patch("poe_tablet_tool.report_builder.get_connection", return_value=mem_conn):
        lid = rb.get_active_league_id()

    assert lid is None
