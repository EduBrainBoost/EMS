"""
SSID-EMS Admin API contract tests.

Validates stable admin API shape for core endpoints.
"""

from __future__ import annotations

import os
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
os.environ["EMS_ENV_MODE"] = "local_scaffold"
os.environ["START_SERVICES"] = "1"
os.environ["EMS_DEMO_AUTH"] = "0"
os.environ["EMS_DATABASE_PATH"] = str(REPO_ROOT / "state" / "test_admin_contract_api.db")
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


def _login(base, username, password):
    status, _, body, _ = _http(base + "/api/v1/auth/login", method="POST", payload={"username": username, "password": password})
    assert status == 200, body
    return body["token"]


def test_admin_users_list_shape():
    store, user, adapter = _bootstrap_admin()
    server, thread, base = _start_backend(adapter)
    try:
        token = _login(base, "admin", "correct horse battery staple")
        status, _, body, _ = _http(base + "/api/v1/admin/users", headers={"Authorization": f"Bearer {token}"})
        assert status == 200
        assert "users" in body
    finally:
        _stop_backend(server, thread)
    _retry_unlink(os.environ["EMS_DATABASE_PATH"])


def test_admin_roles_list_shape():
    store, user, adapter = _bootstrap_admin()
    server, thread, base = _start_backend(adapter)
    try:
        token = _login(base, "admin", "correct horse battery staple")
        status, _, body, _ = _http(base + "/api/v1/admin/roles", headers={"Authorization": f"Bearer {token}"})
        assert status == 200
        assert "roles" in body
    finally:
        _stop_backend(server, thread)
    _retry_unlink(os.environ["EMS_DATABASE_PATH"])


def test_admin_sessions_list_shape():
    store, user, adapter = _bootstrap_admin()
    server, thread, base = _start_backend(adapter)
    try:
        token = _login(base, "admin", "correct horse battery staple")
        status, _, body, _ = _http(base + "/api/v1/admin/sessions", headers={"Authorization": f"Bearer {token}"})
        assert status == 200
        assert "sessions" in body
    finally:
        _stop_backend(server, thread)
    _retry_unlink(os.environ["EMS_DATABASE_PATH"])


def test_admin_audit_list_shape():
    store, user, adapter = _bootstrap_admin()
    server, thread, base = _start_backend(adapter)
    try:
        token = _login(base, "admin", "correct horse battery staple")
        status, _, body, _ = _http(base + "/api/v1/admin/audit", headers={"Authorization": f"Bearer {token}"})
        assert status == 200
        assert "events" in body
    finally:
        _stop_backend(server, thread)
    _retry_unlink(os.environ["EMS_DATABASE_PATH"])


def test_admin_backup_shape():
    store, user, adapter = _bootstrap_admin()
    server, thread, base = _start_backend(adapter)
    try:
        token = _login(base, "admin", "correct horse battery staple")
        status, _, body, _ = _http(base + "/api/v1/admin/backup", method="POST", headers={"Authorization": f"Bearer {token}"})
        assert status == 200
        assert "db_path" in body and "sha256" in body
    finally:
        _stop_backend(server, thread)
    _retry_unlink(os.environ["EMS_DATABASE_PATH"])
