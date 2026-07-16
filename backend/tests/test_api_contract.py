from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request

from backend.app.api_contract import API_CONTRACT_SCHEMA, get_api_contract, validate_contract
from backend.app.http_server import create_backend_server


def _http_json(url: str):
    request = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            raw = response.read().decode("utf-8")
            return response.status, response.headers, json.loads(raw), raw
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8") if exc.fp else ""
        return exc.code, exc.headers, json.loads(raw), raw


def test_get_api_contract_returns_dict():
    contract = get_api_contract()
    assert isinstance(contract, dict)
    assert contract["service"] == "SSID-EMS"


def test_api_contract_has_required_endpoints():
    endpoints = API_CONTRACT_SCHEMA["endpoints"]
    assert "/health" in endpoints
    assert "/readiness" in endpoints
    assert "/version" in endpoints
    assert "/api/contract" in endpoints
    assert "/api/mvp/auth/login" in endpoints
    assert "/api/mvp/auth/session" in endpoints
    assert "/api/mvp/auth/logout" in endpoints


def test_api_contract_policies():
    policies = API_CONTRACT_SCHEMA["policies"]
    assert policies["no_auth_in_scaffold"] is False
    assert policies["auth_boundary"] == "safe-demo-auth-stub"
    assert policies["persistence"] == "in-memory-hash-only-stub"
    assert policies["external_services"] == "NOT_USED"
    assert policies["no_pii"] is True
    assert policies["no_secrets"] is True
    assert policies["start_services"] is False
    assert policies["backend_port"] == 8100
    assert policies["frontend_port"] == 3100


def test_validate_contract_valid():
    assert validate_contract(API_CONTRACT_SCHEMA) is True


def test_validate_contract_invalid_type():
    assert validate_contract("not a dict") is False


def test_validate_contract_missing_keys():
    assert validate_contract({"service": "x"}) is False


def test_validate_contract_bad_backend_port():
    bad = dict(API_CONTRACT_SCHEMA)
    bad["policies"] = dict(bad["policies"])
    bad["policies"]["backend_port"] = 8000
    assert validate_contract(bad) is False


def test_backend_http_server_contract_surface_roundtrip():
    server = create_backend_server("127.0.0.1", 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base_url = f"http://127.0.0.1:{server.server_address[1]}"
        health_status, health_headers, health_body, health_raw = _http_json(base_url + "/health")
        api_health_status, api_health_headers, api_health_body, api_health_raw = _http_json(base_url + "/api/mvp/health")
        api_alias_status, api_alias_headers, api_alias_body, api_alias_raw = _http_json(base_url + "/api/health")
        unknown_status, unknown_headers, unknown_body, unknown_raw = _http_json(base_url + "/does-not-exist")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert health_status == 200
    assert health_headers.get_content_type() == "application/json"
    assert health_body["status"] == "ok"
    assert health_body["service"] == "SSID-EMS"

    assert api_health_status == 200
    assert api_health_headers.get_content_type() == "application/json"
    assert api_health_body["status"] == "ok"
    assert api_health_body["service"] == "SSID-EMS"
    assert api_health_body["diagnostics"]["program_epic_02_ready"] is True
    assert api_health_body["persistence_decision"]["mode"] == "in-memory-hash-only-stub"
    assert api_health_body["persistence_decision"]["restart_safe"] is False
    assert api_health_body["persistence_boundary"] == "no_persistence"

    assert api_alias_status == 200
    assert api_alias_headers.get_content_type() == "application/json"
    assert api_alias_body["status"] == "ok"
    assert api_alias_body["service"] == "SSID-EMS"

    assert unknown_status == 404
    assert unknown_headers.get_content_type() == "application/json"
    assert unknown_body["status"] == "ERROR"
    assert unknown_body["error_code"] == "route_not_found"
    assert unknown_body["path"] == "/does-not-exist"
    assert "Traceback" not in unknown_raw
    assert "Traceback" not in health_raw
    assert "Traceback" not in api_health_raw
    assert "Traceback" not in api_alias_raw
