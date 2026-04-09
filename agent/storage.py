import os
import sqlite3
from pathlib import Path


PRIMARY_APP_HOME = Path(os.getenv("LOCALAPPDATA", str(Path.home()))) / "research-agent-cli"
FALLBACK_APP_HOME = Path.cwd() / ".agent-data"
DB_NAME = "preferences.db"


CREATE_PREFERENCES_TABLE = """
CREATE TABLE IF NOT EXISTS preferences (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
)
"""


CREATE_RUN_STATE_TABLE = """
CREATE TABLE IF NOT EXISTS run_state (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    last_report_path TEXT,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
)
"""


APP_HOME = None
DB_PATH = None


def initialize_storage() -> None:
    global APP_HOME, DB_PATH

    if APP_HOME is None or DB_PATH is None:
        APP_HOME = _resolve_app_home()
        DB_PATH = APP_HOME / DB_NAME

    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(CREATE_PREFERENCES_TABLE)
        connection.execute(CREATE_RUN_STATE_TABLE)
        connection.commit()



def get_preference(key: str) -> str | None:
    initialize_storage()
    with sqlite3.connect(DB_PATH) as connection:
        row = connection.execute(
            "SELECT value FROM preferences WHERE key = ?",
            (key,),
        ).fetchone()
    return row[0] if row else None



def list_preferences() -> list[tuple[str, str, str]]:
    initialize_storage()
    with sqlite3.connect(DB_PATH) as connection:
        rows = connection.execute(
            "SELECT key, value, updated_at FROM preferences ORDER BY key"
        ).fetchall()
    return [(row[0], row[1], row[2]) for row in rows]



def set_preference(key: str, value: str) -> None:
    initialize_storage()
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(
            """
            INSERT INTO preferences(key, value, updated_at)
            VALUES(?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                updated_at = CURRENT_TIMESTAMP
            """,
            (key, value),
        )
        connection.commit()



def delete_preference(key: str) -> bool:
    initialize_storage()
    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.execute(
            "DELETE FROM preferences WHERE key = ?",
            (key,),
        )
        connection.commit()
    return cursor.rowcount > 0



def clear_preferences() -> None:
    initialize_storage()
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("DELETE FROM preferences")
        connection.commit()



def set_last_report_path(path: str) -> None:
    initialize_storage()
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(
            """
            INSERT INTO run_state(id, last_report_path, updated_at)
            VALUES(1, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET
                last_report_path = excluded.last_report_path,
                updated_at = CURRENT_TIMESTAMP
            """,
            (path,),
        )
        connection.commit()



def get_last_report_path() -> str | None:
    initialize_storage()
    with sqlite3.connect(DB_PATH) as connection:
        row = connection.execute(
            "SELECT last_report_path FROM run_state WHERE id = 1"
        ).fetchone()
    return row[0] if row else None



def _resolve_app_home() -> Path:
    for candidate in (PRIMARY_APP_HOME, FALLBACK_APP_HOME):
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write-test"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
            return candidate
        except Exception:
            continue

    raise PermissionError(
        "Could not create writable storage for preferences. Tried LocalAppData and .agent-data in the current folder."
    )
