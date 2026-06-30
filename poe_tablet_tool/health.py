"""
Per-job health tracking for the snapshot scheduler.
"""

import logging
from datetime import datetime, timezone

import httpx

from poe_tablet_tool.config import settings
from poe_tablet_tool.db.connection import get_connection

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def job_key(tablet_type: str, query_mode: str) -> str:
    return f"{tablet_type}/{query_mode}"


def record_success(
    tablet_type: str,
    query_mode: str,
    listing_count: int,
    total_count: int,
    fetched_count: int,
) -> None:
    conn = get_connection()
    key = job_key(tablet_type, query_mode)
    conn.execute(
        """
        INSERT INTO job_health (
            job_key, last_success_at, last_listing_count,
            last_total_count, last_fetched_count, last_error, last_error_at
        ) VALUES (?, ?, ?, ?, ?, NULL, NULL)
        ON CONFLICT (job_key) DO UPDATE SET
            last_success_at = excluded.last_success_at,
            last_listing_count = excluded.last_listing_count,
            last_total_count = excluded.last_total_count,
            last_fetched_count = excluded.last_fetched_count,
            last_error = NULL,
            last_error_at = NULL
        """,
        (key, _now(), listing_count, total_count, fetched_count),
    )
    conn.commit()


def record_failure(tablet_type: str, query_mode: str, error: str) -> None:
    conn = get_connection()
    key = job_key(tablet_type, query_mode)
    conn.execute(
        """
        INSERT INTO job_health (job_key, last_error, last_error_at)
        VALUES (?, ?, ?)
        ON CONFLICT (job_key) DO UPDATE SET
            last_error = excluded.last_error,
            last_error_at = excluded.last_error_at
        """,
        (key, error[:500], _now()),
    )
    conn.commit()


def get_all_health() -> list[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM job_health ORDER BY job_key").fetchall()
    return [dict(r) for r in rows]


def get_db_health() -> dict:
    """Check database health metrics."""
    conn = get_connection()

    try:
        # Count tables and rows
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()

        total_rows = conn.execute(
            """
            SELECT SUM(row_count) as total
            FROM (
                SELECT COUNT(*) as row_count FROM leagues
                UNION ALL SELECT COUNT(*) FROM snapshots
                UNION ALL SELECT COUNT(*) FROM listings
                UNION ALL SELECT COUNT(*) FROM affixes
                UNION ALL SELECT COUNT(*) FROM listing_disappearances
                UNION ALL SELECT COUNT(*) FROM job_health
            )
            """
        ).fetchone()

        last_snapshot = conn.execute(
            "SELECT MAX(taken_at) as last FROM snapshots"
        ).fetchone()

        return {
            "status": "healthy",
            "tables": len(tables),
            "total_rows": total_rows["total"] if total_rows else 0,
            "last_snapshot_at": last_snapshot["last"] if last_snapshot else None,
            "error": None,
        }
    except Exception as e:
        return {
            "status": "error",
            "tables": 0,
            "total_rows": 0,
            "last_snapshot_at": None,
            "error": str(e),
        }


def check_poe_api_health() -> dict:
    """Check if PoE trade API is responding."""
    try:
        client = httpx.Client(
            headers=settings.request_headers,
            timeout=10,
        )
        # Check leagues endpoint (lightweight)
        resp = client.get(f"{settings.leagues_api_url}")

        if resp.status_code == 200:
            return {
                "status": "healthy",
                "endpoint": settings.leagues_api_url,
                "response_time_ms": int(resp.elapsed.total_seconds() * 1000),
                "error": None,
            }
        else:
            return {
                "status": "error",
                "endpoint": settings.leagues_api_url,
                "response_time_ms": int(resp.elapsed.total_seconds() * 1000),
                "error": f"HTTP {resp.status_code}",
            }
    except Exception as e:
        return {
            "status": "unreachable",
            "endpoint": settings.leagues_api_url,
            "response_time_ms": None,
            "error": str(e),
        }


def get_last_snapshot_times() -> list[dict]:
    """Get most recent snapshot times for each tablet type and mode."""
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT tablet_type, query_mode, MAX(taken_at) as last_snapshot_at
        FROM snapshots
        GROUP BY tablet_type, query_mode
        ORDER BY tablet_type, query_mode
        """
    ).fetchall()
    return [dict(r) for r in rows]


def get_detailed_health() -> dict:
    """Get comprehensive health status."""
    return {
        "status": "ok",
        "timestamp": _now(),
        "poe_api": check_poe_api_health(),
        "database": get_db_health(),
        "scheduler": {
            "jobs": get_all_health(),
            "total_jobs": len(get_all_health()),
        },
        "last_snapshots": get_last_snapshot_times(),
    }
