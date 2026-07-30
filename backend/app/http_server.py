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

from backend.app.health import full_status, health_status, readiness_status, set_runtime_state, version_status
from backend.app.api_contract import get_api_contract
from backend.app.runtime_http_adapter import LocalRuntimeAdapter
from backend.app.config import EMS_BACKEND_PORT, START_SERVICES
from backend.app.security import cors_headers, is_origin_allowed

_OPERATIONAL_ADAPTER = None


def _get_operational_adapter():
    global _OPERATIONAL_ADAPTER
    if _OPERATIONAL_ADAPTER is None and START_SERVICES:
        from backend.app.operational_adapter import OperationalAdapter
        _OPERATIONAL_ADAPTER = OperationalAdapter()
    return _OPERATIONAL_ADAPTER


class BackendRequestHandler(BaseHTTPRequestHandler):
    server_version = ""
    sys_version = ""

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        return

    def _security_headers(self, *, sensitive: bool = False) -> dict[str, str]:
        headers = {
            "Content-Security-Policy": "default-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'",
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "no-referrer",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
            "Cross-Origin-Opener-Policy": "same-origin",
            "Cross-Origin-Resource-Policy": "same-origin",
            "X-Frame-Options": "DENY",
            "Cache-Control": "no-store",
        }
        if sensitive:
            headers["Pragma"] = "no-cache"
        return headers

    def _send_json(self, status_code: int, body: dict[str, Any], headers: dict[str, str] | None = None) -> None:
        payload = json.dumps(body, sort_keys=True).encode("utf-8")
        self.send_response(status_code)
        merged = self._security_headers(sensitive=status_code >= 400 or self.path.startswith("/api/"))
        merged.update(headers or {})
        for key, value in merged.items():
            self.send_header(key, value)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:  # noqa: N802
        adapter = getattr(self.server, "adapter", None) or _get_operational_adapter()
        try:
            if self.path in {"/health", "/api/health"}:
                self._send_json(200, health_status(), cors_headers(self.headers.get("Origin")))
                return
            if self.path == "/readiness":
                self._send_json(200, readiness_status(), cors_headers(self.headers.get("Origin")))
                return
            if self.path == "/version":
                self._send_json(200, version_status(), cors_headers(self.headers.get("Origin")))
                return
            if self.path == "/status":
                self._send_json(200, full_status(), cors_headers(self.headers.get("Origin")))
                return
            if self.path == "/api/contract":
                self._send_json(200, get_api_contract(), cors_headers(self.headers.get("Origin")))
                return
            if self.path.startswith("/api/v1/"):
                if isinstance(adapter, LocalRuntimeAdapter):
                    response = adapter.handle_request("GET", self.path, headers={key: value for key, value in self.headers.items()})
                    self._send_json(response["status_code"], response["body"], response.get("headers"))
                    return
                if adapter is None:
                    self._send_json(501, {"status": "ERROR", "error_code": "operational_mode_disabled", "path": self.path})
                    return
                response = adapter.handle_request("GET", self.path, headers={key: value for key, value in self.headers.items()})
                self._send_json(response["status_code"], response["body"])
                return
            if self.path == "/api/mvp/health":
                response = adapter.handle_request("GET", "/api/mvp/health")
                self._send_json(response["status_code"], response["body"], response.get("headers"))
                return
            if self.path == "/api/mvp/demo":
                response = adapter.handle_request("GET", "/api/mvp/demo")
                self._send_json(response["status_code"], response["body"])
                return
            if self.path.startswith("/api/v1/auth/"):
                response = adapter.handle_request("GET", self.path, headers={key: value for key, value in self.headers.items()})
                self._send_json(response["status_code"], response["body"], response.get("headers"))
                return
            if self.path == "/api/mvp/auth/session":
                response = adapter.handle_request("GET", "/api/mvp/auth/session", headers={key: value for key, value in self.headers.items()})
                self._send_json(response["status_code"], response["body"], response.get("headers"))
                return
            self._send_json(404, {"status": "ERROR", "error_code": "route_not_found", "path": self.path})
        except Exception as exc:
            status = getattr(exc, "status_code", 500)
            error_code = getattr(exc, "error_code", "INTERNAL_ERROR")
            message = str(exc) or "Internal server error"
            self._send_json(status, {"status": "ERROR", "error_code": error_code, "message": message})

    def _handle_api_v1(self, method: str) -> None:
        adapter = getattr(self.server, "adapter", None) or _get_operational_adapter()
        if adapter is None:
            self._send_json(501, {"status": "ERROR", "error_code": "operational_mode_disabled", "path": self.path})
            return
        raw = b""
        if method in {"POST", "PUT", "PATCH"}:
            raw = self.rfile.read(int(self.headers.get("Content-Length", "0") or 0))
        route = self.path
        if isinstance(adapter, LocalRuntimeAdapter):
            if route == "/api/v1/auth/login": route = "/api/mvp/auth/login"
            elif route == "/api/v1/auth/logout": route = "/api/mvp/auth/logout"
            elif route == "/api/v1/auth/session": route = "/api/mvp/auth/session"
        response = adapter.handle_request(method, route, raw_body=raw, headers={key: value for key, value in self.headers.items()})
        response_headers = dict(response.get("headers") or {})
        response_headers.update(cors_headers(self.headers.get("Origin")))
        self._send_json(response["status_code"], response["body"], response_headers)

    def do_OPTIONS(self) -> None:  # noqa: N802
        origin = self.headers.get("Origin")
        self.send_response(204 if origin and is_origin_allowed(origin) else 403)
        merged = self._security_headers(sensitive=True)
        if origin and is_origin_allowed(origin):
            merged.update(cors_headers(origin))
        for key, value in merged.items():
            self.send_header(key, value)
        self.end_headers()

    def do_POST(self) -> None:  # noqa: N802
        try:
            if self.path.startswith("/api/v1/"):
                self._handle_api_v1("POST")
                return
            if self.path == "/api/mvp/verify":
                self._handle_api_v1("POST")
                return
            if self.path == "/api/mvp/auth/login":
                self._handle_api_v1("POST")
                return
            if self.path == "/api/mvp/auth/logout":
                self._handle_api_v1("POST")
                return
            self._send_json(405, {"status": "ERROR", "error_code": "method_not_allowed", "path": self.path})
        except Exception as exc:
            status = getattr(exc, "status_code", 500)
            error_code = getattr(exc, "error_code", "INTERNAL_ERROR")
            message = str(exc) or "Internal server error"
            self._send_json(status, {"status": "ERROR", "error_code": error_code, "message": message})

    def do_PUT(self) -> None:  # noqa: N802
        try:
            if self.path.startswith("/api/v1/"):
                self._handle_api_v1("PUT")
                return
            self._send_json(405, {"status": "ERROR", "error_code": "method_not_allowed", "path": self.path})
        except Exception as exc:
            status = getattr(exc, "status_code", 500)
            error_code = getattr(exc, "error_code", "INTERNAL_ERROR")
            message = str(exc) or "Internal server error"
            self._send_json(status, {"status": "ERROR", "error_code": error_code, "message": message})

    def do_PATCH(self) -> None:  # noqa: N802
        try:
            if self.path.startswith("/api/v1/"):
                self._handle_api_v1("PATCH")
                return
            self._send_json(405, {"status": "ERROR", "error_code": "method_not_allowed", "path": self.path})
        except Exception as exc:
            status = getattr(exc, "status_code", 500)
            error_code = getattr(exc, "error_code", "INTERNAL_ERROR")
            message = str(exc) or "Internal server error"
            self._send_json(status, {"status": "ERROR", "error_code": error_code, "message": message})

    def do_DELETE(self) -> None:  # noqa: N802
        try:
            if self.path.startswith("/api/v1/"):
                self._handle_api_v1("DELETE")
                return
            self._send_json(405, {"status": "ERROR", "error_code": "method_not_allowed", "path": self.path})
        except Exception as exc:
            status = getattr(exc, "status_code", 500)
            error_code = getattr(exc, "error_code", "INTERNAL_ERROR")
            message = str(exc) or "Internal server error"
            self._send_json(status, {"status": "ERROR", "error_code": error_code, "message": message})


