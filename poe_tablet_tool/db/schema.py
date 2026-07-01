"""
Database schema creation via the versioned migration system.
Call init_db() once at startup.
"""

from poe_tablet_tool.db.connection import get_connection
from poe_tablet_tool.db.migrations import apply_migrations


def init_db() -> None:
    conn = get_connection()
    apply_migrations(conn)
