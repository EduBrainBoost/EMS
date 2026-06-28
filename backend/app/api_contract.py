"""
EMS API Contract — Rebuild Phase
Defines the EMS surface area for health, readiness, version, and contract introspection.
No auth. No PII. No secrets.
"""

from backend.app.config import (
    EMS_BACKEND_PORT,
    EMS_FRONTEND_PORT,
    MODE,
    SERVICE_NAME,
    START_SERVICES,
    VERSION,
)

API_CONTRACT_SCHEMA: dict = {
    "service": SERVICE_NAME,
    "version": VERSION,
    "mode": MODE,
    "endpoints": {
        "/health": {
            "method": "GET",
            "description": "Liveness probe",
            "response_schema": {
                "type": "object",
                "properties": {
                    "service": {"type": "string"},
                    "status": {"type": "string", "enum": ["not_started"]},
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
    },
    "policies": {
        "no_auth_in_scaffold": True,
        "no_pii": True,
        "no_secrets": True,
        "no_provider_calls": True,
        "no_service_start": START_SERVICES is False,
        "backend_port": EMS_BACKEND_PORT,
        "frontend_port": EMS_FRONTEND_PORT,
    },
}


def get_api_contract() -> dict:
    return API_CONTRACT_SCHEMA


def validate_contract(contract: dict) -> bool:
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
    return True
