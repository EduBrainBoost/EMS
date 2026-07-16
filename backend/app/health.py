"""
SSID-EMS Health, Readiness, and Version Contracts
No service start. No external calls.
"""

from backend.app.config import (
    EMS_BACKEND_PORT,
    EMS_FRONTEND_PORT,
    ENV_MODE,
    SERVICE_NAME,
    START_SERVICES,
    VERSION,
)


def health_status() -> dict:
    """Basic liveness probe."""
    return {
        "service": SERVICE_NAME,
        "status": "ok",
        "started": START_SERVICES,
        "mode": ENV_MODE,
    }


def readiness_status() -> dict:
    """Readiness probe — always not_ready in scaffold because services are not started."""
    return {
        "service": SERVICE_NAME,
        "status": "not_ready",
        "reason": "local_scaffold_no_service_start",
        "started": START_SERVICES,
        "mode": ENV_MODE,
    }


def version_status() -> dict:
    """Version endpoint response."""
    return {
        "service": SERVICE_NAME,
        "version": VERSION,
        "mode": ENV_MODE,
    }


def full_status() -> dict:
    """Aggregated status for evidence and registry."""
    return {
        "service": SERVICE_NAME,
        "version": VERSION,
        "mode": ENV_MODE,
        "started": START_SERVICES,
        "backend_port": EMS_BACKEND_PORT,
        "frontend_port": EMS_FRONTEND_PORT,
        "health": health_status(),
        "readiness": readiness_status(),
    }
