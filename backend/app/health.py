"""SSID-EMS liveness/readiness contracts backed by process lifecycle state."""

from __future__ import annotations

from threading import Lock

from backend.app.config import EMS_BACKEND_PORT, EMS_FRONTEND_PORT, ENV_MODE, SERVICE_NAME, START_SERVICES, VERSION

_STATE_LOCK = Lock()
_RUNTIME_STATE = {"started": False, "ready": False}


def set_runtime_state(*, started: bool, ready: bool) -> None:
    with _STATE_LOCK:
        _RUNTIME_STATE.update(started=started, ready=ready and started)


def runtime_state() -> dict[str, bool]:
    with _STATE_LOCK:
        return dict(_RUNTIME_STATE)


def health_status() -> dict:
    state = runtime_state()
    return {"service": SERVICE_NAME, "status": "ok", "started": state["started"] or START_SERVICES, "mode": ENV_MODE}


def readiness_status() -> dict:
    state = runtime_state()
    started = state["started"] or START_SERVICES
    ready = state["ready"] if state["started"] else False
    return {
        "service": SERVICE_NAME,
        "status": "ready" if ready else "not_ready",
        "reason": None if ready else ("local_scaffold_no_service_start" if not started else "initialization_incomplete"),
        "started": started,
        "mode": ENV_MODE,
    }


def version_status() -> dict:
    return {"service": SERVICE_NAME, "version": VERSION, "mode": ENV_MODE}


def full_status() -> dict:
    state = runtime_state()
    return {
        "service": SERVICE_NAME,
        "version": VERSION,
        "mode": ENV_MODE,
        "started": state["started"] or START_SERVICES,
        "backend_port": EMS_BACKEND_PORT,
        "frontend_port": EMS_FRONTEND_PORT,
        "health": health_status(),
        "readiness": readiness_status(),
    }
