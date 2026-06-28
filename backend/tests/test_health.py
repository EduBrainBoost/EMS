from backend.app.config import EMS_BACKEND_PORT, EMS_FRONTEND_PORT, MODE, START_SERVICES
from backend.app.health import full_status, health_status, readiness_status, version_status


def test_health_status():
    h = health_status()
    assert h["service"] == "EMS"
    assert h["status"] == "not_started"
    assert h["started"] is False
    assert h["mode"] == "local_rebuild"


def test_readiness_status():
    r = readiness_status()
    assert r["service"] == "EMS"
    assert r["status"] == "not_ready"
    assert r["reason"] == "local_rebuild_no_service_start"
    assert r["started"] is False
    assert r["mode"] == "local_rebuild"


def test_version_status():
    v = version_status()
    assert v["service"] == "EMS"
    assert v["version"] == "0.1.0-rebuild"
    assert v["mode"] == "local_rebuild"


def test_full_status():
    f = full_status()
    assert f["service"] == "EMS"
    assert f["version"] == "0.1.0-rebuild"
    assert f["mode"] == "local_rebuild"
    assert f["started"] is False
    assert f["backend_port"] == EMS_BACKEND_PORT
    assert f["frontend_port"] == EMS_FRONTEND_PORT
    assert f["health"]["status"] == "not_started"
    assert f["readiness"]["status"] == "not_ready"
