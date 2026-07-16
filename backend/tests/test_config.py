import pytest
from backend.app.config import (
    EMS_BACKEND_PORT,
    EMS_FRONTEND_PORT,
    ENV_MODE,
    FORBIDDEN_PORTS,
    START_SERVICES,
    validate_ports,
)


def test_frontend_port_is_allowed():
    assert EMS_FRONTEND_PORT == 3100
    assert EMS_FRONTEND_PORT not in FORBIDDEN_PORTS


def test_backend_port_is_allowed():
    assert EMS_BACKEND_PORT == 8100
    assert EMS_BACKEND_PORT not in FORBIDDEN_PORTS


def test_forbidden_ports_listed():
    expected = [3000, 3001, 3002, 3210, 5173, 4321, 8000]
    assert FORBIDDEN_PORTS == expected


def test_env_mode_is_scaffold():
    assert ENV_MODE == "local_scaffold"


def test_start_services_is_false():
    assert START_SERVICES is False


def test_validate_ports_passes():
    result = validate_ports()
    assert result["valid"] is True
    assert result["violations"] == []
    assert result["frontend_port"] == 3100
    assert result["backend_port"] == 8100
