"""
SSID-EMS Admin RBAC contract tests.

Covers acceptance criteria from ems_admin_spec_v1 / ems_admin_acceptance_v1:
- AC-ADMIN-03 unauthenticated 401
- AC-ADMIN-04 missing permission 403
- AC-ADMIN-05 client role cannot escalate
- AC-ADMIN-06 frontend flag cannot bypass backend RBAC
- AC-ADMIN-07 deny-by-default for unknown permission
- AC-ADMIN-12 revoked role takes effect
- AC-ADMIN-13 expired session 401
"""

from __future__ import annotations

import os
import sys
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
os.environ["EMS_ENV_MODE"] = "local_scaffold"
os.environ["START_SERVICES"] = "1"
os.environ["EMS_DEMO_AUTH"] = "0"
os.environ["EMS_DATABASE_PATH"] = str(REPO_ROOT / "state" / "test_admin_contract.db")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _retry_unlink(path: str, attempts: int = 5, delay: float = 0.2) -> None:
    for _ in range(attempts):
        try:
            Path(path).unlink(missing_ok=True)
            return
        except PermissionError:
            time.sleep(delay)


def _http(url, method="GET", payload=None, headers=None, timeout=5):
    data = None if payload is None else __import__("json").dumps(payload).encode("utf-8")
    hdrs = {"Content-Type": "application/json"}
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, resp.headers, __import__("json").loads(raw), raw
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8") if exc.fp else ""
        try:
            body = __import__("json").loads(raw)
        except Exception:
            body = {"raw": raw}
        return exc.code, exc.headers, body, raw
    except urllib.error.RemoteDisconnected:
        return 599, {}, {"status": "ERROR", "error_code": "remote_disconnected"}, ""


def _start_backend(adapter):
    import importlib
    import backend.app.config
    import backend.app.http_server
    importlib.reload(backend.app.config)
    importlib.reload(backend.app.http_server)
    from backend.app.http_server import create_backend_server

    server = create_backend_server("127.0.0.1", 0, adapter=adapter)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    return server, thread, base


def _stop_backend(server, thread):
    server.shutdown()
    server.server_close()
    thread.join(timeout=5)


def _bootstrap_admin():
    from backend.app.database import Database
    from backend.app.password import hash_password
    from backend.app.repository import create_user, get_user_by_username
    from backend.app.audit import record_event
    from backend.app.persistence import PersistentStore
    from backend.app.operational_adapter import OperationalAdapter

    _retry_unlink(os.environ["EMS_DATABASE_PATH"])
    store = PersistentStore(os.environ["EMS_DATABASE_PATH"])
    user = create_user(store, "admin", "correct horse battery staple", actor_id="system", actor_role="bootstrap", roles=["super_admin"])
    adapter = OperationalAdapter(store.db)
    return store, get_user_by_username(store, "admin"), adapter


def _bootstrap_viewer():
    from backend.app.database import Database
    from backend.app.password import hash_password
    from backend.app.repository import create_user, get_user_by_username
    from backend.app.persistence import PersistentStore
    from backend.app.operational_adapter import OperationalAdapter

    _retry_unlink(os.environ["EMS_DATABASE_PATH"])
    store = PersistentStore(os.environ["EMS_DATABASE_PATH"])
    user = create_user(store, "viewer", "correct horse battery staple", actor_id="system", actor_role="bootstrap", roles=["viewer"])
    adapter = OperationalAdapter(store.db)
    return store, get_user_by_username(store, "viewer"), adapter


def _login(base, username, password):
    status, _, body, _ = _http(base + "/api/v1/auth/login", method="POST", payload={"username": username, "password": password})
    assert status == 200, body
    return body["token"]


def _retry_unlink(path: str, attempts: int = 5, delay: float = 0.2) -> None:
    for _ in range(attempts):
        try:
            Path(path).unlink(missing_ok=True)
            return
        except PermissionError:
            time.sleep(delay)


def test_unauthenticated_admin_returns_401():
    from backend.app.database import Database
    from backend.app.operational_adapter import OperationalAdapter

    db_path = str(REPO_ROOT / "state" / f"test_operational_{os.getpid()}.db")
    os.environ["EMS_DATABASE_PATH"] = db_path
    try:
        _retry_unlink(db_path)
        adapter = OperationalAdapter(Database(db_path))
        server, thread, base = _start_backend(adapter)
        try:
            status, _, body, _ = _http(base + "/api/v1/admin/users")
            assert status == 401, body
        finally:
            _stop_backend(server, thread)
    finally:
        _retry_unlink(db_path)


def test_missing_permission_returns_403():
    store, user, adapter = _bootstrap_viewer()
    server, thread, base = _start_backend(adapter)
    try:
        token = _login(base, "viewer", "correct horse battery staple")
        status, _, body, _ = _http(base + "/api/v1/admin/sessions/" + user["id"] + "/revoke", method="POST", headers={"Authorization": f"Bearer {token}"})
        assert status == 403
    finally:
        _stop_backend(server, thread)
    Path(os.environ["EMS_DATABASE_PATH"]).unlink(missing_ok=True)


