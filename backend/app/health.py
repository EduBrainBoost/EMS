"""
EMS Health, Readiness, and Version Contracts
No service start. No external calls.
"""

from backend.app.config import (
    EMS_BACKEND_PORT,
    EMS_FRONTEND_PORT,
    MODE,
    SERVICE_NAME,
    START_SERVICES,
    VERSION,
)


def health_status() -> dict:
    return {
        "service": SERVICE_NAME,
        "status": "not_started",
        "started": START_SERVICES,
        "mode": MODE,
    }


def readiness_status() -> dict:
    return {
        "service": SERVICE_NAME,
        "status": "not_ready",
        "reason": "local_rebuild_no_service_start",
        "started": START_SERVICES,
        "mode": MODE,
    }


def version_status() -> dict:
    return {
        "service": SERVICE_NAME,
        "version": VERSION,
        "mode": MODE,
    }


def full_status() -> dict:
    return {
        "service": SERVICE_NAME,
        "version": VERSION,
        "mode": MODE,
        "started": START_SERVICES,
        "backend_port": EMS_BACKEND_PORT,
        "frontend_port": EMS_FRONTEND_PORT,
        "health": health_status(),
        "readiness": readiness_status(),
    }
