"""FastAPI smoke tests: all routes return non-500 responses with a seeded DB."""

import sqlite3
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from poe_tablet_tool.api import app
from tests.conftest import LEAGUE_ID


@pytest.fixture()
def client(seeded_conn: sqlite3.Connection) -> TestClient:
    """TestClient with all DB calls redirected to the seeded in-memory DB."""
    patches = [
        patch("poe_tablet_tool.report_builder.get_connection", return_value=seeded_conn),
        patch("poe_tablet_tool.snapshot_store.get_connection", return_value=seeded_conn),
        patch("poe_tablet_tool.health.get_connection", return_value=seeded_conn),
        patch("poe_tablet_tool.api.get_connection", return_value=seeded_conn, create=True),
    ]
    for p in patches:
        p.start()
    yield TestClient(app)
    for p in patches:
        p.stop()


# ---------------------------------------------------------------------------
# Health endpoints
# ---------------------------------------------------------------------------


def test_health_ok(client: TestClient):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data


def test_health_detailed(client: TestClient):
    with patch("poe_tablet_tool.health.check_poe_api_health", return_value={"status": "mocked"}):
        resp = client.get("/api/health/detailed")
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Report endpoints (all require a seeded active league)
# ---------------------------------------------------------------------------

_REPORT_ROUTES = [
    "/api/reports/affix-frequency",
    "/api/reports/affix-price",
    "/api/reports/affix-velocity",
    "/api/reports/price-over-time",
    "/api/reports/price-distribution",
    "/api/reports/affix-combos",
    "/api/reports/rare-affix-lift",
    "/api/reports/buy-signals",
    "/api/reports/regex",
    "/api/reports/normal-prices",
    "/api/reports/price-spread",
    "/api/reports/crafting-profitability",
    "/api/reports/time-patterns",
]


@pytest.mark.parametrize("route", _REPORT_ROUTES)
def test_report_routes_not_500(client: TestClient, route: str):
    resp = client.get(route)
    assert resp.status_code != 500, f"{route} returned 500: {resp.text}"


def test_report_summary_not_500(client: TestClient):
    resp = client.get("/api/reports/summary")
    assert resp.status_code != 500


# ---------------------------------------------------------------------------
# CSV export
# ---------------------------------------------------------------------------


def test_export_csv_content_type(client: TestClient):
    """Regression: CSV export must return text/csv, not a JSON string."""
    resp = client.get("/api/export/prices-csv")
    assert resp.status_code != 500
    if resp.status_code == 200:
        assert "text/csv" in resp.headers["content-type"]
        # Should look like CSV, not a JSON-quoted string
        assert not resp.text.startswith('"')


# ---------------------------------------------------------------------------
# League info
# ---------------------------------------------------------------------------


def test_league_info(client: TestClient):
    with (
        patch("poe_tablet_tool.league_detector.detect_league", return_value="TestLeague"),
        patch("poe_tablet_tool.league_reset.get_all_leagues", return_value=[]),
    ):
        resp = client.get("/api/league/info")
    assert resp.status_code == 200
    data = resp.json()
    assert "current_league" in data


# ---------------------------------------------------------------------------
# Modifier reference endpoints (static data — no DB needed)
# ---------------------------------------------------------------------------


def test_mod_reference(client: TestClient):
    with patch("poe_tablet_tool.modifiers_data.get_modifiers_separated", return_value=[]):
        resp = client.get("/api/reports/mod-reference")
    assert resp.status_code == 200


def test_mod_reference_separated(client: TestClient):
    with patch("poe_tablet_tool.modifiers_data.get_modifiers_separated", return_value=[]):
        resp = client.get("/api/reports/mod-reference-separated")
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# 503 when no active league
# ---------------------------------------------------------------------------


def test_reports_503_when_no_league(mem_conn: sqlite3.Connection):
    """Routes that require a league should return 503, not 500, when none is active."""
    with patch("poe_tablet_tool.report_builder.get_connection", return_value=mem_conn):
        tc = TestClient(app)
        resp = tc.get("/api/reports/affix-frequency")
    assert resp.status_code == 503