class BackendHTTPServer(ThreadingHTTPServer):
    def __init__(self, server_address: tuple[str, int], RequestHandlerClass: type[BaseHTTPRequestHandler], adapter: LocalRuntimeAdapter | None = None):
        super().__init__(server_address, RequestHandlerClass)
        self.adapter = adapter or LocalRuntimeAdapter()


def create_backend_server(host: str = "127.0.0.1", port: int = 8100, adapter: LocalRuntimeAdapter | None = None) -> BackendHTTPServer:
    if host not in {"127.0.0.1", "localhost"}:
        raise ValueError("backend server may bind only to localhost")
    global _OPERATIONAL_ADAPTER
    if adapter is not None:
        _OPERATIONAL_ADAPTER = adapter
    server = BackendHTTPServer((host, port), BackendRequestHandler, adapter=adapter)
    return server


def serve_backend(host: str = "127.0.0.1", port: int = 8100) -> None:
    server = create_backend_server(host=host, port=port)
    set_runtime_state(started=True, ready=True)
    print(f"SSID-EMS backend listening on http://{host}:{server.server_address[1]}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("SSID-EMS backend shutting down", flush=True)
    finally:
        set_runtime_state(started=False, ready=False)
        server.server_close()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SSID-EMS backend server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8100, type=int)
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = parse_args()
    serve_backend(host=args.host, port=args.port)
