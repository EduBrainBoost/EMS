from __future__ import annotations

from backend.app import runtime_http_adapter


def test_program_api_errors_include_stable_release_schema_and_correlation_id():
    adapter = runtime_http_adapter.LocalRuntimeAdapter()

    response = adapter.handle_request("POST", "/api/mvp/verify", raw_body="{broken")

    assert response["status_code"] == 400
    assert response["body"]["status"] == "ERROR"
    assert response["body"]["error_code"] == "invalid_json"
    assert response["body"]["audit_correlation_id"].startswith("ev")
    assert response["body"]["privacy_boundary"] == "NO_RAW_PII_NO_PRIVATE_KEY_MATERIAL"


def test_program_api_rejects_auth_bypass_and_production_like_auth():
    adapter = runtime_http_adapter.LocalRuntimeAdapter()
    demo = adapter.handle_request("GET", "/api/mvp/demo")["body"]

    no_auth = adapter.handle_request("POST", "/api/mvp/verify", json_body=demo["request"])
    production_auth = adapter.handle_request(
        "POST",
        "/api/mvp/verify",
        json_body=demo["request"],
        headers={"X-SSID-Production-Auth": "forbidden-production-token"},
    )
    bypass = adapter.handle_request(
        "POST",
        "/api/mvp/verify",
        json_body={**demo["request"], "auth_boundary": "bypass"},
        headers={"X-SSID-Demo-Auth": "demo-runtime-auth"},
    )

    assert no_auth["status_code"] == 403
    assert no_auth["body"]["error_code"] == "auth_required"
    assert production_auth["status_code"] == 403
    assert production_auth["body"]["error_code"] == "production_auth_not_allowed"
    assert bypass["status_code"] == 400
    assert bypass["body"]["error_code"] in {"request_mismatch", "auth_boundary_violation"}


def test_program_api_health_exposes_release_diagnostics_without_external_services():
    health = runtime_http_adapter.LocalRuntimeAdapter().handle_request("GET", "/api/mvp/health")

    assert health["status_code"] == 200
    assert health["body"]["diagnostics"]["runtime_mode"] == "local-release-candidate"
    assert health["body"]["diagnostics"]["external_services"] == "NOT_USED"
    assert health["body"]["diagnostics"].get("program_epic_02_ready") is True
