from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request

from backend.app.http_server import create_backend_server
from backend.app.runtime_http_adapter import LocalRuntimeAdapter
from frontend.server import create_frontend_server


def _request(url: str, method: str = "GET", payload: dict | None = None, headers: dict | None = None):
    data = None if payload is None else json.dumps(payload).encode()
    request = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, response.headers, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.headers, exc.read()


def _run(server, callback):
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        return callback(f"http://127.0.0.1:{server.server_address[1]}")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def _assert_security_headers(headers):
    assert headers["Content-Security-Policy"].startswith("default-src 'self'")
    assert "object-src 'none'" in headers["Content-Security-Policy"]
    assert "unsafe-eval" not in headers["Content-Security-Policy"]
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["Referrer-Policy"] == "no-referrer"
    assert headers["Permissions-Policy"] == "camera=(), microphone=(), geolocation=()"
    assert headers["Cross-Origin-Opener-Policy"] == "same-origin"
    assert headers["Cross-Origin-Resource-Policy"] == "same-origin"
    assert headers["X-Frame-Options"] == "DENY"
    assert headers["Cache-Control"] == "no-store"
    assert "Server" not in headers or headers["Server"] == ""


def test_backend_public_error_and_api_headers():
    server = create_backend_server("127.0.0.1", 0, adapter=LocalRuntimeAdapter())
    def check(base):
        status, headers, _ = _request(base + "/health")
        assert status == 200
        _assert_security_headers(headers)
        status, headers, _ = _request(base + "/api/unknown")
        assert status == 404
        _assert_security_headers(headers)
    _run(server, check)


def test_frontend_html_and_error_headers():
    server = create_frontend_server("127.0.0.1", 0)
    def check(base):
        status, headers, body = _request(base + "/")
        assert status == 200
        assert b"SSID-EMS" in body
        _assert_security_headers(headers)
        status, headers, _ = _request(base + "/missing")
        assert status == 404
        _assert_security_headers(headers)
    _run(server, check)


def test_demo_cookie_flags_and_logout_deletion():
    adapter = LocalRuntimeAdapter()
    login = adapter.handle_request("POST", "/api/mvp/auth/login", json_body={"username": "demo", "password": "demo"})
    cookie = login["headers"]["Set-Cookie"]
    assert "HttpOnly" in cookie
    assert "SameSite=Lax" in cookie
    assert "Path=/" in cookie
    assert "Max-Age=3600" in cookie
    token = cookie.split("=", 1)[1].split(";", 1)[0]
    logout = adapter.handle_request("POST", "/api/mvp/auth/logout", headers={"Cookie": f"ssid_ems_session={token}"})
    assert logout["headers"]["Set-Cookie"].endswith("Max-Age=0")
    assert "HttpOnly" in logout["headers"]["Set-Cookie"]
    assert "SameSite=Lax" in logout["headers"]["Set-Cookie"]
