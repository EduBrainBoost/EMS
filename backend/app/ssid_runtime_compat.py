"""Deterministic local SSID runtime compatibility layer for EMS.

This module keeps the EMS test and release-candidate runtime self-contained.
It reproduces the PII-minimized productization contracts used by EMS without
reading a sibling checkout, contacting external services, or persisting data.
Only Python's standard library is required.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from functools import lru_cache
from typing import Any

CONTRACT_VERSION = "1.0.0"
RUNTIME_ID = "runtime_20260709_productization_sprint_02"
RUNTIME_AUTH_STUB = "demo-runtime-auth"
PRIVACY_BOUNDARY = "NO_RAW_PII_NO_PRIVATE" + "_KEY_MATERIAL"
ZERO_HASH_REF = "sha256:" + "0" * 64
PRODUCT_DEMO_ID = "demo_20260709_productization_sprint_01"
RUNTIME_DEMO_ID = "demo_20260709_productization_sprint_02_runtime"
RUNTIME_TIMESTAMP_BASE = "2026-07-09T11:19"

PUBLIC_DEMO_ENDPOINTS = ["GET /api/mvp/health", "GET /api/mvp/demo"]
PROTECTED_ENDPOINTS = ["POST /api/mvp/verify"]
RUNTIME_EVENT_TYPES = (
    "RUNTIME_HEALTH_CHECKED",
    "RUNTIME_DEMO_PAYLOAD_EMITTED",
    "RUNTIME_VERIFY_REQUEST_ACCEPTED",
    "RUNTIME_AUTH_BOUNDARY_CHECKED",
    "RUNTIME_PERSISTENCE_STUB_WRITTEN",
    "RUNTIME_VERIFY_RESPONSE_EMITTED",
)
PRODUCT_FLOW_EVENT_TYPES = (
    "MVP_IDENTITY_PROFILE_VALIDATED",
    "MVP_CREDENTIAL_IMPORTED",
    "MVP_VERIFICATION_REQUEST_CREATED",
    "MVP_VERIFICATION_RESULT_RECORDED",
    "MVP_API_RESPONSE_EMITTED",
    "MVP_UI_RESULT_RENDERED",
)

_FORBIDDEN_FIELDS = frozenset(
    {
        "name",
        "email",
        "phone",
        "address",
        "dateofbirth",
        "date_of_birth",
        "birthdate",
        "ssn",
        "private" + "_key",
        "privatekey",
        "d",
        "seed",
        "mnemonic",
        "secret",
        "token",
        "password",
        "credential_secret",
    }
)
_SENSITIVE_VALUE_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE" + r" KEY-----"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
)


class RuntimeValidationError(ValueError):
    """Fail-closed compatibility runtime error."""


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def sha256_ref(payload: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def _walk(value: Any):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key, child
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def is_pii_safe(payload: Any) -> bool:
    for key, value in _walk(payload):
        if str(key).lower() in _FORBIDDEN_FIELDS:
            return False
        if isinstance(value, str) and any(pattern.search(value) for pattern in _SENSITIVE_VALUE_PATTERNS):
            return False
    return True


def _safe_copy(payload: Any) -> Any:
    return copy.deepcopy(payload)


def _assert_pii_safe(payload: Any, error_code: str = "raw_pii_or_sensitive_material_not_allowed") -> None:
    if not is_pii_safe(payload):
        raise RuntimeValidationError(error_code)


def _public_key_fingerprint() -> str:
    jwk = {
        "kty": "EC",
        "crv": "P-256",
        "x": "Wf2EXAMPLEPublicCoordinateXNoPII000000000001",
        "y": "C2EXAMPLEPublicCoordinateYNoPII000000000002",
    }
    return hashlib.sha256(canonical_json(jwk).encode("utf-8")).hexdigest()


def _product_flow() -> dict[str, Any]:
    fingerprint = _public_key_fingerprint()
    did = f"did:key:z{fingerprint}"
    identity_profile = {
        "schema_version": CONTRACT_VERSION,
        "identity_profile_id": "ipid_20260709_productization_01",
        "did": did,
        "holder_ref": f"urn:ssid:holder:{fingerprint}",
        "public_key_fingerprint": fingerprint,
        "did_method": "did:key",
        "created_at_utc": "2026-07-09T08:52:44Z",
        "assurance_level": "MVP_PUBLIC_KEY_CONTROL",
        "privacy_boundary": PRIVACY_BOUNDARY,
    }
    did_document = {
        "@context": ["https://www.w3.org/ns/did/v1", "https://w3id.org/security/suites/jws-2020/v1"],
        "id": did,
        "verificationMethod": [
            {
                "id": f"{did}#key-1",
                "type": "JsonWebKey2020",
                "controller": did,
                "publicKeyJwk": {
                    "kty": "EC",
                    "crv": "P-256",
                    "x": "Wf2EXAMPLEPublicCoordinateXNoPII000000000001",
                    "y": "C2EXAMPLEPublicCoordinateYNoPII000000000002",
                },
            }
        ],
        "authentication": [f"{did}#key-1"],
        "assertionMethod": [f"{did}#key-1"],
    }
    credential = {
        "schema_version": CONTRACT_VERSION,
        "credential_id": "cred_20260709_productization_01",
        "type": "SSIDProofCredential",
        "issuer_did": "did:key:zday01issuer111111111111111111111111111111",
        "subject_did": did,
        "claims_commitment_hash": "sha256:" + "2" * 64,
        "proof_hash": "sha256:" + "3" * 64,
        "issued_at_utc": "2026-07-09T08:52:44Z",
        "expires_at_utc": "2026-08-09T06:31:15Z",
        "status": "ACTIVE",
        "storage_mode": "HASH_ONLY",
    }
    request = {
        "schema_version": CONTRACT_VERSION,
        "request_id": "vreq_20260709_productization_01",
        "identity_profile_ref": identity_profile["identity_profile_id"],
        "credential_ref": credential["credential_id"],
        "verifier_ref": "urn:ssid:verifier:day01-mvp",
        "requested_purpose": "ssid-mvp-verification",
        "nonce_hash": "sha256:" + hashlib.sha256(b"day01-mvp-verification").hexdigest(),
        "created_at_utc": "2026-07-09T08:52:44Z",
    }
    transcript = {
        "identity_profile": identity_profile,
        "credential_or_proof": credential,
        "verification_request": request,
    }
    verification_result = {
        "schema_version": CONTRACT_VERSION,
        "result_id": "vres_20260709_productization_01",
        "request_ref": request["request_id"],
        "identity_profile_ref": identity_profile["identity_profile_id"],
        "credential_ref": credential["credential_id"],
        "status": "VALID",
        "checked_at_utc": "2026-07-09T08:52:45Z",
        "verification_method": "holder-signature-hash-proof",
        "evidence_hash": sha256_ref(transcript),
        "audit_evidence_ref": "ev_20260709_productization_01",
        "metadata": {"privacy_boundary": PRIVACY_BOUNDARY},
    }
    audit_base = {
        "schema_version": CONTRACT_VERSION,
        "evidence_id": "ev_20260709_productization_01",
        "event_type": "MVP_VERIFICATION_RESULT_RECORDED",
        "verification_result_ref": verification_result["result_id"],
        "previous_evidence_hash": ZERO_HASH_REF,
        "payload_hash": verification_result["evidence_hash"],
        "record_hash": ZERO_HASH_REF,
        "created_at_utc": "2026-07-09T06:31:17Z",
        "retention_class": "MVP_AUDIT_MINIMAL_HASH_ONLY",
    }
    audit_evidence = _safe_copy(audit_base)
    audit_evidence["record_hash"] = sha256_ref(audit_base)
    api_response = {
        "schema_version": CONTRACT_VERSION,
        "response_id": "api_20260709_productization_01",
        "generated_at_utc": "2026-07-09T06:31:18Z",
        "verification_result": verification_result,
        "links": {"audit_evidence_ref": audit_evidence["evidence_id"]},
        "privacy_boundary": PRIVACY_BOUNDARY,
    }
    flow = {
        "identity_profile": identity_profile,
        "did_document": did_document,
        "credential_or_proof": credential,
        "verification_request": request,
        "verification_result": verification_result,
        "audit_evidence": audit_evidence,
        "audit_chain": [_safe_copy(audit_evidence)],
        "api_response": api_response,
    }
    _assert_pii_safe(flow)
    return flow


def _ui_result(flow: dict[str, Any]) -> dict[str, Any]:
    result = flow["verification_result"]
    evidence = flow["audit_evidence"]
    model = {
        "component": "SSIDMVPVerificationResult",
        "schema_version": CONTRACT_VERSION,
        "status_label": "PASS" if result["status"] == "VALID" else "FAIL",
        "result_id": result["result_id"],
        "request_ref": result["request_ref"],
        "identity_profile_ref": result["identity_profile_ref"],
        "credential_ref": result["credential_ref"],
        "verification_method": result["verification_method"],
        "audit_evidence_ref": evidence["evidence_id"],
        "evidence_hash": result["evidence_hash"],
        "record_hash": evidence["record_hash"],
        "checked_at_utc": result["checked_at_utc"],
        "privacy_boundary": PRIVACY_BOUNDARY,
        "display_fields": [
            "status_label",
            "result_id",
            "verification_method",
            "audit_evidence_ref",
            "checked_at_utc",
        ],
    }
    _assert_pii_safe(model)
    return model


def _product_audit_event(
    event_type: str,
    payload: dict[str, Any],
    *,
    evidence_id: str,
    previous_evidence_hash: str,
    created_at_utc: str,
) -> dict[str, Any]:
    base = {
        "schema_version": CONTRACT_VERSION,
        "evidence_id": evidence_id,
        "event_type": event_type,
        "verification_result_ref": payload.get("verification_result_ref", "vres_20260709_productization_01"),
        "previous_evidence_hash": previous_evidence_hash,
        "payload_hash": sha256_ref(payload),
        "record_hash": ZERO_HASH_REF,
        "created_at_utc": created_at_utc,
        "retention_class": "MVP_AUDIT_MINIMAL_HASH_ONLY",
    }
    event = _safe_copy(base)
    event["record_hash"] = sha256_ref(base)
    _assert_pii_safe(event)
    return event


def _product_audit_chain(flow: dict[str, Any], ui_model: dict[str, Any]) -> list[dict[str, Any]]:
    payloads = [
        {"identity_profile_ref": flow["identity_profile"]["identity_profile_id"], "did": flow["identity_profile"]["did"]},
        {"credential_ref": flow["credential_or_proof"]["credential_id"], "subject_did": flow["credential_or_proof"]["subject_did"]},
        {"request_ref": flow["verification_request"]["request_id"], "credential_ref": flow["verification_request"]["credential_ref"]},
        {"verification_result_ref": flow["verification_result"]["result_id"], "status": flow["verification_result"]["status"]},
        {"response_ref": flow["api_response"]["response_id"], "verification_result_ref": flow["verification_result"]["result_id"]},
        {"component": ui_model["component"], "audit_evidence_ref": ui_model["audit_evidence_ref"]},
    ]
    chain: list[dict[str, Any]] = []
    previous = ZERO_HASH_REF
    for index, (event_type, payload) in enumerate(zip(PRODUCT_FLOW_EVENT_TYPES, payloads), start=1):
        event = _product_audit_event(
            event_type,
            payload,
            evidence_id=f"evp_20260709_productization_{index:02d}",
            previous_evidence_hash=previous,
            created_at_utc=f"2026-07-09T08:52:{45 + index:02d}Z",
        )
        chain.append(event)
        previous = event["record_hash"]
    return chain


@lru_cache(maxsize=1)
def _productization_fixture_json() -> str:
    flow = _product_flow()
    ui_model = _ui_result(flow)
    audit_chain = _product_audit_chain(flow, ui_model)
    fixture = {
        "demo_id": PRODUCT_DEMO_ID,
        "schema_version": CONTRACT_VERSION,
        "flow": flow,
        "product_audit_chain": audit_chain,
        "ems_api_result": {
            "status": "PASS",
            "result_id": flow["verification_result"]["result_id"],
            "api_response": flow["api_response"],
            "audit_evidence": flow["audit_evidence"],
            "product_audit_chain_ref": audit_chain[-1]["evidence_id"],
            "privacy_boundary": PRIVACY_BOUNDARY,
        },
        "ems_ui_result": ui_model,
    }
    _assert_pii_safe(fixture)
    return canonical_json(fixture)


def productization_demo_fixture() -> dict[str, Any]:
    return json.loads(_productization_fixture_json())


def auth_boundary_contract() -> dict[str, Any]:
    return {
        "mode": "safe-demo-auth-stub",
        "public_demo_endpoints": list(PUBLIC_DEMO_ENDPOINTS),
        "protected_endpoints": list(PROTECTED_ENDPOINTS),
        "auth_header": "X-SSID-Demo-Auth",
        "accepted_stub_context": RUNTIME_AUTH_STUB,
        "no_real_user_management": True,
        "no_secrets": True,
        "fail_closed": True,
        "sprint_03_follow_up": "replace safe demo stub with real AuthN/AuthZ design after product boundary approval",
    }


def persistence_decision() -> dict[str, Any]:
    return {
        "mode": "in-memory-hash-only-stub",
        "decision": "no real database or restart-safe persistence in Sprint 02",
        "restart_safe": False,
        "stores_raw_pii": False,
        "stores_secrets": False,
        "allowed_payloads": ["audit evidence ids", "sha256 hashes", "deterministic runtime event metadata"],
        "future_storage": "DECISION_NEEDED for Sprint 03 after AuthN/AuthZ and data minimization review",
    }


class SafePersistenceStub:
    """Hash-only in-memory evidence stub."""

    def __init__(self) -> None:
        self._records: list[dict[str, Any]] = []

    def decision(self) -> dict[str, Any]:
        return persistence_decision()

    def store_audit_event(self, event: dict[str, Any]) -> dict[str, Any]:
        _assert_pii_safe(event)
        record = {
            "status": "STORED_IN_MEMORY_ONLY",
            "evidence_id": event["evidence_id"],
            "event_type": event["event_type"],
            "record_hash": event["record_hash"],
            "payload_hash": event["payload_hash"],
            "restart_safe": False,
        }
        self._records.append(record)
        return _safe_copy(record)

    def export_state(self) -> dict[str, Any]:
        return {"decision": self.decision(), "records": _safe_copy(self._records)}


def runtime_audit_event(
    event_type: str,
    payload: dict[str, Any],
    *,
    evidence_id: str,
    previous_evidence_hash: str,
    created_at_utc: str,
) -> dict[str, Any]:
    if event_type not in (*RUNTIME_EVENT_TYPES, "RUNTIME_ERROR_RECORDED"):
        raise RuntimeValidationError("unknown_runtime_audit_event")
    _assert_pii_safe(payload)
    base = {
        "schema_version": CONTRACT_VERSION,
        "evidence_id": evidence_id,
        "event_type": event_type,
        "runtime_id": RUNTIME_ID,
        "previous_evidence_hash": previous_evidence_hash,
        "payload_hash": sha256_ref(payload),
        "record_hash": ZERO_HASH_REF,
        "created_at_utc": created_at_utc,
        "retention_class": "RUNTIME_AUDIT_MINIMAL_HASH_ONLY",
    }
    event = _safe_copy(base)
    event["record_hash"] = sha256_ref(base)
    _assert_pii_safe(event)
    return event


def _runtime_request(product_fixture: dict[str, Any]) -> dict[str, Any]:
    request = _safe_copy(product_fixture["flow"]["verification_request"])
    request["runtime_id"] = RUNTIME_ID
    request["auth_boundary"] = "safe-demo-auth-stub-required-for-verify"
    return request


def validate_runtime_request(request: dict[str, Any]) -> bool:
    required = {
        "request_id",
        "identity_profile_ref",
        "credential_ref",
        "verifier_ref",
        "nonce_hash",
        "runtime_id",
        "auth_boundary",
    }
    if not isinstance(request, dict) or not required.issubset(request):
        return False
    if request.get("runtime_id") != RUNTIME_ID:
        return False
    if request.get("auth_boundary") != "safe-demo-auth-stub-required-for-verify":
        return False
    if not str(request.get("nonce_hash", "")).startswith("sha256:"):
        return False
    return is_pii_safe(request)


def _runtime_audit_chain(product_fixture: dict[str, Any], request: dict[str, Any]) -> list[dict[str, Any]]:
    payloads = [
        {"runtime_id": RUNTIME_ID, "status": "ok"},
        {"demo_id": product_fixture["demo_id"], "request_ref": request["request_id"]},
        {"request_ref": request["request_id"], "credential_ref": request["credential_ref"]},
        {"route": "POST /api/mvp/verify", "auth_mode": "safe-demo-auth-stub"},
        {"mode": persistence_decision()["mode"], "restart_safe": False},
        {"result_ref": product_fixture["flow"]["verification_result"]["result_id"], "status": "PASS"},
    ]
    chain: list[dict[str, Any]] = []
    previous = ZERO_HASH_REF
    for index, (event_type, payload) in enumerate(zip(RUNTIME_EVENT_TYPES, payloads), start=1):
        event = runtime_audit_event(
            event_type,
            payload,
            evidence_id=f"evr_20260709_runtime_{index:02d}",
            previous_evidence_hash=previous,
            created_at_utc=f"{RUNTIME_TIMESTAMP_BASE}:{39 + index:02d}Z",
        )
        chain.append(event)
        previous = event["record_hash"]
    return chain


@lru_cache(maxsize=1)
def _runtime_fixture_json() -> str:
    product_fixture = productization_demo_fixture()
    request = _runtime_request(product_fixture)
    chain = _runtime_audit_chain(product_fixture, request)
    fixture = {
        "runtime_id": RUNTIME_ID,
        "demo_id": RUNTIME_DEMO_ID,
        "status": "PASS",
        "request": request,
        "api_response": {
            "status": "PASS",
            "verification_result": product_fixture["flow"]["verification_result"],
            "response": product_fixture["flow"]["api_response"],
        },
        "ui_result": product_fixture["ems_ui_result"],
        "audit_evidence": product_fixture["flow"]["audit_evidence"],
        "audit_evidence_id": product_fixture["flow"]["audit_evidence"]["evidence_id"],
        "runtime_audit_chain": chain,
        "auth_boundary": auth_boundary_contract(),
        "persistence_decision": persistence_decision(),
        "privacy_boundary": PRIVACY_BOUNDARY,
    }
    _assert_pii_safe(fixture)
    return canonical_json(fixture)


def runtime_demo_fixture() -> dict[str, Any]:
    return json.loads(_runtime_fixture_json())


def _runtime_error(error_code: str, message: str, *, route: str = "POST /api/mvp/verify") -> dict[str, Any]:
    event = runtime_audit_event(
        "RUNTIME_ERROR_RECORDED",
        {"error_code": error_code, "route": route},
        evidence_id=f"evr_20260709_runtime_error_{hashlib.sha256(error_code.encode()).hexdigest()[:8]}",
        previous_evidence_hash=ZERO_HASH_REF,
        created_at_utc=f"{RUNTIME_TIMESTAMP_BASE}:59Z",
    )
    return {
        "status": "ERROR",
        "error_code": error_code,
        "message": message,
        "runtime_audit_event": event,
        "privacy_boundary": PRIVACY_BOUNDARY,
    }


def verify_runtime_request(
    request: dict[str, Any] | None,
    *,
    auth_context: str | None,
    persistence: SafePersistenceStub | None = None,
) -> dict[str, Any]:
    if auth_context != RUNTIME_AUTH_STUB:
        return _runtime_error("auth_required", "verification requires safe demo auth stub")
    demo = runtime_demo_fixture()
    if not validate_runtime_request(request or {}):
        return _runtime_error("schema_violation", "invalid runtime verification request")
    if request != demo["request"]:
        return _runtime_error("request_mismatch", "request does not match deterministic runtime fixture")
    stub = persistence or SafePersistenceStub()
    stored = [stub.store_audit_event(event) for event in demo["runtime_audit_chain"]]
    result = {
        "status": "PASS",
        "runtime_id": RUNTIME_ID,
        "api_response": demo["api_response"],
        "ui_result": demo["ui_result"],
        "audit_evidence": demo["audit_evidence"],
        "audit_evidence_id": demo["audit_evidence_id"],
        "runtime_audit_chain": demo["runtime_audit_chain"],
        "persistence_records": stored,
        "persistence_decision": stub.decision(),
        "privacy_boundary": PRIVACY_BOUNDARY,
    }
    _assert_pii_safe(result)
    return result
