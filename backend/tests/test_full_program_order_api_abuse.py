from __future__ import annotations

from backend.app import runtime_http_adapter


def test_pre_release_api_abuse_cases_are_rejected_consistently():
    adapter = runtime_http_adapter.LocalRuntimeAdapter()
    demo = adapter.handle_request("GET", "/api/mvp/demo")["body"]

    cases = {
        "empty_body": adapter.handle_request("POST", "/api/mvp/verify", raw_body="", headers={"Content-Type": "application/json", "X-SSID-Demo-Auth": "demo-runtime-auth"}),
        "wrong_method": adapter.handle_request("GET", "/api/mvp/verify"),
        "wrong_content_type": adapter.handle_request("POST", "/api/mvp/verify", raw_body="{}", headers={"Content-Type": "text/plain", "X-SSID-Demo-Auth": "demo-runtime-auth"}),
        "huge_nested_object": adapter.handle_request("POST", "/api/mvp/verify", raw_body='{"a":' * 3000 + '0' + '}' * 3000, headers={"Content-Type": "application/json", "X-SSID-Demo-Auth": "demo-runtime-auth"}),
        "unknown_fields": adapter.handle_request("POST", "/api/mvp/verify", json_body={**demo["request"], "unexpected": "field"}, headers={"Content-Type": "application/json", "X-SSID-Demo-Auth": "demo-runtime-auth"}),
        "unsupported_version": adapter.handle_request("POST", "/api/mvp/verify", json_body={**demo["request"], "contract_version": "999.0"}, headers={"Content-Type": "application/json", "X-SSID-Demo-Auth": "demo-runtime-auth"}),
        "invalid_status_injection": adapter.handle_request("POST", "/api/mvp/verify", json_body={**demo["request"], "status": "OWNED"}, headers={"Content-Type": "application/json", "X-SSID-Demo-Auth": "demo-runtime-auth"}),
        "fake_token": adapter.handle_request("POST", "/api/mvp/verify", json_body=demo["request"], headers={"Content-Type": "application/json", "X-SSID-Demo-Auth": "fake-token"}),
    }

    assert cases["empty_body"]["status_code"] == 400
    assert cases["wrong_method"]["status_code"] == 405
    assert cases["wrong_content_type"]["status_code"] == 415
    assert cases["huge_nested_object"]["status_code"] in {400, 413}
    assert cases["unknown_fields"]["body"]["error_code"] == "unknown_fields_rejected"
    assert cases["unsupported_version"]["body"]["error_code"] == "unsupported_version"
    assert cases["invalid_status_injection"]["body"]["error_code"] == "invalid_status_injection"
    assert cases["fake_token"]["status_code"] == 403
    for response in cases.values():
        assert response["body"]["status"] == "ERROR"
        assert response["body"]["audit_correlation_id"]
        assert response["body"]["privacy_boundary"] == "NO_RAW_PII_NO_PRIVATE_KEY_MATERIAL"
