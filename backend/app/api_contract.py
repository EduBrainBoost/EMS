"""
SSID-EMS API Contract — Scaffold Phase
Defines the EMS surface area for health, readiness, version, contract introspection, and local demo auth.
Local demo auth only. No PII. No secrets.
"""

from backend.app.config import (
    EMS_BACKEND_PORT,
    EMS_FRONTEND_PORT,
    ENV_MODE,
    SERVICE_NAME,
    START_SERVICES,
    VERSION,
)


API_CONTRACT_SCHEMA: dict = {
    "service": SERVICE_NAME,
    "version": VERSION,
    "mode": ENV_MODE,
    "endpoints": {
        "/health": {
            "method": "GET",
            "description": "Liveness probe",
            "response_schema": {
                "type": "object",
                "properties": {
                    "service": {"type": "string"},
                    "status": {"type": "string", "enum": ["ok"]},
                    "started": {"type": "boolean"},
                    "mode": {"type": "string"},
                },
                "required": ["service", "status", "started", "mode"],
            },
        },
        "/readiness": {
            "method": "GET",
            "description": "Readiness probe",
            "response_schema": {
                "type": "object",
                "properties": {
                    "service": {"type": "string"},
                    "status": {"type": "string", "enum": ["not_ready"]},
                    "reason": {"type": "string"},
                    "started": {"type": "boolean"},
                    "mode": {"type": "string"},
                },
                "required": ["service", "status", "reason", "started", "mode"],
            },
        },
        "/version": {
            "method": "GET",
            "description": "Version information",
            "response_schema": {
                "type": "object",
                "properties": {
                    "service": {"type": "string"},
                    "version": {"type": "string"},
                    "mode": {"type": "string"},
                },
                "required": ["service", "version", "mode"],
            },
        },
        "/api/contract": {
            "method": "GET",
            "description": "Self-describing API contract",
            "response_schema": {
                "type": "object",
                "properties": {
                    "service": {"type": "string"},
                    "version": {"type": "string"},
                    "mode": {"type": "string"},
                    "endpoints": {"type": "object"},
                },
                "required": ["service", "version", "mode", "endpoints"],
            },
        },
        "/api/mvp/health": {
            "method": "GET",
            "description": "Local runtime health for Sprint 02 adapter path",
            "response_schema": {
                "type": "object",
                "properties": {
                    "service": {"type": "string"},
                    "status": {"type": "string", "enum": ["ok"]},
                    "runtime_id": {"type": "string"},
                    "external_services": {"type": "string", "enum": ["NOT_USED"]},
                    "persistence_decision": {"type": "object"},
                    "persistence_boundary": {"type": "string"},
                },
                "required": ["service", "status", "runtime_id", "external_services", "persistence_decision", "persistence_boundary"],
            },
        },
        "/api/mvp/demo": {
            "method": "GET",
            "description": "Deterministic SSID MVP demo fixture without external providers or PII",
            "response_schema": {
                "type": "object",
                "properties": {
                    "demo_id": {"type": "string"},
                    "request": {"type": "object"},
                    "api_response": {"type": "object"},
                    "ui_result": {"type": "object"},
                    "audit_evidence": {"type": "object"},
                    "privacy_boundary": {"type": "string"},
                },
                "required": ["demo_id", "request", "api_response", "ui_result", "audit_evidence", "privacy_boundary"],
            },
        },
        "/api/mvp/verify": {
            "method": "POST",
            "description": "Local deterministic MVP verification result for the demo request",
            "request_schema": {
                "type": "object",
                "required": ["request_id", "identity_profile_ref", "credential_ref", "verifier_ref", "nonce_hash"],
            },
            "response_schema": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["PASS", "FAIL", "INSUFFICIENT", "ERROR"]},
                    "api_response": {"type": "object"},
                    "ui_result": {"type": "object"},
                    "audit_evidence": {"type": "object"},
                    "product_audit_chain": {"type": "array"},
                    "privacy_boundary": {"type": "string"},
                },
                "required": ["status", "privacy_boundary"],
            },
        },
        "/api/mvp/auth/login": {
            "method": "POST",
            "description": "Local demo auth login for the MVP contract",
            "request_schema": {
                "type": "object",
                "required": ["username", "password"],
            },
            "response_schema": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["ok", "error"]},
                    "authenticated": {"type": "boolean"},
                    "session_mode": {"type": "string", "enum": ["local_demo"]},
                    "user_role": {"type": "string"},
                    "privacy_boundary": {"type": "string"},
                    "persistence_boundary": {"type": "string"},
                    "error_code": {"type": "string"},
                },
                "required": ["status", "authenticated", "persistence_boundary"],
            },
        },
        "/api/mvp/auth/session": {
            "method": "GET",
            "description": "Local demo auth session check",
            "response_schema": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["ok"]},
                    "authenticated": {"type": "boolean"},
                    "session_mode": {"type": "string", "enum": ["local_demo"]},
                    "persistence": {"type": "string", "enum": ["none"]},
                    "persistence_boundary": {"type": "string"},
                },
                "required": ["status", "authenticated", "session_mode", "persistence", "persistence_boundary"],
            },
        },
        "/api/mvp/auth/logout": {
            "method": "POST",
            "description": "Local demo auth logout",
            "response_schema": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["ok"]},
                    "authenticated": {"type": "boolean"},
                    "persistence_boundary": {"type": "string"},
                },
                "required": ["status", "authenticated", "persistence_boundary"],
            },
        },
    },
    "policies": {
        "no_auth_in_scaffold": False,
        "no_pii": True,
        "no_secrets": True,
        "start_services": START_SERVICES,
        "backend_port": EMS_BACKEND_PORT,
        "frontend_port": EMS_FRONTEND_PORT,
        "auth_boundary": "safe-demo-auth-stub",
        "persistence": "in-memory-hash-only-stub",
        "external_services": "NOT_USED",
    },
}


def get_api_contract() -> dict:
    """Returns the canonical API contract for this EMS build."""
    return API_CONTRACT_SCHEMA


def validate_contract(contract: dict) -> bool:
    """
    Validates that a given contract dict matches the required scaffold invariants.
    """
    if not isinstance(contract, dict):
        return False
    required_top = {"service", "version", "mode", "endpoints", "policies"}
    if not required_top.issubset(contract.keys()):
        return False
    policies = contract.get("policies", {})
    if policies.get("backend_port") not in (8100,):
        return False
    if policies.get("frontend_port") not in (3100,):
        return False
    if policies.get("no_secrets") is not True:
        return False
    endpoints = contract.get("endpoints", {})
    if "/api/mvp/health" not in endpoints or "/api/mvp/demo" not in endpoints or "/api/mvp/verify" not in endpoints:
        return False
    if endpoints["/api/mvp/verify"].get("method") != "POST":
        return False
    if "/api/mvp/auth/login" not in endpoints or "/api/mvp/auth/session" not in endpoints or "/api/mvp/auth/logout" not in endpoints:
        return False
    if endpoints["/api/mvp/auth/login"].get("method") != "POST":
        return False
    if endpoints["/api/mvp/auth/session"].get("method") != "GET":
        return False
    if endpoints["/api/mvp/auth/logout"].get("method") != "POST":
        return False
    if policies.get("external_services") != "NOT_USED":
        return False
    if policies.get("auth_boundary") != "safe-demo-auth-stub":
        return False
    if policies.get("no_pii") is not True:
        return False
    return True
