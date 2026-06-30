"""
Archives the current league DB and resets for a new league.
"""

import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path

from poe_tablet_tool.config import settings
from poe_tablet_tool.db.connection import get_connection

logger = logging.getLogger(__name__)


def archive_league(old_league_name: str) -> None:
    """Copy the current DB file to a timestamped archive."""
    db_path = Path(settings.database_path)
    if not db_path.exists():
        return

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    safe_name = old_league_name.replace(" ", "_").lower()
    archive_path = db_path.parent / f"archive_{safe_name}_{timestamp}.db"

    shutil.copy2(db_path, archive_path)
    logger.info("Archived league DB to %s", archive_path)


def reset_for_new_league(old_league_name: str) -> None:
    """Archive previous league and wipe the working DB for a fresh start."""
    if settings.archive_on_league_reset:
        archive_league(old_league_name)

    db_path = Path(settings.database_path)
    if db_path.exists():
        db_path.unlink()
        logger.info("Deleted working DB for league reset")

    # Re-init will happen automatically on next get_connection() + init_db() call


def get_all_leagues() -> list[dict]:
    """Get all leagues from the database."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, name, started_at, ended_at, is_active FROM leagues ORDER BY started_at DESC"
    ).fetchall()
    return [dict(r) for r in rows]
