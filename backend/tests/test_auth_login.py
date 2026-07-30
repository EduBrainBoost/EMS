from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request

from backend.app.http_server import create_backend_server


def _http_json(url: str, method: str = "GET", payload: dict | None = None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"} if payload is not None else {}
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=5) as response:  # nosec B310 - run-owned localhost test server
            raw = response.read().decode("utf-8")
            return response.status, response.headers, json.loads(raw), raw
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8") if exc.fp else ""
        return exc.code, exc.headers, json.loads(raw), raw


def test_auth_login_session_logout_demo_flow():
    server = create_backend_server("127.0.0.1", 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base_url = f"http://127.0.0.1:{server.server_address[1]}"

        session_before = _http_json(base_url + "/api/mvp/auth/session")
        login_ok = _http_json(base_url + "/api/mvp/auth/login", "POST", {"username": "demo", "password": "demo"})
        session_after = _http_json(base_url + "/api/mvp/auth/session")
        logout_ok = _http_json(base_url + "/api/mvp/auth/logout", "POST")
        bad_login = _http_json(base_url + "/api/mvp/auth/login", "POST", {"username": "wrong", "password": "creds"})
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert session_before[0] == 200
    assert session_before[1].get_content_type() == "application/json"
    assert session_before[2]["status"] == "ok"
    assert session_before[2]["authenticated"] is False
    assert session_before[2]["session_mode"] == "local_demo"
    assert session_before[2]["persistence"] == "none"
    assert session_before[2]["persistence_boundary"] == "no_persistence"

    assert login_ok[0] == 200
    assert login_ok[1].get_content_type() == "application/json"
    assert login_ok[2]["status"] == "ok"
    assert login_ok[2]["authenticated"] is True
    assert login_ok[2]["session_mode"] == "local_demo"
    assert login_ok[2]["user_role"] == "demo_user"
    assert login_ok[2]["privacy_boundary"] == "no_real_credentials_no_persistence"
    assert login_ok[2]["persistence_boundary"] == "no_persistence"

    assert session_after[0] == 200
    assert session_after[2]["authenticated"] is True
    assert session_after[2]["session_mode"] == "local_demo"
    assert session_after[2]["persistence"] == "none"
    assert session_after[2]["persistence_boundary"] == "no_persistence"

    assert logout_ok[0] == 200
    assert logout_ok[1].get_content_type() == "application/json"
    assert logout_ok[2]["status"] == "ok"
    assert logout_ok[2]["authenticated"] is False
    assert logout_ok[2]["persistence_boundary"] == "no_persistence"

    assert bad_login[0] == 401
    assert bad_login[1].get_content_type() == "application/json"
    assert bad_login[2]["status"] == "error"
    assert bad_login[2]["authenticated"] is False
    assert bad_login[2]["error_code"] == "AUTH_INVALID_DEMO_CREDENTIALS"
    assert bad_login[2]["persistence_boundary"] == "no_persistence"

    for raw in (session_before[3], login_ok[3], session_after[3], logout_ok[3], bad_login[3]):
        assert "Traceback" not in raw
