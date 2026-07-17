"""
SSID-EMS persistence compatibility shim.

Provides the historic `PersistentStore` and `ZERO_HASH` names on top of the
existing stdlib `Database` wrapper so existing imports keep working.
"""

from __future__ import annotations

from backend.app.database import Database, SCHEMA_VERSION

ZERO_HASH = "0" * 64


class PersistentStore:
    """Compatibility wrapper around `Database`."""

    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = db_path or None
        self.db = Database(self.db_path)

    def connection(self):  # noqa: D401
        return self.db._connection()

    def ensure_schema(self) -> None:
        self.db._ensure_schema()

    def integrity_check(self) -> bool:
        return self.db.integrity_check()

    def current_schema_version(self) -> int:
        return int(self.db.schema_version)

    def migration_status(self) -> list[dict]:
        try:
            rows = self.db.fetchall("SELECT migration_id, checksum, applied_at_utc FROM schema_migrations")
            return [dict(r) for r in rows]
        except Exception:  # noqa: BLE001
            return []

    def close(self) -> None:
        pass
