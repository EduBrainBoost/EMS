"""
SSID-EMS Phase 2/3 minimal operational hardening checks.

Single-file runnable check for the lazy path: DB persistence, password hashing,
auth/session, RBAC denial, CORS/CSRF/rate helpers, audit chain, backup/restore,
and one live HTTP happy path with START_SERVICES=True.
"""

from __future__ import annotations

import gc
import hashlib
import os
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Config / env
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
os.environ["EMS_ENV_MODE"] = "local_scaffold"
os.environ["START_SERVICES"] = "1"
os.environ["EMS_DEMO_AUTH"] = "0"
os.environ["EMS_DATABASE_PATH"] = str(REPO_ROOT / "state" / "test_operational.db")
# Keep runtime imports local to avoid collection-time side effects.
sys_mod = __import__("sys")
if str(REPO_ROOT) not in sys_mod.path:
    sys_mod.path.insert(0, str(REPO_ROOT))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _http(url, method="GET", payload=None, headers=None, timeout=5):
    data = None if payload is None else __import__("json").dumps(payload).encode("utf-8")
    hdrs = {"Content-Type": "application/json"}
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310 - run-owned localhost test server
            raw = resp.read().decode("utf-8")
            return resp.status, resp.headers, __import__("json").loads(raw), raw
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8") if exc.fp else ""
        return exc.code, exc.headers, __import__("json").loads(raw), raw


# ---------------------------------------------------------------------------
# Database + password + RBAC
# ---------------------------------------------------------------------------
def test_database_persistence_roundtrip():
    from backend.app.database import Database
    db = Database(os.environ["EMS_DATABASE_PATH"])
    try:
        assert db.schema_version >= 1
        assert db.integrity_check() is True
        uid = "usr_" + __import__("secrets").token_hex(6)
        db.execute(
            "INSERT INTO users (id, username_normalized, username_display, password_hash, status, created_at_utc, updated_at_utc) VALUES (?, ?, ?, ?, 'active', datetime('now'), datetime('now'))",
            (uid, "alice", "Alice", "x"),
        )
        row = db.fetchone("SELECT id FROM users WHERE id = ?", (uid,))
        assert row and row["id"] == uid
    finally:
        Path(os.environ["EMS_DATABASE_PATH"]).unlink(missing_ok=True)


def test_password_scrypt_roundtrip():
    from backend.app.password import hash_password, verify_password
    h = hash_password("correct horse battery staple")
    assert verify_password("correct horse battery staple", h) is True
    assert verify_password("wrong password", h) is False


def test_rbac_deny_by_default():
    from backend.app.rbac import AuthContext, require_permission, RBACError
    ctx = AuthContext(user_id="u1", username="u", roles=[], authenticated=True)
    with pytest.raises(RBACError) as exc:
        require_permission(None, ctx, "users.manage")
    assert exc.value.status_code == 403


# ---------------------------------------------------------------------------
# CORS / CSRF / rate
# ---------------------------------------------------------------------------
def test_cors_allowlist():
    from backend.app.security import is_origin_allowed, cors_headers
    assert is_origin_allowed("http://127.0.0.1:3100") is True
    assert is_origin_allowed("http://evil.example") is False
    assert is_origin_allowed("null") is False
    hdrs = cors_headers("http://127.0.0.1:3100")
    assert hdrs["Access-Control-Allow-Origin"] == "http://127.0.0.1:3100"


def test_csrf_live():
    from backend.app.security import new_csrf_token, csrf_matches
    tok = new_csrf_token()
    assert csrf_matches(tok, hashlib.sha256(tok.encode()).hexdigest()) is True
    assert csrf_matches("bad", hashlib.sha256(tok.encode()).hexdigest()) is False


def test_rate_limit_live():
    from backend.app.security import RateLimiter
    rl = RateLimiter()
    ok, rem = rl.check("x", 2, 60)
    assert ok is True and rem == 2
    rl.hit("x", 60)
    rl.hit("x", 60)
    ok, _ = rl.check("x", 2, 60)
    assert ok is False


# ---------------------------------------------------------------------------
# Audit chain
# ---------------------------------------------------------------------------
def test_audit_chain_live():
    from backend.app.persistence import PersistentStore
    from backend.app.audit import record_event, verify_chain
    store = PersistentStore(os.environ["EMS_DATABASE_PATH"])
    try:
        ev1 = record_event(store, "service.started", "system", "bootstrap", "service", "ssid-ems", "success")
        ev2 = record_event(store, "auth.login.success", "u1", "admin", "auth", "login", "success")
        res = verify_chain(store)
        assert res["chain_valid"] is True
        assert res["event_count"] == 2
        assert res["last_event_hash"] == ev2["event_hash"]
    finally:
        try:
            store.db._connection().close()
        except Exception:
            pass
        Path(os.environ["EMS_DATABASE_PATH"]).unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Backup/restore
# ---------------------------------------------------------------------------
def test_backup_restore_live():
    from backend.app.persistence import PersistentStore
    from backend.app.backup import create_backup, restore_test
    store = PersistentStore(os.environ["EMS_DATABASE_PATH"])
    try:
        store.db.execute(
            "INSERT INTO users (id, username_normalized, username_display, password_hash, status, created_at_utc, updated_at_utc) VALUES (?, ?, ?, ?, 'active', datetime('now'), datetime('now'))",
            ("usr_backup", "bob", "Bob", "x"),
        )
        backup = create_backup(store)
        assert backup["sha256"]
        iso = str(REPO_ROOT / "state" / "test_restore.db")
        res = restore_test(store, backup["db_path"], iso)
        assert res["integrity_check"] is True
        assert res["user_count"] == 1
        assert res["audit_chain"]["chain_valid"] is True
        Path(iso).unlink(missing_ok=True)
    finally:
        try:
            store.db._connection().close()
        except Exception:
            pass
        for _ in range(5):
            try:
                Path(os.environ["EMS_DATABASE_PATH"]).unlink(missing_ok=True)
                break
            except PermissionError:
                gc.collect()
                time.sleep(0.2)


# ---------------------------------------------------------------------------
# Live HTTP happy path with operational mode enabled
# ---------------------------------------------------------------------------
def test_live_http_operational_path():
    # Keep demo disabled and services enabled for this test.
    os.environ["START_SERVICES"] = "1"
    from backend.app.http_server import create_backend_server

    server = create_backend_server("127.0.0.1", 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        status, _, body, _ = _http(base + "/status")
        assert status == 200
        assert body["service"] == "SSID-EMS"
        status, _, body, _ = _http(base + "/api/mvp/auth/login", method="POST", payload={"username": "nope", "password": "nope"})
        assert status == 401
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