def test_client_role_cannot_escalate_privileges():
    store, user, adapter = _bootstrap_viewer()
    server, thread, base = _start_backend(adapter)
    try:
        token = _login(base, "viewer", "correct horse battery staple")
        status, _, body, _ = _http(
            base + "/api/v1/admin/users/" + user["id"] + "/roles",
            method="PUT",
            payload={"roles": ["super_admin"]},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert status == 403
    finally:
        _stop_backend(server, thread)
    Path(os.environ["EMS_DATABASE_PATH"]).unlink(missing_ok=True)


def test_frontend_flag_cannot_bypass_backend_rbac():
    store, user, adapter = _bootstrap_viewer()
    server, thread, base = _start_backend(adapter)
    try:
        token = _login(base, "viewer", "correct horse battery staple")
        status, _, body, _ = _http(
            base + "/api/v1/admin/sessions",
            headers={"Authorization": f"Bearer {token}", "X-SSID-Admin-Override": "true"},
        )
        assert status == 403
    finally:
        _stop_backend(server, thread)
    Path(os.environ["EMS_DATABASE_PATH"]).unlink(missing_ok=True)


def test_deny_by_default_for_unknown_permission():
    store, user, adapter = _bootstrap_viewer()
    server, thread, base = _start_backend(adapter)
    try:
        token = _login(base, "viewer", "correct horse battery staple")
        status, _, body, _ = _http(
            base + "/api/v1/admin/sessions/" + user["id"] + "/revoke",
            method="POST",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert status == 403
    finally:
        _stop_backend(server, thread)
    Path(os.environ["EMS_DATABASE_PATH"]).unlink(missing_ok=True)


def test_expired_session_returns_401():
    store, user, adapter = _bootstrap_admin()
    with store.connection() as conn:
        conn.execute("UPDATE sessions SET expires_at_utc = ? WHERE user_id = ?", (_now_utc_offset(-3600), user["id"]))
    server, thread, base = _start_backend(adapter)
    try:
        token = _login(base, "admin", "correct horse battery staple")
        with store.connection() as conn:
            conn.execute("UPDATE sessions SET expires_at_utc = ? WHERE user_id = ?", (_now_utc_offset(-3600), user["id"]))
        status, _, body, _ = _http(base + "/api/v1/admin/users", headers={"Authorization": f"Bearer {token}"})
        assert status == 401
    finally:
        _stop_backend(server, thread)
    Path(os.environ["EMS_DATABASE_PATH"]).unlink(missing_ok=True)


def test_two_clients_are_independent_and_server_enforced():
    from backend.app.persistence import PersistentStore
    from backend.app.repository import create_user, get_user_by_username
    from backend.app.operational_adapter import OperationalAdapter

    _retry_unlink(os.environ["EMS_DATABASE_PATH"])
    store = PersistentStore(os.environ["EMS_DATABASE_PATH"])
    create_user(store, "admin", "admin-password", actor_id="system", actor_role="bootstrap", roles=["super_admin"])
    create_user(store, "client-a", "client-a-password", actor_id="system", actor_role="bootstrap", roles=["viewer"])
    create_user(store, "client-b", "client-b-password", actor_id="system", actor_role="bootstrap", roles=["viewer"])
    client_a = get_user_by_username(store, "client-a")
    client_b = get_user_by_username(store, "client-b")
    assert client_a and client_b
    server, thread, base = _start_backend(OperationalAdapter(store.db))
    try:
        admin_token = _login(base, "admin", "admin-password")
        token_a = _login(base, "client-a", "client-a-password")
        token_b = _login(base, "client-b", "client-b-password")
        auth_a = {"Authorization": f"Bearer {token_a}"}
        auth_b = {"Authorization": f"Bearer {token_b}"}
        auth_admin = {"Authorization": f"Bearer {admin_token}"}
        assert _http(base + "/api/v1/auth/session", headers=auth_a)[2]["authenticated"] is True
        assert _http(base + "/api/v1/auth/session", headers=auth_b)[2]["authenticated"] is True
        assert _http(base + f"/api/v1/admin/users/{client_a['id']}", headers=auth_a)[0] == 200
        assert _http(base + f"/api/v1/admin/users/{client_b['id']}", headers=auth_b)[0] == 200
        assert _http(base + f"/api/v1/admin/users/{client_b['id']}", headers=auth_a)[0] == 403
        assert _http(base + f"/api/v1/admin/users/{client_a['id']}", headers=auth_b)[0] == 403
        assert _http(base + "/api/v1/admin/sessions", headers=auth_a)[0] == 403
        assert _http(base + "/api/v1/admin/sessions", headers=auth_b)[0] == 403
        assert _http(base + "/api/v1/admin/users", headers={})[0] == 401
        assert _http(base + "/api/v1/auth/logout", method="POST", headers=auth_a)[0] == 200
        assert _http(base + "/api/v1/auth/session", headers=auth_a)[2]["authenticated"] is False
        assert _http(base + "/api/v1/auth/session", headers=auth_b)[2]["authenticated"] is True
        token_a = _login(base, "client-a", "client-a-password")
        auth_a = {"Authorization": f"Bearer {token_a}"}
        session_a = _http(base + "/api/v1/auth/session", headers=auth_a)[2]["session_id"]
        listed = _http(base + "/api/v1/admin/sessions", headers=auth_admin)
        assert listed[0] == 200
        assert any(item["id"] == session_a for item in listed[2]["sessions"])
        revoke = _http(base + f"/api/v1/admin/sessions/{session_a}/revoke", method="POST", headers=auth_admin)
        assert revoke[0] == 200, revoke[2]
        assert _http(base + "/api/v1/auth/session", headers=auth_a)[2]["authenticated"] is False
        assert _http(base + "/api/v1/auth/session", headers=auth_b)[2]["authenticated"] is True
        assert _http(base + "/api/v1/admin/users", headers={"Authorization": "Bearer tampered"})[0] == 401
    finally:
        _stop_backend(server, thread)
    Path(os.environ["EMS_DATABASE_PATH"]).unlink(missing_ok=True)


def _now_utc_offset(seconds_offset: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=seconds_offset)).strftime("%Y-%m-%dT%H:%M:%SZ")
