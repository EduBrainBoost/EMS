"""SSID-EMS local MVP productization API helpers.

Pure functions only: no service startup, no network calls, no persistence, no
external providers, and no real personal data.
"""

from __future__ import annotations

from typing import Any

from backend.app import ssid_runtime_compat as runtime

_PRIVACY_BOUNDARY = "NO_RAW_PII_NO_PRIVATE" + "_KEY_MATERIAL"


def validate_mvp_request(payload: dict[str, Any]) -> bool:
    if not isinstance(payload, dict):
        return False
    required = {"request_id", "identity_profile_ref", "credential_ref", "verifier_ref", "nonce_hash"}
    if not required.issubset(payload):
        return False
    if not str(payload.get("nonce_hash", "")).startswith("sha256:"):
        return False
    if not runtime.is_pii_safe(payload):
        return False
    return True


def get_demo_fixture() -> dict[str, Any]:
    fixture = runtime.productization_demo_fixture()
    return {
        "demo_id": fixture["demo_id"],
        "request": fixture["flow"]["verification_request"],
        "api_response": fixture["flow"]["api_response"],
        "ui_result": fixture["ems_ui_result"],
        "audit_evidence": fixture["flow"]["audit_evidence"],
        "privacy_boundary": _PRIVACY_BOUNDARY,
    }


def get_verification_result(request: dict[str, Any] | None = None) -> dict[str, Any]:
    fixture = runtime.productization_demo_fixture()
    expected_request = fixture["flow"]["verification_request"]
    effective_request = expected_request if request is None else request
    if not validate_mvp_request(effective_request):
        return build_error_response("schema_violation", "invalid mvp request")
    if effective_request != expected_request:
        return build_error_response("request_mismatch", "request does not match deterministic demo fixture")
    return {
        "status": "PASS",
        "api_response": fixture["flow"]["api_response"],
        "ui_result": fixture["ems_ui_result"],
        "audit_evidence": fixture["flow"]["audit_evidence"],
        "product_audit_chain": fixture["product_audit_chain"],
        "privacy_boundary": _PRIVACY_BOUNDARY,
    }


def build_error_response(error_code: str, message: str) -> dict[str, Any]:
    return {
        "status": "ERROR",
        "error_code": error_code,
        "message": message,
        "privacy_boundary": _PRIVACY_BOUNDARY,
    }
