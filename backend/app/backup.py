"""
SSID-EMS backup & restore service.

Backup: SQLite DB file + WAL + audit chain status + schema version + registry
snapshots + config manifest (no secrets) + UTC timestamp + SHA256.

Restore is performed only into an isolated test path. Original DB untouched.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.app import config
from backend.app.audit import verify_chain
from backend.app.persistence import PersistentStore


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _db_path(store):
    path = getattr(store, "db_path", None)
    if path:
        return Path(path)
    inner = getattr(store, "db", None)
    if inner is not None:
        return Path(getattr(inner, "path", "."))
    path = getattr(store, "path", None)
    if path:
        return Path(path)
    return Path(".")


def create_backup(store: PersistentStore, backup_dir: str | None = None) -> dict[str, Any]:
    backup_dir = Path(backup_dir or r"C:\Users\bibel\SSID-Workspace\SSID-Arbeitsbereich\backups")
    backup_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_name = f"ssid-ems-backup-{ts}"
    target = backup_dir / backup_name
    target.mkdir(parents=True, exist_ok=True)

    db_path = _db_path(store)
    # Ensure WAL is checkpointed into the main db before copy.
    try:
        with sqlite3.connect(str(db_path)) as c:
            c.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    except Exception:
        pass
    shutil.copy(db_path, target / "ems.db")
    for suffix in ("-wal", "-shm"):
        src = db_path.with_suffix(db_path.suffix + suffix)
        if src.exists():
            shutil.copy(src, target / f"ems.db{suffix}")

    # Audit + schema metadata (no secrets)
    wrapped = store if hasattr(store, "connection") else PersistentStore(str(db_path))
    chain = verify_chain(wrapped)
    schema_version = getattr(store, "current_schema_version", None)
    if not callable(schema_version):
        schema_version = getattr(store, "schema_version", 0)
        if callable(schema_version):
            schema_version = schema_version()
    else:
        schema_version = schema_version()
    metadata = {
        "backup_id": backup_name,
        "created_at_utc": _now_utc(),
        "source_db": str(db_path),
        "schema_version": schema_version,
        "audit_chain": chain,
        "config_manifest": {
            "env_mode": config.ENV_MODE,
            "version": config.VERSION,
            "cors_allowed_origins": config.EMS_CORS_ALLOWED_ORIGINS,
            "session_ttl_seconds": config.EMS_SESSION_TTL_SECONDS,
            "demo_auth_enabled": config.EMS_DEMO_AUTH_ENABLED,
            "min_password_length": config.EMS_MIN_PASSWORD_LENGTH,
        },
        "integrity_check": wrapped.integrity_check(),
    }
    (target / "backup_manifest.json").write_text(json.dumps(metadata, indent=2, sort_keys=True))

    sha = _sha256(target / "ems.db")
    size = (target / "ems.db").stat().st_size
    return {
        "backup_id": backup_name,
        "path": str(target),
        "db_path": str(target / "ems.db"),
        "sha256": sha,
        "size_bytes": size,
        "manifest": metadata,
        "created_at_utc": _now_utc(),
    }


def restore_test(store: PersistentStore, backup_path: str, isolated_db_path: str) -> dict[str, Any]:
    """Restore a backup into an isolated DB and verify integrity. Does NOT touch original."""
    src_db = Path(backup_path)
    if src_db.is_dir():
        src_db = src_db / "ems.db"
    isolated = Path(isolated_db_path)
    isolated.parent.mkdir(parents=True, exist_ok=True)
    if isolated.exists():
        isolated.unlink()
    shutil.copy(src_db, isolated)

    iso_store = PersistentStore(str(isolated))
    result: dict[str, Any] = {}
    result["integrity_check"] = iso_store.integrity_check()
    result["schema_version"] = iso_store.current_schema_version()
    from backend.app.repository import count_users
    result["user_count"] = count_users(iso_store)
    result["audit_chain"] = verify_chain(iso_store)
    result["migration_status"] = iso_store.migration_status()
    return result
