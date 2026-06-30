"""
Main scheduler and orchestrator.

Staggered 60-minute cycle across all tablet types and query modes:
  Each (tablet_type, query_mode) pair gets its own scheduled slot.
  Jobs spread across the hour to avoid bursting all requests at once.

Run:
  python -m poe_tablet_tool.scheduler
"""

import logging
from datetime import datetime, timezone

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

from poe_tablet_tool.analytics import run_all_analytics
from poe_tablet_tool.config import settings
from poe_tablet_tool.db import init_db
from poe_tablet_tool.differ import diff_snapshots
from poe_tablet_tool.health import record_failure, record_success
from poe_tablet_tool.league_detector import detect_league, ensure_league_in_db
from poe_tablet_tool.league_reset import reset_for_new_league
from poe_tablet_tool.parser import filter_for_query_mode, parse_all
from poe_tablet_tool.query_builder import (
    MAGIC_MODE,
    NORMAL_MODE,
    RARE_MODE,
    build_magic_query,
    build_normal_query,
    build_rare_query,
)
from poe_tablet_tool.rate_provider import refresh_rates
from poe_tablet_tool.scraper import search_and_fetch_dual
from poe_tablet_tool.snapshot_store import create_snapshot, store_listings
from poe_tablet_tool.tablets import TABLET_TYPES

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

_current_league_name: str = ""
_current_league_id: int = 0


def _run_scheduled_analytics() -> None:
    if _current_league_id:
        run_all_analytics(_current_league_id)


def _detect_and_sync_league() -> tuple[str, int]:
    global _current_league_name, _current_league_id

    new_name = detect_league()

    if _current_league_name and new_name != _current_league_name:
        logger.warning(
            "League changed: %s → %s. Archiving and resetting.",
            _current_league_name,
            new_name,
        )
        reset_for_new_league(_current_league_name)
        init_db()

    _current_league_name = new_name
    _current_league_id = ensure_league_in_db(new_name)
    refresh_rates(_current_league_id)
    return _current_league_name, _current_league_id


def run_snapshot_job(tablet_key: str, query_mode: str) -> None:
    tablet = TABLET_TYPES[tablet_key]
    league_name = _current_league_name
    league_id = _current_league_id

    if not league_name or not league_id:
        logger.warning(
            "League not initialized, skipping job %s/%s", tablet_key, query_mode
        )
        return

    logger.info("▶ Starting snapshot: %s / %s", tablet.label, query_mode)

    try:
        if query_mode == RARE_MODE:
            payload_asc, query_hash = build_rare_query(tablet, league_name, sort="asc")
            payload_desc, _ = build_rare_query(tablet, league_name, sort="desc")
        elif query_mode == MAGIC_MODE:
            payload_asc, query_hash = build_magic_query(tablet, league_name, sort="asc")
            payload_desc, _ = build_magic_query(tablet, league_name, sort="desc")
        else:
            payload_asc, query_hash = build_normal_query(
                tablet, league_name, sort="asc"
            )
            payload_desc, _ = build_normal_query(tablet, league_name, sort="desc")

        raw_results, total_count, fetched_count = search_and_fetch_dual(
            league_name, payload_asc, payload_desc
        )

        if not raw_results:
            logger.info("No results for %s/%s", tablet_key, query_mode)
            record_success(tablet_key, query_mode, 0, total_count, fetched_count)
            return

        parsed = filter_for_query_mode(parse_all(raw_results), query_mode)

        snapshot_id = create_snapshot(
            league_id=league_id,
            tablet_type=tablet_key,
            query_mode=query_mode,
            query_hash=query_hash,
            listing_count=len(parsed),
            total_count=total_count,
            fetched_count=fetched_count,
        )

        store_listings(snapshot_id, league_id, tablet_key, query_mode, parsed)
        disappeared = diff_snapshots(league_id, tablet_key, query_mode, snapshot_id)

        record_success(
            tablet_key,
            query_mode,
            len(parsed),
            total_count,
            fetched_count,
        )

        logger.info(
            "✔ Done: %s/%s — %d stored (%d fetched/%d total), %d disappeared",
            tablet.label,
            query_mode,
            len(parsed),
            fetched_count,
            total_count,
            disappeared,
        )

    except Exception as exc:
        logger.exception("✘ Job failed: %s/%s", tablet_key, query_mode)
        record_failure(tablet_key, query_mode, str(exc))


