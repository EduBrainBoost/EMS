from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request

from backend.app.http_server import create_backend_server
from backend.app.runtime_http_adapter import LocalRuntimeAdapter


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


def test_no_persistence_boundary_is_explicit_and_restart_unsafed():
    adapter = LocalRuntimeAdapter()

    health = adapter.handle_request("GET", "/api/mvp/health")
    session_before = adapter.handle_request("GET", "/api/mvp/auth/session")
    login_ok = adapter.handle_request("POST", "/api/mvp/auth/login", json_body={"username": "demo", "password": "demo"})
    session_after = adapter.handle_request("GET", "/api/mvp/auth/session")
    logout_ok = adapter.handle_request("POST", "/api/mvp/auth/logout")
    login_invalid = adapter.handle_request("POST", "/api/mvp/auth/login", json_body={"username": "bad", "password": "creds"})

    decision = health["body"]["persistence_decision"]
    assert decision["mode"] == "in-memory-hash-only-stub"
    assert decision["restart_safe"] is False
    assert decision["stores_raw_pii"] is False
    assert decision["stores_secrets"] is False
    assert health["body"]["persistence_boundary"] == "no_persistence"

    assert session_before["body"]["authenticated"] is False
    assert session_before["body"]["persistence"] == "none"
    assert session_before["body"]["persistence_boundary"] == "no_persistence"
    assert login_ok["body"]["privacy_boundary"] == "no_real_credentials_no_persistence"
    assert login_ok["body"]["persistence_boundary"] == "no_persistence"
    assert session_after["body"]["authenticated"] is True
    assert session_after["body"]["persistence_boundary"] == "no_persistence"
    assert logout_ok["body"]["authenticated"] is False
    assert logout_ok["body"]["persistence_boundary"] == "no_persistence"
    assert login_invalid["body"]["error_code"] == "AUTH_INVALID_DEMO_CREDENTIALS"
    assert login_invalid["body"]["persistence_boundary"] == "no_persistence"


def test_no_persistence_boundary_survives_http_roundtrip_without_writing_state():
    adapter = LocalRuntimeAdapter()
    server = create_backend_server("127.0.0.1", 0, adapter)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base_url = f"http://127.0.0.1:{server.server_address[1]}"
        health_status, health_headers, health_body, health_raw = _http_json(base_url + "/api/mvp/health")
        login_status, login_headers, login_body, login_raw = _http_json(base_url + "/api/mvp/auth/login", "POST", {"username": "demo", "password": "demo"})
        session_status, session_headers, session_body, session_raw = _http_json(base_url + "/api/mvp/auth/session")
        logout_status, logout_headers, logout_body, logout_raw = _http_json(base_url + "/api/mvp/auth/logout", "POST")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert health_status == 200
    assert health_headers.get_content_type() == "application/json"
    assert health_body["persistence_boundary"] == "no_persistence"
    assert login_status == 200
    assert login_headers.get_content_type() == "application/json"
    assert login_body["persistence_boundary"] == "no_persistence"
    assert session_status == 200
    assert session_headers.get_content_type() == "application/json"
    assert session_body["persistence_boundary"] == "no_persistence"
    assert logout_status == 200
    assert logout_headers.get_content_type() == "application/json"
    assert logout_body["persistence_boundary"] == "no_persistence"

    for raw in (health_raw, login_raw, session_raw, logout_raw):
        assert "Traceback" not in raw
        assert "sqlite" not in raw.lower()
        assert "password" not in raw.lower()
