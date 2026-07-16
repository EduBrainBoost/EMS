from __future__ import annotations

from backend.app import runtime_http_adapter


def test_release_candidate_backend_rejects_oversized_payload_and_keeps_error_schema():
    adapter = runtime_http_adapter.LocalRuntimeAdapter()
    oversized = "{" + "\"x\":" + "\"" + ("a" * (runtime_http_adapter.MAX_REQUEST_BYTES + 1)) + "\"}"

    response = adapter.handle_request(
        "POST",
        "/api/mvp/verify",
        raw_body=oversized,
        headers={"X-SSID-Demo-Auth": "demo-runtime-auth"},
    )

    assert response["status_code"] == 413
    assert response["body"]["status"] == "ERROR"
    assert response["body"]["error_code"] == "payload_too_large"
    assert response["body"]["audit_correlation_id"] == response["body"]["runtime_audit_event"]["evidence_id"]


def test_release_candidate_backend_rejects_production_like_auth_call():
    adapter = runtime_http_adapter.LocalRuntimeAdapter()
    demo = adapter.handle_request("GET", "/api/mvp/demo")["body"]

    response = adapter.handle_request(
        "POST",
        "/api/mvp/verify",
        json_body=demo["request"],
        headers={"X-SSID-Production-Auth": "forbidden-production-token"},
    )

    assert response["status_code"] == 403
    assert response["body"]["status"] == "ERROR"
    assert response["body"]["error_code"] == "production_auth_not_allowed"
    assert response["body"]["audit_correlation_id"].startswith("evr_")


def test_release_candidate_health_contains_diagnostics_without_external_services():
    adapter = runtime_http_adapter.LocalRuntimeAdapter()

    health = adapter.handle_request("GET", "/api/mvp/health")

    assert health["status_code"] == 200
    assert health["body"]["diagnostics"]["runtime_mode"] == "local-release-candidate"
    assert health["body"]["diagnostics"]["external_services"] == "NOT_USED"
    assert health["body"]["diagnostics"]["logs_contain_pii"] is False
