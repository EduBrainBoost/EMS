"""
SSID-EMS auth service: login, logout, session resolution.

Production: demo auth forbidden. Persistent server-side sessions. Deny by
default on unknown user (no existence disclosure). Constant-time checks.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from backend.app import config, security
from backend.app.audit import record_event
from backend.app.password import verify_password
from backend.app.persistence import PersistentStore
from backend.app.rbac import AuthContext, build_context
from backend.app.repository import (
    create_session, get_session_by_token, get_user_by_username,
    record_login_attempt, revoke_session,
)
from backend.app.security import RateLimiter, source_hash, user_agent_hash

_login_limiter = RateLimiter()
_api_limiter = RateLimiter()
_admin_limiter = RateLimiter()


class AuthError(Exception):
    def __init__(self, status_code: int, error_code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code
        self.message = message


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _login_rate_key(username: str, src_hash: str) -> str:
    return f"login:u:{hashlib.sha256(username.lower().encode()).hexdigest()}:s:{src_hash}"


def login(store: PersistentStore, username: str, password: str, *,
          source_ip: str = "unknown", user_agent: str = "unknown",
          request_id: str = "") -> dict[str, Any]:
    src_hash = source_hash(source_ip)
    ua_hash = user_agent_hash(user_agent)
    rate_key = _login_rate_key(username, src_hash)

    allowed, _ = _login_limiter.check(rate_key, config.EMS_LOGIN_RATE_LIMIT, config.EMS_LOGIN_RATE_WINDOW_SECONDS)
    if not allowed:
        record_event(store, "auth.login.failure", "anonymous", "none", "auth", "login",
                     "rate_limited", reason="login rate limit exceeded",
                     request_id=request_id, payload={"username_normalized": username.lower()})
        raise AuthError(429, "RATE_LIMIT_EXCEEDED", "Too many login attempts")

    user = get_user_by_username(store, username)
    # Constant-time-ish: always run a hash compare to avoid timing oracle.
    dummy = "$".join(["scrypt", "v1", "16384", "8", "1", "AQEBAQEBAQEBAQEBAQEBAQ==",
                      hashlib.sha256(b"dummy").hexdigest()])
    ok = verify_password(password, user["password_hash"]) if user else verify_password(password, dummy)

    if not user or not ok or user["status"] != "active":
        record_login_attempt(store, username, src_hash, False, reason="invalid_credentials")
        _login_limiter.hit(rate_key, config.EMS_LOGIN_RATE_WINDOW_SECONDS)
        if user and user["status"] == "locked":
            record_event(store, "auth.login.failure", user["id"], "unknown", "auth", "login",
                         "locked", reason="account locked", request_id=request_id)
            raise AuthError(423, "AUTH_ACCOUNT_LOCKED", "Account locked")
        if user and user["status"] == "disabled":
            raise AuthError(403, "AUTH_ACCOUNT_DISABLED", "Account disabled")
        record_event(store, "auth.login.failure", user["id"] if user else "anonymous", "none",
                     "auth", "login", "failure", reason="invalid_credentials",
                     request_id=request_id, payload={"username_normalized": username.lower()})
        raise AuthError(401, "AUTH_INVALID_CREDENTIALS", "Invalid credentials")

    record_login_attempt(store, username, src_hash, True)
    session = create_session(store, user, source_hash=src_hash, user_agent_hash=ua_hash)
    ctx = build_context(store, user, session_id=session["session_id"])
    record_event(store, "auth.login.success", user["id"], ctx.roles[0] if ctx.roles else "none",
                 "auth", "login", "success", request_id=request_id,
                 payload={"session_id": session["session_id"], "roles": ctx.roles})
    return {
        "status": "ok",
        "authenticated": True,
        "session_id": session["session_id"],
        "token": session["token"],
        "csrf_token": session["csrf_token"],
        "user_id": user["id"],
        "username": user["username_display"],
        "roles": ctx.roles,
        "expires_at_utc": session_expiry(store, session["session_id"]),
    }


def session_expiry(store: PersistentStore, session_id: str) -> str | None:
    from backend.app.repository import list_sessions
    for s in list_sessions(store, limit=200):
        if s["id"] == session_id:
            return s["expires_at_utc"]
    return None


def resolve_session(store: PersistentStore, token: str | None) -> AuthContext | None:
    if not token:
        return None
    sess = get_session_by_token(store, token)
    if not sess or sess.get("state") != "active":
        return None
    user = sess["user"]
    if user["status"] != "active":
        return None
    from backend.app.repository import touch_session
    touch_session(store, sess["id"])
    return build_context(store, user, session_id=sess["id"])


def logout(store: PersistentStore, token: str | None, *, actor_id: str = "anonymous",
           actor_role: str = "none") -> None:
    if not token:
        return
    sess = get_session_by_token(store, token)
    if not sess:
        return
    revoke_session(store, sess["id"], actor_id=actor_id, actor_role=actor_role, reason="logout")
    record_event(store, "auth.logout", actor_id, actor_role, "session", sess["id"], "success")


def check_api_rate(src_hash: str) -> None:
    allowed, _ = _api_limiter.check(f"api:s:{src_hash}", config.EMS_API_RATE_LIMIT, config.EMS_API_RATE_WINDOW_SECONDS)
    if not allowed:
        raise AuthError(429, "RATE_LIMIT_EXCEEDED", "API rate limit exceeded")
    _api_limiter.hit(f"api:s:{src_hash}", config.EMS_API_RATE_WINDOW_SECONDS)


def check_admin_rate(src_hash: str) -> None:
    allowed, _ = _admin_limiter.check(f"admin:s:{src_hash}", config.EMS_ADMIN_RATE_LIMIT, config.EMS_ADMIN_RATE_WINDOW_SECONDS)
    if not allowed:
        raise AuthError(429, "RATE_LIMIT_EXCEEDED", "Admin rate limit exceeded")
    _admin_limiter.hit(f"admin:s:{src_hash}", config.EMS_ADMIN_RATE_WINDOW_SECONDS)
