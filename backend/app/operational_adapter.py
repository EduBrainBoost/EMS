"""
SSID-EMS operational HTTP adapter.

Minimal stdlib-only router for /api/v1 routes when services are enabled.
Existing /api/mvp/* routes keep the local runtime adapter unchanged.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from typing import Any

from backend.app import config
from backend.app.audit import verify_chain
from backend.app.auth_service import AuthError, login, logout, resolve_session
from backend.app.backup import create_backup, restore_test
from backend.app.database import Database
from backend.app.password import hash_password, verify_password
from backend.app.rbac import (
    AuthContext,
    RBACError,
    require_any_permission,
    require_authenticated_user,
    require_permission,
)
from backend.app.repository import (
    assign_roles,
    count_active_super_admins,
    count_users,
    create_user,
    get_user_by_id,
    list_permissions,
    list_roles,
    list_sessions,
    revoke_session,
    set_user_status,
)
from backend.app.security import cors_headers, csrf_matches, is_origin_allowed, new_csrf_token, source_hash, user_agent_hash


class OperationalAdapter:
    def __init__(self, db: Database | None = None) -> None:
        self.db = db or Database()
        self.db.ensure_schema()

    # --- helpers ----------------------------------------------------------
    def _json(self, body: dict[str, Any], status: int = 200) -> dict[str, Any]:
        return {"status_code": status, "body": body}

    def _error(self, status: int, error_code: str, message: str) -> dict[str, Any]:
        return {
            "status_code": status,
            "body": {
                "status": "ERROR",
                "error_code": error_code,
                "message": message,
                "timestamp_utc": _now_utc(),
            },
        }

    def _ok(self, body: dict[str, Any]) -> dict[str, Any]:
        return self._json(body, 200)

    # --- auth -------------------------------------------------------------
    def handle_auth_login(self, payload: dict[str, Any], origin: str | None, source_ip: str, user_agent: str, request_id: str) -> dict[str, Any]:
        try:
            result = login(self.db, payload.get("username", ""), payload.get("password", ""),
                           source_ip=source_ip, user_agent=user_agent, request_id=request_id)
            return self._ok(result)
        except AuthError as exc:
            return self._error(exc.status_code, exc.error_code, exc.message)

    def handle_auth_logout(self, token: str | None, actor_id: str, actor_role: str) -> dict[str, Any]:
        logout(self.db, token, actor_id=actor_id, actor_role=actor_role)
        return self._ok({"status": "ok", "authenticated": False})

    def handle_auth_session(self, token: str | None) -> dict[str, Any]:
        ctx = resolve_session(self.db, token)
        if not ctx:
            return self._json({"authenticated": False}, 200)
        return self._json({
            "authenticated": True,
            "user_id": ctx.user_id,
            "username": ctx.username,
            "roles": ctx.roles,
            "session_id": ctx.session_id,
        })

    # --- admin/users ------------------------------------------------------
    def handle_admin_users(self, ctx: AuthContext, query: dict[str, str]) -> dict[str, Any]:
        require_permission(None, ctx, "users.read")
        users = list_users(self.db, limit=int(query.get("limit", "50")), offset=int(query.get("offset", "0")))
        return self._ok({"users": [_safe_user(u) for u in users]})

    def handle_admin_user_detail(self, ctx: AuthContext, user_id: str) -> dict[str, Any]:
        require_permission(None, ctx, "users.read")
        user = get_user_by_id(self.db, user_id)
        if not user:
            return self._error(404, "USER_NOT_FOUND", "User not found")
        return self._ok({"user": _safe_user(user)})

    def handle_admin_user_status(self, ctx: AuthContext, user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        require_permission(None, ctx, "users.manage")
        target = get_user_by_id(self.db, user_id)
        if not target:
            return self._error(404, "USER_NOT_FOUND", "User not found")
        if payload.get("status") in (None, "disabled") and _is_last_active_super_admin(self.db, user_id):
            return self._error(403, "LAST_SUPER_ADMIN_PROTECTED", "Cannot disable the last active super admin")
        user = set_user_status(self.db, user_id, _safe_status(payload.get("status", target["status"])),
                               actor_id=ctx.user_id, actor_role=ctx.roles[0] if ctx.roles else "none",
                               reason=payload.get("reason", ""))
        return self._ok({"user": _safe_user(user)})

    def handle_admin_user_roles(self, ctx: AuthContext, user_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        require_permission(None, ctx, "roles.manage")
        target = get_user_by_id(self.db, user_id)
        if not target:
            return self._error(404, "USER_NOT_FOUND", "User not found")
        if target["id"] == ctx.user_id:
            return self._error(403, "SELF_ROLE_CHANGE_FORBIDDEN", "Users cannot change their own roles")
        roles = [r for r in payload.get("roles", []) if r in _ALL_ROLES]
        assign_roles(self.db, user_id, roles, actor_id=ctx.user_id,
                     actor_role=ctx.roles[0] if ctx.roles else "none", reason=payload.get("reason", ""))
        return self._ok({"roles": get_user_roles(self.db, user_id)})

    # --- admin/roles/permissions -------------------------------------------
    def handle_admin_roles(self, ctx: AuthContext) -> dict[str, Any]:
        require_permission(None, ctx, "roles.read")
        return self._ok({"roles": list_roles(self.db)})

    def handle_admin_permissions(self, ctx: AuthContext) -> dict[str, Any]:
        require_permission(None, ctx, "roles.read")
        return self._ok({"permissions": list_permissions(self.db)})

    # --- admin/sessions ----------------------------------------------------
    def handle_admin_sessions(self, ctx: AuthContext) -> dict[str, Any]:
        require_permission(None, ctx, "sessions.read")
        return self._ok({"sessions": [_safe_session(s) for s in list_sessions(self.db)]})

    def handle_admin_session_revoke(self, ctx: AuthContext, session_id: str) -> dict[str, Any]:
        require_permission(None, ctx, "sessions.revoke")
        ok = revoke_session(self.db, session_id, actor_id=ctx.user_id,
                            actor_role=ctx.roles[0] if ctx.roles else "none", reason="admin_revoke")
        if not ok:
            return self._error(404, "SESSION_NOT_FOUND", "Session not found or already revoked")
        return self._ok({"status": "ok", "session_id": session_id})

    # --- admin/audit -------------------------------------------------------
    def handle_admin_audit(self, ctx: AuthContext) -> dict[str, Any]:
        require_any_permission(None, ctx, {"audit.read", "audit.export"})
        events = []
        with self.db._connection() as conn:
            for row in conn.execute("SELECT * FROM audit_events ORDER BY sequence_number DESC LIMIT 100").fetchall():
                r = dict(row)
                r["payload_json"] = "[REDACTED]" if r.get("payload_json") else ""
                events.append(r)
        return self._ok({"events": events})

    # --- backup/restore ----------------------------------------------------
    def handle_backup(self, ctx: AuthContext) -> dict[str, Any]:
        require_permission(None, ctx, "registry.manage")
        result = create_backup(self.db)
        return self._ok(result)

    def handle_restore_test(self, ctx: AuthContext, payload: dict[str, Any]) -> dict[str, Any]:
        require_permission(None, ctx, "registry.manage")
        backup_path = payload.get("backup_path", "")
        isolated_path = payload.get("isolated_db_path", "")
        if not backup_path or not isolated_path:
            return self._error(400, "INVALID_REQUEST", "backup_path and isolated_db_path required")
        result = restore_test(self.db, backup_path, isolated_path)
        return self._ok(result)

    # --- router ------------------------------------------------------------
    def handle_request(self, method: str, path: str, *, raw_body: bytes | None = None, headers: dict[str, str] | None = None) -> dict[str, Any]:
        headers = headers or {}
        normalized = {k.lower(): v for k, v in headers.items()}
        origin = normalized.get("origin")
        source_ip = normalized.get("x-forwarded-for", normalized.get("x-real-ip", "127.0.0.1")).split(",")[0].strip()
        request_id = normalized.get("x-request-id", "")

        if method == "OPTIONS" and is_origin_allowed(origin):
            return {"status_code": 204, "body": {}, "cors": cors_headers(origin)}

        payload: dict[str, Any] | None = None
        if raw_body is not None and method in {"POST", "PUT", "PATCH"}:
            try:
                payload = json.loads(raw_body.decode("utf-8")) if raw_body else {}
            except json.JSONDecodeError:
                return self._error(400, "INVALID_JSON", "Request body is not valid JSON")

        # auth session resolution
        token = _bearer_token(normalized)

        if method == "GET" and path == "/api/v1/auth/session":
            return self.handle_auth_session(token)

        if method == "POST" and path == "/api/v1/auth/login":
            if not isinstance(payload, dict):
                return self._error(400, "INVALID_PAYLOAD", "Login requires JSON object")
            return self.handle_auth_login(payload, origin, source_hash(source_ip), user_agent_hash(normalized.get("user-agent", "unknown")), request_id)

        if method == "POST" and path == "/api/v1/auth/logout":
            ctx = resolve_session(self.db, token)
            return self.handle_auth_logout(token, actor_id=ctx.user_id if ctx else "anonymous", actor_role=ctx.roles[0] if ctx and ctx.roles else "none")

        if method == "GET" and path == "/api/v1/admin/sessions":
            ctx = resolve_session(self.db, token)
            if not ctx:
                return self._error(401, "AUTH_SESSION_REQUIRED", "Authentication required")
            require_permission(None, ctx, "sessions.read")
            return self._ok({"sessions": [_safe_session(s) for s in list_sessions(self.db)]})

        if method == "POST" and _match(path, "/api/v1/admin/sessions/{session_id}/revoke"):
            ctx = resolve_session(self.db, token)
            if not ctx:
                return self._error(401, "AUTH_SESSION_REQUIRED", "Authentication required")
            return self.handle_admin_session_revoke(ctx, path.split("/")[-1])

        if method == "GET" and path == "/api/v1/admin/users":
            ctx = resolve_session(self.db, token)
            if not ctx:
                return self._error(401, "AUTH_SESSION_REQUIRED", "Authentication required")
            return self.handle_admin_users(ctx, normalized)

        if method == "GET" and _match(path, "/api/v1/admin/users/{user_id}"):
            ctx = resolve_session(self.db, token)
            if not ctx:
                return self._error(401, "AUTH_SESSION_REQUIRED", "Authentication required")
            return self.handle_admin_user_detail(ctx, path.split("/")[-1])

        if method == "PATCH" and _match(path, "/api/v1/admin/users/{user_id}/status"):
            ctx = resolve_session(self.db, token)
            if not ctx:
                return self._error(401, "AUTH_SESSION_REQUIRED", "Authentication required")
            session = _session_by_token(self.db, token) if token else None
            if not session or not _valid_csrf(normalized, session):
                return self._error(403, "CSRF_TOKEN_INVALID", "CSRF token missing or invalid")
            return self.handle_admin_user_status(ctx, path.split("/")[-2], payload or {})

        if method == "PUT" and _match(path, "/api/v1/admin/users/{user_id}/roles"):
            ctx = resolve_session(self.db, token)
            if not ctx:
                return self._error(401, "AUTH_SESSION_REQUIRED", "Authentication required")
            session = _session_by_token(self.db, token) if token else None
            if not session or not _valid_csrf(normalized, session):
                return self._error(403, "CSRF_TOKEN_INVALID", "CSRF token missing or invalid")
            return self.handle_admin_user_roles(ctx, path.split("/")[-2], payload or {})

        if method == "GET" and path == "/api/v1/admin/roles":
            ctx = resolve_session(self.db, token)
            if not ctx:
                return self._error(401, "AUTH_SESSION_REQUIRED", "Authentication required")
            return self.handle_admin_roles(ctx)

        if method == "GET" and path == "/api/v1/admin/permissions":
            ctx = resolve_session(self.db, token)
            if not ctx:
                return self._error(401, "AUTH_SESSION_REQUIRED", "Authentication required")
            return self.handle_admin_permissions(ctx)

        if method == "GET" and path == "/api/v1/admin/sessions":
            ctx = resolve_session(self.db, token)
            if not ctx:
                return self._error(401, "AUTH_SESSION_REQUIRED", "Authentication required")
            return self.handle_admin_sessions(ctx)

        if method == "POST" and _match(path, "/api/v1/admin/sessions/{session_id}/revoke"):
            ctx = resolve_session(self.db, token)
            if not ctx:
                return self._error(401, "AUTH_SESSION_REQUIRED", "Authentication required")
            return self.handle_admin_session_revoke(ctx, path.split("/")[-1])

        if method == "GET" and path == "/api/v1/admin/audit":
            ctx = resolve_session(self.db, token)
            if not ctx:
                return self._error(401, "AUTH_SESSION_REQUIRED", "Authentication required")
            return self.handle_admin_audit(ctx)

        if method == "POST" and path == "/api/v1/admin/backup":
            ctx = resolve_session(self.db, token)
            if not ctx:
                return self._error(401, "AUTH_SESSION_REQUIRED", "Authentication required")
            return self.handle_backup(ctx)

        if method == "POST" and path == "/api/v1/admin/restore-test":
            ctx = resolve_session(self.db, token)
            if not ctx:
                return self._error(401, "AUTH_SESSION_REQUIRED", "Authentication required")
            return self.handle_restore_test(ctx, payload or {})

        return self._error(404, "ROUTE_NOT_FOUND", "Route not found")


# ---------------------------------------------------------------------------
# Module-level utilities used above
# ---------------------------------------------------------------------------
def _now_utc() -> str:
    return __import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _match(path: str, pattern: str) -> bool:
    parts = path.split("/")
    pat_parts = pattern.split("/")
    if len(parts) != len(pat_parts):
        return False
    return all(pp.startswith("{") and pp.endswith("}") or p == pp for p, pp in zip(parts, pat_parts))


def _bearer_token(headers: dict[str, str]) -> str | None:
    auth = headers.get("authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:]
    return headers.get("x-session-token")


def _session_by_token(db: Database, token: str) -> dict[str, Any] | None:
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return db.fetchone("SELECT * FROM sessions WHERE token_hash = ?", (token_hash,))


def _valid_csrf(headers: dict[str, str], session: dict[str, Any]) -> bool:
    provided = headers.get("x-csrf-token")
    if not provided:
        return False
    provided_hash = hashlib.sha256(provided.encode("utf-8")).hexdigest()
    return hmac.compare_digest(provided_hash, session["csrf_token_hash"])


def _safe_user(user: dict[str, Any]) -> dict[str, Any]:
    out = dict(user)
    out.pop("password_hash", None)
    return out


def _safe_session(session: dict[str, Any]) -> dict[str, Any]:
    out = dict(session)
    out.pop("token_hash", None)
    out.pop("csrf_token_hash", None)
    return out


def get_user_roles(db: Database, user_id: str) -> list[str]:
    rows = db.fetchall("SELECT r.name FROM roles r JOIN user_roles ur ON ur.role_id = r.id WHERE ur.user_id = ?", (user_id,))
    return [r["name"] for r in rows]


def list_users(db: Database, *, limit: int = 50, offset: int = 0, status: str | None = None,
               sort: str = "username_display", order: str = "asc") -> list[dict[str, Any]]:
    allowed_sort = {"username_display", "created_at_utc", "status"}
    if sort not in allowed_sort:
        sort = "username_display"
    order = "DESC" if order.lower() == "desc" else "ASC"
    limit = max(1, min(limit, 200))
    sql = "SELECT * FROM users"
    params: list[Any] = []
    if status:
        sql += " WHERE status = ?"
        params.append(status)
    sql += f" ORDER BY {sort} {order} LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    return db.fetchall(sql, tuple(params))


def _safe_status(value: str) -> str:
    return value if value in {"active", "disabled", "locked"} else "active"


def _is_last_active_super_admin(db: Database, user_id: str) -> bool:
    row = db.fetchone(
        """
        SELECT COUNT(*) AS c FROM users u
        JOIN user_roles ur ON ur.user_id = u.id
        JOIN roles r ON r.id = ur.role_id
        WHERE u.status='active' AND r.name='super_admin'
        """
    )
    return int(row["c"]) <= 1 if row else False


_ALL_ROLES = {"super_admin", "security_admin", "compliance_admin", "operations_admin", "support_admin", "auditor", "viewer"}
