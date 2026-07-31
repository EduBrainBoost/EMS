"""
SSID-EMS RBAC enforcement engine.

Deny by default. Backend is the single source of enforcement. No implicit
permission via login. Guards used by the HTTP layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


@dataclass
class AuthContext:
    """Resolved identity for the current request."""

    user_id: str
    username: str
    roles: list[str] = field(default_factory=list)
    permissions: set[str] = field(default_factory=set)
    session_id: str | None = None
    authenticated: bool = False


class RBACError(Exception):
    def __init__(self, status_code: int, error_code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code
        self.message = message


def load_permissions_for_roles(store, roles: Iterable[str]) -> set[str]:
    perms: set[str] = set()
    with store.connection() as conn:
        for role in roles:
            rows = conn.execute(
                """
                SELECT p.name
                FROM roles r
                JOIN role_permissions rp ON rp.role_id = r.id
                JOIN permissions p ON p.id = rp.permission_id
                WHERE r.name = ?
                """,
                (role,),
            ).fetchall()
            perms.update(r["name"] for r in rows)
    return perms


def build_context(store, user: dict, session_id: str | None = None) -> AuthContext:
    with store.connection() as conn:
        role_rows = conn.execute(
            """
            SELECT r.name FROM roles r
            JOIN user_roles ur ON ur.role_id = r.id
            WHERE ur.user_id = ?
            """,
            (user["id"],),
        ).fetchall()
    roles = [r["name"] for r in role_rows]
    perms = load_permissions_for_roles(store, roles)
    return AuthContext(
        user_id=user["id"],
        username=user["username_display"],
        roles=roles,
        permissions=perms,
        session_id=session_id,
        authenticated=True,
    )


def require_authenticated_user(ctx: AuthContext | None) -> AuthContext:
    if ctx is None or not ctx.authenticated:
        raise RBACError(401, "AUTH_SESSION_REQUIRED", "Authentication required")
    return ctx


def require_permission(store, ctx: AuthContext, permission: str) -> AuthContext:
    require_authenticated_user(ctx)
    if permission not in ctx.permissions:
        # Audit the denied attempt at the call site; here we raise.
        raise RBACError(403, "AUTH_PERMISSION_DENIED", f"Missing permission: {permission}")
    return ctx


def require_any_permission(store, ctx: AuthContext, permissions: Iterable[str]) -> AuthContext:
    require_authenticated_user(ctx)
    if not any(p in ctx.permissions for p in permissions):
        raise RBACError(403, "AUTH_PERMISSION_DENIED", "Missing required permission")
    return ctx


def require_role(ctx: AuthContext, role: str) -> AuthContext:
    require_authenticated_user(ctx)
    if role not in ctx.roles:
        raise RBACError(403, "AUTH_ROLE_DENIED", f"Missing role: {role}")
    return ctx


def require_admin_session(ctx: AuthContext) -> AuthContext:
    return require_any_permission(None, ctx, {"roles.manage", "users.manage", "security.manage"})
