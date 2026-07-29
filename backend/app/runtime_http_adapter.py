"""Local HTTP adapter for SSID Productization Sprint 02.

Uses Python stdlib only for local testability. No external network service is
contacted; the optional HTTP server binds only to caller-provided local address
inside tests.
"""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sys
from typing import Any

_GITHUB_ROOT = Path(__file__).resolve().parents[3]
_SSID_REPO = Path(os.environ["SSID_REPO"]) if os.environ.get("SSID_REPO") else _GITHUB_ROOT / "SSID"
_SSID_CANDIDATES = (
    _SSID_REPO,
    Path(r"C:\SSID-R\20260728T204803Z\SSID"),
    Path(r"C:\Users\bibel\SSID-Workspace\SSID-Arbeitsbereich\Github\SSID"),
)
_SSID_REPO = next((candidate for candidate in _SSID_CANDIDATES if (candidate / "03_core" / "src").is_dir()), _SSID_REPO)
_CORE_SRC = _SSID_REPO / "03_core" / "src"
for candidate in (str(_CORE_SRC), str(_SSID_REPO)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from ssid_production import productization_sprint_02_runtime as runtime  # noqa: E402

MAX_REQUEST_BYTES = 8192
ALLOWED_VERIFY_FIELDS = {
    "request_id",
    "identity_profile_ref",
    "credential_ref",
    "verifier_ref",
    "nonce_hash",
    "runtime_id",
    "auth_boundary",
    "created_at_utc",
    "requested_purpose",
    "schema_version",
}

AUTH_DEMO_USERNAME = "demo"
AUTH_DEMO_PASSWORD = "demo"
AUTH_DEMO_SESSION_MODE = "local_demo"
AUTH_DEMO_USER_ROLE = "demo_user"
AUTH_DEMO_PRIVACY_BOUNDARY = "no_real_credentials_no_persistence"
AUTH_DEMO_PERSISTENCE_BOUNDARY = "no_persistence"
AUTH_INVALID_DEMO_CREDENTIALS = "AUTH_INVALID_DEMO_CREDENTIALS"


class LocalRuntimeAdapter:
    """Fail-closed local EMS runtime adapter."""

    def __init__(self, persistence: runtime.SafePersistenceStub | None = None) -> None:
        self.persistence = persistence or runtime.SafePersistenceStub()
        self._demo_cache: dict[str, Any] | None = None
        self._auth_authenticated = False

    def _auth_success(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "authenticated": self._auth_authenticated,
            "session_mode": AUTH_DEMO_SESSION_MODE,
            "persistence": "none",
            "privacy_boundary": AUTH_DEMO_PRIVACY_BOUNDARY,
            "persistence_boundary": AUTH_DEMO_PERSISTENCE_BOUNDARY,
        }

    def _auth_error(self, status_code: int = 401) -> dict[str, Any]:
        return {
            "status_code": status_code,
            "body": {
                "status": "error",
                "authenticated": False,
                "error_code": AUTH_INVALID_DEMO_CREDENTIALS,
                "persistence_boundary": AUTH_DEMO_PERSISTENCE_BOUNDARY,
            },
        }

    def handle_request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
        raw_body: str | bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        method = method.upper()
        headers = headers or {}
        normalized_headers = {key.lower(): value for key, value in headers.items()}
        if raw_body is not None:
            if method == "POST" and path in {"/api/mvp/verify", "/api/mvp/auth/login"} and normalized_headers.get("content-type", "application/json").split(";", 1)[0].strip().lower() != "application/json":
                if path == "/api/mvp/auth/login":
                    return self._auth_error(401)
                return self._error(415, "wrong_content_type", "verify endpoint requires application/json", route=f"{method} {path}")
            raw_length = len(raw_body.encode("utf-8") if isinstance(raw_body, str) else raw_body)
            if raw_length > MAX_REQUEST_BYTES:
                return self._error(413, "payload_too_large", "request body exceeds local RC limit")
            try:
                if isinstance(raw_body, bytes):
                    raw_body = raw_body.decode("utf-8")
                json_body = json.loads(raw_body) if raw_body else None
            except json.JSONDecodeError:
                if path == "/api/mvp/auth/login":
                    return self._auth_error(401)
                return self._error(400, "invalid_json", "request body is not valid JSON")
        if method == "GET" and path == "/api/mvp/health":
            return self._ok(
                {
                    "service": "SSID-EMS",
                    "status": "ok",
                    "runtime_id": runtime.RUNTIME_ID,
                    "adapter": "local-stdlib-http",
                    "auth_boundary": runtime.auth_boundary_contract(),
                    "persistence_decision": self.persistence.decision(),
                    "external_services": "NOT_USED",
                    "diagnostics": {
                        "runtime_mode": "local-release-candidate",
                        "program_epic_02_ready": True,
                        "contract_version": "0.3.0-program-epic-02",
                        "external_services": "NOT_USED",
                        "logs_contain_pii": False,
                        "logs_contain_secrets": False,
                        "max_request_bytes": MAX_REQUEST_BYTES,
                    },
                    "privacy_boundary": runtime.PRIVACY_BOUNDARY,
                    "persistence_boundary": AUTH_DEMO_PERSISTENCE_BOUNDARY,
                }
            )
        if method == "GET" and path == "/api/mvp/demo":
            if self._demo_cache is None:
                self._demo_cache = runtime.runtime_demo_fixture()
            return self._ok(self._demo_cache)
        if path == "/api/mvp/demo":
            return self._error(405, "method_not_allowed", "demo endpoint allows GET only", route=f"{method} {path}")
        if method == "GET" and path == "/api/mvp/auth/session":
            return self._ok(self._auth_success())
        if method == "POST" and path == "/api/mvp/auth/logout":
            self._auth_authenticated = False
            return self._ok({"status": "ok", "authenticated": False, "session_mode": AUTH_DEMO_SESSION_MODE, "privacy_boundary": AUTH_DEMO_PRIVACY_BOUNDARY, "persistence_boundary": AUTH_DEMO_PERSISTENCE_BOUNDARY})
        if method == "POST" and path == "/api/mvp/auth/login":
            if not isinstance(json_body, dict):
                return self._auth_error(401)
            if json_body.get("username") != AUTH_DEMO_USERNAME or json_body.get("password") != AUTH_DEMO_PASSWORD:
                return self._auth_error(401)
            self._auth_authenticated = True
            return self._ok(
                {
                    "status": "ok",
                    "authenticated": True,
                    "session_mode": AUTH_DEMO_SESSION_MODE,
                    "user_role": AUTH_DEMO_USER_ROLE,
                    "privacy_boundary": AUTH_DEMO_PRIVACY_BOUNDARY,
                    "persistence_boundary": AUTH_DEMO_PERSISTENCE_BOUNDARY,
                }
            )
        if path in {"/api/mvp/auth/login", "/api/mvp/auth/logout", "/api/mvp/auth/session"}:
            return self._error(405, "method_not_allowed", "auth endpoint method not allowed", route=f"{method} {path}")
        if method == "POST" and path == "/api/mvp/verify":
            if "x-ssid-production-auth" in normalized_headers:
                return self._error(403, "production_auth_not_allowed", "production-like auth is forbidden in local RC", route=f"{method} {path}")
            auth_context = normalized_headers.get("x-ssid-demo-auth")
            if auth_context and auth_context != runtime.RUNTIME_AUTH_STUB:
                return self._error(403, "fake_token_rejected", "safe demo auth token was not accepted", route=f"{method} {path}")
            if not isinstance(json_body, dict):
                return self._error(400, "schema_violation", "verify request must be a JSON object", route=f"{method} {path}")
            unknown_fields = set(json_body) - ALLOWED_VERIFY_FIELDS
            if unknown_fields:
                if "contract_version" in unknown_fields:
                    return self._error(400, "unsupported_version", "unsupported contract version is rejected", route=f"{method} {path}")
                if "status" in unknown_fields:
                    return self._error(400, "invalid_status_injection", "status injection is rejected", route=f"{method} {path}")
                return self._error(400, "unknown_fields_rejected", "unknown verify fields are rejected", route=f"{method} {path}")
            if auth_context == runtime.RUNTIME_AUTH_STUB and isinstance(json_body, dict) and json_body.get("auth_boundary") not in {None, "safe-demo-auth-stub-required-for-verify"}:
                return self._error(400, "auth_boundary_violation", "auth boundary bypass attempt rejected", route=f"{method} {path}")
            if self._demo_cache is None:
                self._demo_cache = runtime.runtime_demo_fixture()
            body = runtime.verify_runtime_request(json_body, auth_context=auth_context, persistence=self.persistence)
            return {"status_code": 200 if body["status"] == "PASS" else 403 if body.get("error_code") == "auth_required" else 400, "body": body}
        if path == "/api/mvp/verify":
            return self._error(405, "method_not_allowed", "verify endpoint allows POST only", route=f"{method} {path}")
        return self._error(404, "route_not_allowed", "runtime route is not allowed", route=f"{method} {path}")

    def _ok(self, body: dict[str, Any]) -> dict[str, Any]:
        return {"status_code": 200, "body": body}

    def _error(self, status_code: int, error_code: str, message: str, *, route: str = "UNKNOWN") -> dict[str, Any]:
        event = runtime.runtime_audit_event(
            "RUNTIME_ERROR_RECORDED",
            {"error_code": error_code, "route": route},
            evidence_id=f"evr_20260709_runtime_http_error_{status_code}",
            previous_evidence_hash=runtime.ZERO_HASH_REF,
            created_at_utc="2026-07-09T11:19:59Z",
        )
        return {
            "status_code": status_code,
            "body": {
                "status": "ERROR",
                "error_code": error_code,
                "message": message,
                "audit_correlation_id": event["evidence_id"],
                "runtime_audit_event": event,
                "privacy_boundary": runtime.PRIVACY_BOUNDARY,
            },
        }


def get_runtime_health() -> dict[str, Any]:
    return LocalRuntimeAdapter().handle_request("GET", "/api/mvp/health")["body"]


def get_runtime_demo() -> dict[str, Any]:
    return LocalRuntimeAdapter().handle_request("GET", "/api/mvp/demo")["body"]


def post_runtime_verify(request: dict[str, Any] | None, auth_context: str | None = None) -> dict[str, Any]:
    headers = {"X-SSID-Demo-Auth": auth_context} if auth_context else {}
    return LocalRuntimeAdapter().handle_request("POST", "/api/mvp/verify", json_body=request, headers=headers)["body"]


def create_runtime_server(host: str = "127.0.0.1", port: int = 0, adapter: LocalRuntimeAdapter | None = None) -> ThreadingHTTPServer:
    runtime_adapter = adapter or LocalRuntimeAdapter()

    class RuntimeRequestHandler(BaseHTTPRequestHandler):
        server_version = "SSIDLocalRuntime/0.1"

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
            return

        def _send(self, response: dict[str, Any]) -> None:
            payload = json.dumps(response["body"], sort_keys=True).encode("utf-8")
            self.send_response(response["status_code"])
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self) -> None:  # noqa: N802
            self._send(runtime_adapter.handle_request("GET", self.path))

        def do_POST(self) -> None:  # noqa: N802
            raw = self.rfile.read(int(self.headers.get("Content-Length", "0") or 0))
            headers = {key: value for key, value in self.headers.items()}
            self._send(runtime_adapter.handle_request("POST", self.path, raw_body=raw, headers=headers))

    if host not in {"127.0.0.1", "localhost"}:
        raise ValueError("runtime server may bind only to localhost")
    return ThreadingHTTPServer((host, port), RuntimeRequestHandler)
