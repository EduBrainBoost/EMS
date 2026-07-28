from __future__ import annotations

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

FRONTEND_PORT = 3100
BACKEND_PORT = 8100
SERVICE_NAME = "SSID-EMS"
FRONTEND_MODE = "local_static_admin_shell"

# Canonical static route registry. Backend APIs remain the authority for data and permissions.
RESTORE_ROUTES = [
    "/console", "/live", "/office", "/team", "/board/[taskId]",
    "/content/[contentId]", "/memory/[docId]", "/governance/command-center",
    "/governance/remediation", "/governance/sot-status", "/operations",
    "/automation", "/knowledge", "/risk",
]
ADMIN_ROUTES = [
    "/admin/compliance/exceptions", "/admin/compliance/jurisdictions",
    "/admin/audit/reports", "/admin/runtime/blockers", "/admin/settings",
    "/admin/settings/providers", "/admin/settings/integrations",
    "/admin/settings/feature-gates",
]
def _route_group(path: str) -> str:
    if path in {"/console", "/live"}: return "Overview"
    if path in {"/operations", "/office", "/team"}: return "Operations"
    if path == "/automation": return "Automation"
    if path in {"/knowledge", "/content/[contentId]", "/memory/[docId]"}: return "Knowledge"
    if path == "/risk": return "Risk"
    if path.startswith("/governance/"): return "Governance"
    return "Admin"

NAVIGATION = [
    (_route_group(path), path.strip("/").replace("/", " / "), path)
    for path in RESTORE_ROUTES + ADMIN_ROUTES
]
SPA_ROUTE_PREFIXES = tuple(dict.fromkeys(RESTORE_ROUTES + ADMIN_ROUTES))

REPO_ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = Path(__file__).with_name("index.html")


class FrontendRequestHandler(BaseHTTPRequestHandler):
    server_version = "SSIDEMSFrontend/0.1"

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        return

    def _send_json(self, status_code: int, body: dict[str, Any]) -> None:
        payload = json.dumps(body, sort_keys=True).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _send_html(self, status_code: int, html: str) -> None:
        payload = html.encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _index_html(self) -> str:
        if INDEX_PATH.exists():
            html = INDEX_PATH.read_text(encoding="utf-8")
            links = "".join(
                f'<a data-route="{path}" href="{path}">{label}</a>'
                for _group, label, path in NAVIGATION
            )
            return html.replace("<!-- NAVIGATION_REGISTRY -->", links)
        return "<html><body><h1>SSID-EMS Frontend</h1><p>Index missing.</p></body></html>"

    def do_GET(self) -> None:  # noqa: N802
        if self.path in {"/", "/index.html"} or self.path in SPA_ROUTE_PREFIXES:
            self._send_html(200, self._index_html())
            return
        if self.path in {"/health", "/api/health"}:
            self._send_json(
                200,
                {
                    "service": SERVICE_NAME,
                    "status": "ok",
                    "started": True,
                    "mode": FRONTEND_MODE,
                    "frontend_port": FRONTEND_PORT,
                    "backend_port": BACKEND_PORT,
                    "manifest_present": (REPO_ROOT / "package.json").exists(),
                },
            )
            return
        self._send_json(404, {"status": "ERROR", "error_code": "route_not_found", "path": self.path})

    def do_HEAD(self) -> None:  # noqa: N802
        if self.path in {"/", "/index.html"} or self.path in SPA_ROUTE_PREFIXES:
            payload = self._index_html().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            return
        if self.path in {"/health", "/api/health"}:
            payload = json.dumps({"service": SERVICE_NAME, "status": "ok"}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            return
        self.send_response(404)
        self.end_headers()


class FrontendHTTPServer(ThreadingHTTPServer):
    def __init__(self, server_address: tuple[str, int], RequestHandlerClass: type[BaseHTTPRequestHandler]):
        super().__init__(server_address, RequestHandlerClass)


def create_frontend_server(host: str = "127.0.0.1", port: int = FRONTEND_PORT) -> FrontendHTTPServer:
    if host not in {"127.0.0.1", "localhost"}:
        raise ValueError("frontend server may bind only to localhost")
    return FrontendHTTPServer((host, port), FrontendRequestHandler)


def serve_frontend(host: str = "127.0.0.1", port: int = FRONTEND_PORT) -> None:
    server = create_frontend_server(host=host, port=port)
    print(f"SSID-EMS frontend listening on http://{host}:{server.server_address[1]}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("SSID-EMS frontend shutting down", flush=True)
    finally:
        server.server_close()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SSID-EMS frontend server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=FRONTEND_PORT, type=int)
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = parse_args()
    serve_frontend(host=args.host, port=args.port)
