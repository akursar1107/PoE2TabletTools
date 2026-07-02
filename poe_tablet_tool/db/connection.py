import sqlite3
import threading
from pathlib import Path

from poe_tablet_tool.config import settings

_local = threading.local()


def get_connection() -> sqlite3.Connection:
    """Return a per-thread SQLite connection, creating it if needed."""
    if not hasattr(_local, "conn") or _local.conn is None:
        db_path = Path(settings.database_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path), detect_types=sqlite3.PARSE_DECLTYPES)
        conn.row_factory = sqlite3.Row
        # Performance optimizations
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=-20000")  # 20MB cache
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.execute("PRAGMA foreign_keys=ON")
        _local.conn = conn
    return _local.conn
