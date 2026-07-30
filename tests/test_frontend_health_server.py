from __future__ import annotations

import importlib.util
import json
import py_compile
import threading
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SERVER_PATH = REPO_ROOT / "frontend" / "server.py"


def load_server_module():
    spec = importlib.util.spec_from_file_location("ssid_ems_frontend_server", SERVER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fetch_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=5) as response:  # nosec B310 - run-owned localhost test server
        return json.loads(response.read().decode("utf-8"))


def fetch_text(url: str) -> str:
    with urllib.request.urlopen(url, timeout=5) as response:  # nosec B310 - run-owned localhost test server
        return response.read().decode("utf-8")


def test_frontend_static_server_compiles_exposes_health_and_index_links():
    py_compile.compile(str(SERVER_PATH), doraise=True)
    index_path = REPO_ROOT / "frontend" / "index.html"
    assert index_path.exists()
    assert not (REPO_ROOT / "frontend" / "package.json").exists()

    server_module = load_server_module()
    server = server_module.create_frontend_server("127.0.0.1", 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base_url = f"http://127.0.0.1:{server.server_address[1]}"
        health = fetch_json(base_url + "/health")
        api_health = fetch_json(base_url + "/api/health")
        index = fetch_text(base_url + "/")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert health["service"] == "SSID-EMS"
    assert health["status"] == "ok"
    assert health["frontend_port"] == 3100
    assert health["manifest_present"] is False
    assert api_health["status"] == "ok"
    assert api_health["frontend_port"] == 3100
    assert api_health["backend_port"] == 8100
    assert 'href="/health"' in index
    assert 'href="/api/health"' in index
    assert "SSID-EMS Frontend" in index
