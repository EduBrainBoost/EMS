from backend.app.config import EMS_BACKEND_PORT, EMS_FRONTEND_PORT, ENV_MODE, START_SERVICES
from backend.app.health import full_status, health_status, readiness_status, version_status


def test_health_status():
    h = health_status()
    assert h["service"] == "SSID-EMS"
    assert h["status"] == "ok"
    assert h["started"] is False
    assert h["mode"] == "local_scaffold"


def test_readiness_status():
    r = readiness_status()
    assert r["service"] == "SSID-EMS"
    assert r["status"] == "not_ready"
    assert r["reason"] == "local_scaffold_no_service_start"
    assert r["started"] is False
    assert r["mode"] == "local_scaffold"


def test_version_status():
    v = version_status()
    assert v["service"] == "SSID-EMS"
    assert v["version"] == "0.1.0-scaffold"
    assert v["mode"] == "local_scaffold"


def test_full_status():
    f = full_status()
    assert f["service"] == "SSID-EMS"
    assert f["version"] == "0.1.0-scaffold"
    assert f["mode"] == "local_scaffold"
    assert f["started"] is False
    assert f["backend_port"] == EMS_BACKEND_PORT
    assert f["frontend_port"] == EMS_FRONTEND_PORT
    assert f["health"]["status"] == "ok"
    assert f["readiness"]["status"] == "not_ready"
