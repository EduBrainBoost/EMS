"""
EMS Application Factory — Rebuild Phase
NO uvicorn execution. NO entrypoint guard block. NO service start.
"""

from backend.app.api_contract import get_api_contract
from backend.app.config import EMS_BACKEND_PORT, EMS_FRONTEND_PORT, MODE, START_SERVICES, VERSION
from backend.app.health import full_status, health_status, readiness_status, version_status


def create_app() -> dict:
    """
    Returns the EMS application descriptor.
    In a real framework setup this would return the app instance.
    In rebuild phase it returns a safe descriptor dict.
    """
    return {
        "service": "EMS",
        "version": VERSION,
        "mode": MODE,
        "started": START_SERVICES,
        "backend_port": EMS_BACKEND_PORT,
        "frontend_port": EMS_FRONTEND_PORT,
        "routes": {
            "/health": health_status,
            "/readiness": readiness_status,
            "/version": version_status,
            "/api/contract": get_api_contract,
            "/status": full_status,
        },
    }