def _schedule_jobs(scheduler: BlockingScheduler) -> None:
    jobs = [
        (tablet_key, mode)
        for tablet_key in TABLET_TYPES
        for mode in (RARE_MODE, MAGIC_MODE, NORMAL_MODE)
    ]

    interval_minutes = settings.snapshot_interval_minutes
    slot_minutes = interval_minutes / len(jobs)

    for i, (tablet_key, mode) in enumerate(jobs):
        delay_seconds = int(i * slot_minutes * 60)

        scheduler.add_job(
            run_snapshot_job,
            trigger=IntervalTrigger(minutes=interval_minutes),
            args=[tablet_key, mode],
            id=f"{tablet_key}_{mode}",
            name=f"{TABLET_TYPES[tablet_key].label} / {mode}",
            next_run_time=_offset_now(delay_seconds),
            max_instances=1,
            coalesce=True,
        )


def _offset_now(seconds: int):
    from datetime import timedelta

    return datetime.now(timezone.utc) + timedelta(seconds=seconds)


def run_single_snapshot_job(tablet_key: str, query_mode: str) -> dict:
    """
    Run a single snapshot job manually (for backfill or debugging).
    Returns result summary.
    """
    tablet = TABLET_TYPES[tablet_key]
    league_name = _current_league_name
    league_id = _current_league_id

    if not league_name or not league_id:
        return {"error": "League not initialized"}

    try:
        if query_mode == RARE_MODE:
            payload_asc, query_hash = build_rare_query(tablet, league_name, sort="asc")
            payload_desc, _ = build_rare_query(tablet, league_name, sort="desc")
        elif query_mode == MAGIC_MODE:
            payload_asc, query_hash = build_magic_query(tablet, league_name, sort="asc")
            payload_desc, _ = build_magic_query(tablet, league_name, sort="desc")
        else:
            payload_asc, query_hash = build_normal_query(
                tablet, league_name, sort="asc"
            )
            payload_desc, _ = build_normal_query(tablet, league_name, sort="desc")

        raw_results, total_count, fetched_count = search_and_fetch_dual(
            league_name, payload_asc, payload_desc
        )

        if not raw_results:
            return {
                "tablet_type": tablet_key,
                "query_mode": query_mode,
                "listings": 0,
                "total": total_count,
                "fetched": fetched_count,
                "message": "No results",
            }

        from poe_tablet_tool.parser import filter_for_query_mode, parse_all

        parsed = filter_for_query_mode(parse_all(raw_results), query_mode)

        from poe_tablet_tool.snapshot_store import create_snapshot, store_listings

        snapshot_id = create_snapshot(
            league_id=league_id,
            tablet_type=tablet_key,
            query_mode=query_mode,
            query_hash=query_hash,
            listing_count=len(parsed),
            total_count=total_count,
            fetched_count=fetched_count,
        )

        store_listings(snapshot_id, league_id, tablet_key, query_mode, parsed)
        disappeared = diff_snapshots(league_id, tablet_key, query_mode, snapshot_id)

        record_success(
            tablet_key,
            query_mode,
            len(parsed),
            total_count,
            fetched_count,
        )

        return {
            "tablet_type": tablet_key,
            "query_mode": query_mode,
            "listings_stored": len(parsed),
            "total_count": total_count,
            "fetched_count": fetched_count,
            "disappeared": disappeared,
            "snapshot_id": snapshot_id,
            "status": "success",
        }

    except Exception as exc:
        logger.exception("Manual job failed: %s/%s", tablet_key, query_mode)
        record_failure(tablet_key, query_mode, str(exc))
        return {
            "tablet_type": tablet_key,
            "query_mode": query_mode,
            "error": str(exc),
            "status": "failed",
        }


def main() -> None:
    logger.info("=== PoE2 Tablet Tool starting ===")

    init_db()
    _detect_and_sync_league()
    logger.info("Active league: %s (id=%d)", _current_league_name, _current_league_id)

    scheduler = BlockingScheduler(timezone="UTC")

    scheduler.add_job(
        _detect_and_sync_league,
        trigger=IntervalTrigger(minutes=settings.snapshot_interval_minutes),
        id="league_refresh",
        name="League Refresh",
        next_run_time=_offset_now(30),
    )

    scheduler.add_job(
        _run_scheduled_analytics,
        trigger=IntervalTrigger(minutes=settings.snapshot_interval_minutes),
        id="analytics_refresh",
        name="Analytics Refresh",
        next_run_time=_offset_now(60),
    )

    _schedule_jobs(scheduler)

    logger.info(
        "Scheduler running — %d jobs across %d-minute cycle. Press Ctrl+C to stop.",
        len(TABLET_TYPES) * 3,
        settings.snapshot_interval_minutes,
    )

    if settings.enable_api:
        import threading

        from poe_tablet_tool.api import main as run_api

        threading.Thread(
            target=run_api,
            name="api-server",
            daemon=True,
        ).start()
        logger.info(
            "API server starting on %s:%d", settings.api_host, settings.api_port
        )

    try:
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Shutting down.")


if __name__ == "__main__":
    main()
