"""
SSID-EMS Application Factory — Scaffold Phase
NO uvicorn execution. NO entrypoint guard block. NO service start.
"""

from backend.app.api_contract import get_api_contract
from backend.app.config import EMS_BACKEND_PORT, EMS_FRONTEND_PORT, ENV_MODE, START_SERVICES, VERSION
from backend.app.health import full_status, health_status, readiness_status, version_status
from backend.app.mvp_productization import get_demo_fixture, get_verification_result
from backend.app.runtime_http_adapter import get_runtime_demo, get_runtime_health, post_runtime_verify


def create_app() -> dict:
    """
    Returns the EMS application descriptor.
    In a real FastAPI/Flask setup this would return the app instance.
    In scaffold phase it returns a safe descriptor dict.
    """
    return {
        "service": "SSID-EMS",
        "version": VERSION,
        "mode": ENV_MODE,
        "started": START_SERVICES,
        "backend_port": EMS_BACKEND_PORT,
        "frontend_port": EMS_FRONTEND_PORT,
        "routes": {
            "/health": health_status,
            "/readiness": readiness_status,
            "/version": version_status,
            "/api/contract": get_api_contract,
            "/api/mvp/demo": get_demo_fixture,
            "/api/mvp/verify": get_verification_result,
            "/api/mvp/health": get_runtime_health,
            "/api/mvp/runtime/demo": get_runtime_demo,
            "/api/mvp/runtime/verify": post_runtime_verify,
            "/status": full_status,
        },
    }
