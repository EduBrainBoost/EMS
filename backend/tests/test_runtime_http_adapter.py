from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request

from backend.app import runtime_http_adapter


def http_json(url: str, method: str = "GET", payload: dict | None = None, auth: str | None = None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if auth:
        headers["X-SSID-Demo-Auth"] = auth
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def test_runtime_adapter_handles_health_demo_and_verify_without_external_services():
    adapter = runtime_http_adapter.LocalRuntimeAdapter()

    health = adapter.handle_request("GET", "/api/mvp/health")
    demo = adapter.handle_request("GET", "/api/mvp/demo")
    verify = adapter.handle_request(
        "POST",
        "/api/mvp/verify",
        json_body=demo["body"]["request"],
        headers={"X-SSID-Demo-Auth": "demo-runtime-auth"},
    )

    assert health["status_code"] == 200
    assert health["body"]["status"] == "ok"
    assert demo["status_code"] == 200
    assert verify["status_code"] == 200
    assert verify["body"]["status"] == "PASS"
    assert verify["body"]["audit_evidence_id"] == verify["body"]["audit_evidence"]["evidence_id"]
    assert adapter.persistence.decision()["restart_safe"] is False


def test_runtime_adapter_rejects_negative_runtime_cases_fail_closed():
    adapter = runtime_http_adapter.LocalRuntimeAdapter()
    demo = adapter.handle_request("GET", "/api/mvp/demo")["body"]

    cases = [
        adapter.handle_request("POST", "/api/mvp/demo", json_body={}),
        adapter.handle_request("POST", "/api/mvp/verify", json_body=demo["request"]),
        adapter.handle_request("POST", "/api/mvp/verify", json_body={"request_id": "bad"}, headers={"X-SSID-Demo-Auth": "demo-runtime-auth"}),
        adapter.handle_request("POST", "/api/mvp/verify", raw_body="{not-json", headers={"X-SSID-Demo-Auth": "demo-runtime-auth"}),
        adapter.handle_request("POST", "/api/mvp/verify", json_body={**demo["request"], "email": "blocked.invalid"}, headers={"X-SSID-Demo-Auth": "demo-runtime-auth"}),
    ]

    assert [case["body"]["status"] for case in cases] == ["ERROR", "ERROR", "ERROR", "ERROR", "ERROR"]
    assert all(case["body"]["runtime_audit_event"]["event_type"] == "RUNTIME_ERROR_RECORDED" for case in cases)


def test_runtime_http_server_roundtrip_uses_localhost_only_and_returns_json():
    adapter = runtime_http_adapter.LocalRuntimeAdapter()
    server = runtime_http_adapter.create_runtime_server("127.0.0.1", 0, adapter)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base = f"http://127.0.0.1:{server.server_address[1]}"
        health_status, health = http_json(base + "/api/mvp/health")
        demo_status, demo = http_json(base + "/api/mvp/demo")
        verify_status, verify = http_json(
            base + "/api/mvp/verify",
            method="POST",
            payload=demo["request"],
            auth="demo-runtime-auth",
        )
        denied_status, denied = http_json(base + "/api/mvp/verify", method="POST", payload=demo["request"])
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert health_status == 200
    assert health["status"] == "ok"
    assert demo_status == 200
    assert verify_status == 200
    assert verify["status"] == "PASS"
    assert denied_status == 403
    assert denied["error_code"] == "auth_required"
