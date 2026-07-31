"""SSID-EMS SQLite persistence layer.

Stdlib-only. No external dependencies.
WAL mode, foreign keys, parameterized queries only.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generator, Iterator

DB_DEFAULT_PATH = "state/ems.db"

SCHEMA_VERSION = 1

SCHEMA_SQL_V1 = """\
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;
PRAGMA synchronous=FULL;

CREATE TABLE IF NOT EXISTS schema_migrations (
    migration_id TEXT PRIMARY KEY,
    checksum TEXT NOT NULL,
    applied_at_utc TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username_normalized TEXT NOT NULL UNIQUE,
    username_display TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL,
    disabled_at_utc TEXT,
    session_version INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS roles (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    system_role BOOLEAN NOT NULL DEFAULT 0,
    created_at_utc TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS permissions (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE IF NOT EXISTS user_roles (
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id TEXT NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);

CREATE TABLE IF NOT EXISTS role_permissions (
    role_id TEXT NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id TEXT NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL,
    csrf_token_hash TEXT NOT NULL,
    created_at_utc TEXT NOT NULL,
    expires_at_utc TEXT NOT NULL,
    last_seen_at_utc TEXT NOT NULL,
    revoked_at_utc TEXT,
    source_hash TEXT NOT NULL,
    user_agent_hash TEXT NOT NULL,
    session_version INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS login_attempts (
    id TEXT PRIMARY KEY,
    username_normalized TEXT NOT NULL,
    source_hash TEXT NOT NULL,
    success BOOLEAN NOT NULL,
    attempted_at_utc TEXT NOT NULL,
    reason TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS audit_events (
    sequence_number INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL UNIQUE,
    timestamp_utc TEXT NOT NULL,
    actor_id TEXT,
    actor_role TEXT,
    action TEXT NOT NULL,
    resource_type TEXT,
    resource_id TEXT,
    result TEXT NOT NULL,
    reason TEXT,
    request_id TEXT,
    correlation_id TEXT,
    source_service TEXT NOT NULL,
    previous_hash TEXT NOT NULL,
    event_hash TEXT NOT NULL,
    payload_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_audit_events_timestamp ON audit_events(timestamp_utc);
CREATE INDEX IF NOT EXISTS idx_audit_events_actor ON audit_events(actor_id);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_login_attempts_username ON login_attempts(username_normalized, attempted_at_utc);
"""

from backend.app.migrations import MIGRATIONS


class DatabaseError(Exception):
    """Raised on database constraint violation or connection failure."""


class Database:
    """Thread-safe SQLite database wrapper."""

    def __init__(self, path: str | Path = DB_DEFAULT_PATH) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._lock = threading.Lock()
        self._schema_version = self._ensure_schema()

    @contextmanager
    def _connection(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(str(self.path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA synchronous=FULL")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _ensure_schema(self) -> int:
        with self._lock:
            with self._connection() as conn:
                conn.executescript(SCHEMA_SQL_V1)
                for migration in MIGRATIONS:
                    row = conn.execute(
                        "SELECT migration_id, checksum FROM schema_migrations WHERE migration_id = ?",
                        (migration["migration_id"],),
                    ).fetchone()
                    expected_checksum = migration.get("checksum") or __import__("hashlib").sha256(migration.get("sql", "").encode()).hexdigest()
                    if row is None or row["checksum"] != expected_checksum:
                        sql = migration.get("sql")
                        if sql:
                            conn.executescript(sql)
                        conn.execute(
                            "INSERT OR REPLACE INTO schema_migrations (migration_id, checksum, applied_at_utc) VALUES (?, ?, ?)",
                            (
                                migration["migration_id"],
                                expected_checksum,
                                datetime.now(timezone.utc).isoformat(),
                            ),
                        )
                Database._migrate_login_attempts(conn)
                return Database._current_schema_version(conn)

    @staticmethod
    def _migrate_login_attempts(conn: sqlite3.Connection) -> None:
        cols = {r["name"] for r in conn.execute("PRAGMA table_info(login_attempts)").fetchall()}
        if "attempted_at_utc" not in cols:
            conn.execute("ALTER TABLE login_attempts ADD COLUMN attempted_at_utc TEXT NOT NULL DEFAULT ''")
        if "reason" not in cols:
            conn.execute("ALTER TABLE login_attempts ADD COLUMN reason TEXT NOT NULL DEFAULT ''")

    @staticmethod
    def _current_schema_version(conn: sqlite3.Connection) -> int:
        row = conn.execute("SELECT MAX(migration_id) FROM schema_migrations").fetchone()
        if row and row[0]:
            # parse version from migration_id like "v1_initial_schema"
            try:
                return int(row[0].split("_")[0][1:])
            except (ValueError, IndexError):
                return 0
        return 0

    def integrity_check(self) -> bool:
        with self._connection() as conn:
            row = conn.execute("PRAGMA integrity_check").fetchone()
            return row is not None and row[0] == "ok"

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Cursor:
        with self._connection() as conn:
            return conn.execute(sql, params)

    def executemany(self, sql: str, params_list: list[tuple[Any, ...]]) -> None:
        with self._connection() as conn:
            conn.executemany(sql, params_list)

    def fetchone(self, sql: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
        with self._connection() as conn:
            row = conn.execute(sql, params).fetchone()
            return dict(row) if row else None

    def fetchall(self, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        with self._connection() as conn:
            return [dict(r) for r in conn.execute(sql, params).fetchall()]

    @property
    def schema_version(self) -> int:
        return self._schema_version

    def ensure_schema(self) -> None:
        self._ensure_schema()

    def connection(self):  # noqa: D401
        return self._connection()
