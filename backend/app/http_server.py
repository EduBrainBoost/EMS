from __future__ import annotations

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.health import full_status, health_status, readiness_status, version_status
from backend.app.runtime_http_adapter import LocalRuntimeAdapter


class BackendRequestHandler(BaseHTTPRequestHandler):
    server_version = "SSIDEMSBackend/0.1"

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        return

    def _send_json(self, status_code: int, body: dict[str, Any]) -> None:
        payload = json.dumps(body, sort_keys=True).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:  # noqa: N802
        adapter = self.server.adapter  # type: ignore[attr-defined]
        if self.path in {"/health", "/api/health"}:
            self._send_json(200, health_status())
            return
        if self.path == "/readiness":
            self._send_json(200, readiness_status())
            return
        if self.path == "/version":
            self._send_json(200, version_status())
            return
        if self.path == "/status":
            self._send_json(200, full_status())
            return
        if self.path == "/api/mvp/health":
            response = adapter.handle_request("GET", "/api/mvp/health")
            self._send_json(response["status_code"], response["body"])
            return
        if self.path == "/api/mvp/demo":
            response = adapter.handle_request("GET", "/api/mvp/demo")
            self._send_json(response["status_code"], response["body"])
            return
        if self.path == "/api/mvp/auth/session":
            response = adapter.handle_request("GET", "/api/mvp/auth/session")
            self._send_json(response["status_code"], response["body"])
            return
        self._send_json(404, {"status": "ERROR", "error_code": "route_not_found", "path": self.path})

    def do_POST(self) -> None:  # noqa: N802
        adapter = self.server.adapter  # type: ignore[attr-defined]
        raw = self.rfile.read(int(self.headers.get("Content-Length", "0") or 0))
        if self.path == "/api/mvp/verify":
            response = adapter.handle_request("POST", "/api/mvp/verify", raw_body=raw, headers={key: value for key, value in self.headers.items()})
            self._send_json(response["status_code"], response["body"])
            return
        if self.path == "/api/mvp/auth/login":
            response = adapter.handle_request("POST", "/api/mvp/auth/login", raw_body=raw, headers={key: value for key, value in self.headers.items()})
            self._send_json(response["status_code"], response["body"])
            return
        if self.path == "/api/mvp/auth/logout":
            response = adapter.handle_request("POST", "/api/mvp/auth/logout", headers={key: value for key, value in self.headers.items()})
            self._send_json(response["status_code"], response["body"])
            return
        self._send_json(405, {"status": "ERROR", "error_code": "method_not_allowed", "path": self.path})


class BackendHTTPServer(ThreadingHTTPServer):
    def __init__(self, server_address: tuple[str, int], RequestHandlerClass: type[BaseHTTPRequestHandler], adapter: LocalRuntimeAdapter | None = None):
        super().__init__(server_address, RequestHandlerClass)
        self.adapter = adapter or LocalRuntimeAdapter()


def create_backend_server(host: str = "127.0.0.1", port: int = 8100, adapter: LocalRuntimeAdapter | None = None) -> BackendHTTPServer:
    if host not in {"127.0.0.1", "localhost"}:
        raise ValueError("backend server may bind only to localhost")
    return BackendHTTPServer((host, port), BackendRequestHandler, adapter)


def serve_backend(host: str = "127.0.0.1", port: int = 8100) -> None:
    server = create_backend_server(host=host, port=port)
    print(f"SSID-EMS backend listening on http://{host}:{server.server_address[1]}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("SSID-EMS backend shutting down", flush=True)
    finally:
        server.server_close()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SSID-EMS backend server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8100, type=int)
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = parse_args()
    serve_backend(host=args.host, port=args.port)
