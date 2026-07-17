"""
SSID-EMS user and session repositories.

All queries parameterized. No string concatenation in SQL.
Hashes (password, token, csrf, source) stored only — never plaintext.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from backend.app import config
from backend.app.audit import record_event
from backend.app.password import hash_password, verify_password
from backend.app.persistence import PersistentStore
from backend.app.rbac_matrix import ROLE_PERMISSIONS


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _normalize(username: str) -> str:
    return username.strip().lower()


# --- users ---------------------------------------------------------------
def create_user(store: PersistentStore, username: str, password: str, *, actor_id: str = "system",
                actor_role: str = "bootstrap", roles: list[str] | None = None) -> dict:
    uname_norm = _normalize(username)
    uname_disp = username.strip()
    pw_hash = hash_password(password)
    user_id = "usr_" + secrets.token_hex(12)
    now = _now_utc()
    with store.connection() as conn:
        conn.execute(
            """
            INSERT INTO users (id, username_normalized, username_display, password_hash,
                               status, created_at_utc, updated_at_utc)
            VALUES (?, ?, ?, ?, 'active', ?, ?)
            """,
            (user_id, uname_norm, uname_disp, pw_hash, now, now),
        )
        if roles:
            for role in roles:
                _assign_role(conn, user_id, role, actor_id, "initial assignment")
    record_event(store, "user.created", actor_id, actor_role, "user", user_id, "success",
                 payload={"username_normalized": uname_norm, "roles": roles or []})
    return get_user_by_id(store, user_id)


def get_user_by_username(store: PersistentStore, username: str) -> dict | None:
    with store.connection() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username_normalized = ?", (_normalize(username),)
        ).fetchone()
    return dict(row) if row else None


def get_user_by_id(store: PersistentStore, user_id: str) -> dict | None:
    with store.connection() as conn:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(row) if row else None


def list_users(store: PersistentStore, *, limit: int = 50, offset: int = 0, status: str | None = None,
                sort: str = "username_display", order: str = "asc") -> list[dict]:
    allowed_sort = {"username_display", "created_at_utc", "status"}
    if sort not in allowed_sort:
        sort = "username_display"
    order = "DESC" if order.lower() == "desc" else "ASC"
    limit = max(1, min(limit, 200))
    sql = f"SELECT * FROM users"
    params: list = []
    if status:
        sql += " WHERE status = ?"
        params.append(status)
    sql += f" ORDER BY {sort} {order} LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    with store.connection() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def set_user_status(store: PersistentStore, user_id: str, status: str, *, actor_id: str,
                    actor_role: str, reason: str = "") -> dict:
    now = _now_utc()
    disabled_at = now if status == "disabled" else None
    with store.connection() as conn:
        conn.execute(
            "UPDATE users SET status = ?, updated_at_utc = ?, disabled_at_utc = ? WHERE id = ?",
            (status, now, disabled_at, user_id),
        )
    record_event(store, "user.status.changed", actor_id, actor_role, "user", user_id, "success",
                 reason=reason, payload={"status": status})
    return get_user_by_id(store, user_id)


def count_users(store: PersistentStore) -> int:
    with store.connection() as conn:
        row = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()
    return int(row["c"])


def count_active_super_admins(store: PersistentStore) -> int:
    with store.connection() as conn:
        row = conn.execute(
            """
            SELECT COUNT(*) AS c FROM users u
            JOIN user_roles ur ON ur.user_id = u.id
            JOIN roles r ON r.id = ur.role_id
            WHERE u.status = 'active' AND r.name = 'super_admin'
            """
        ).fetchone()
    return int(row["c"])


# --- roles ---------------------------------------------------------------
def _assign_role(conn, user_id: str, role_name: str, actor_id: str, reason: str) -> None:
    rid = conn.execute("SELECT id FROM roles WHERE name = ?", (role_name,)).fetchone()
    if not rid:
        return
    conn.execute(
        """
        INSERT OR IGNORE INTO user_roles (user_id, role_id)
        VALUES (?, ?)
        """,
        (user_id, rid["id"]),
    )


def assign_roles(store: PersistentStore, user_id: str, role_names: list[str], *, actor_id: str,
                 actor_role: str, reason: str = "") -> None:
    with store.connection() as conn:
        for role in role_names:
            _assign_role(conn, user_id, role, actor_id, reason)
    record_event(store, "user.roles.changed", actor_id, actor_role, "user", user_id, "success",
                 reason=reason, payload={"roles": role_names})


def get_user_roles(store: PersistentStore, user_id: str) -> list[str]:
    with store.connection() as conn:
        rows = conn.execute(
            """
            SELECT r.name FROM roles r
            JOIN user_roles ur ON ur.role_id = r.id
            WHERE ur.user_id = ?
            """,
            (user_id,),
        ).fetchall()
    return [r["name"] for r in rows]


def list_roles(store: PersistentStore) -> list[dict]:
    with store.connection() as conn:
        rows = conn.execute("SELECT * FROM roles ORDER BY name").fetchall()
    return [dict(r) for r in rows]


def list_permissions(store: PersistentStore) -> list[dict]:
    with store.connection() as conn:
        rows = conn.execute("SELECT * FROM permissions ORDER BY name").fetchall()
    return [dict(r) for r in rows]


# --- sessions ------------------------------------------------------------
def create_session(store: PersistentStore, user: dict, *, source_hash: str, user_agent_hash: str) -> dict:
    session_id = secrets.token_urlsafe(32)
    token = secrets.token_urlsafe(32)
    csrf = secrets.token_urlsafe(32)
    import hashlib
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    csrf_hash = hashlib.sha256(csrf.encode("utf-8")).hexdigest()
    now = _now_utc()
    expires = (datetime.now(timezone.utc) + timedelta(seconds=config.EMS_SESSION_TTL_SECONDS)).strftime("%Y-%m-%dT%H:%M:%SZ")
    with store.connection() as conn:
        conn.execute(
            """
            INSERT INTO sessions (id, user_id, token_hash, csrf_token_hash, created_at_utc,
                                  expires_at_utc, last_seen_at_utc, source_hash, user_agent_hash, session_version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (session_id, user["id"], token_hash, csrf_hash, now, expires, now, source_hash, user_agent_hash, user["session_version"]),
        )
    return {"session_id": session_id, "token": token, "csrf_token": csrf}


def get_session_by_token(store: PersistentStore, token: str) -> dict | None:
    import hashlib
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    with store.connection() as conn:
        row = conn.execute("SELECT * FROM sessions WHERE token_hash = ?", (token_hash,)).fetchone()
        if not row:
            return None
        s = dict(row)
        user = conn.execute("SELECT * FROM users WHERE id = ?", (s["user_id"],)).fetchone()
    if not user:
        return None
    now = datetime.now(timezone.utc)
    expires = datetime.strptime(s["expires_at_utc"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    if s["revoked_at_utc"]:
        return {**s, "user": dict(user), "state": "revoked"}
    if expires < now:
        return {**s, "user": dict(user), "state": "expired"}
    return {**s, "user": dict(user), "state": "active"}


def verify_csrf(store: PersistentStore, session_id: str, csrf_token: str) -> bool:
    import hashlib
    csrf_hash = hashlib.sha256(csrf_token.encode("utf-8")).hexdigest()
    with store.connection() as conn:
        row = conn.execute("SELECT csrf_token_hash FROM sessions WHERE id = ?", (session_id,)).fetchone()
    if not row:
        return False
    return hmac.compare_digest(csrf_hash, row["csrf_token_hash"])


def revoke_session(store: PersistentStore, session_id: str, *, actor_id: str, actor_role: str,
                   reason: str = "") -> bool:
    now = _now_utc()
    with store.connection() as conn:
        cur = conn.execute("UPDATE sessions SET revoked_at_utc = ? WHERE id = ? AND revoked_at_utc IS NULL",
                           (now, session_id))
        affected = cur.rowcount
    if affected:
        record_event(store, "auth.session.revoked", actor_id, actor_role, "session", session_id, "success",
                     reason=reason)
    return affected > 0


def list_sessions(store: PersistentStore, *, limit: int = 50, offset: int = 0) -> list[dict]:
    limit = max(1, min(limit, 200))
    with store.connection() as conn:
        rows = conn.execute(
            "SELECT * FROM sessions ORDER BY created_at_utc DESC LIMIT ? OFFSET ?", (limit, offset)
        ).fetchall()
    return [dict(r) for r in rows]


def touch_session(store: PersistentStore, session_id: str) -> None:
    now = _now_utc()
    with store.connection() as conn:
        conn.execute("UPDATE sessions SET last_seen_at_utc = ? WHERE id = ?", (now, session_id))


def rotate_user_sessions(store: PersistentStore, user_id: str, *, actor_id: str, actor_role: str,
                         reason: str = "security rotation") -> None:
    now = _now_utc()
    with store.connection() as conn:
        conn.execute("UPDATE sessions SET revoked_at_utc = ? WHERE user_id = ? AND revoked_at_utc IS NULL",
                     (now, user_id))
    record_event(store, "auth.session.revoked", actor_id, actor_role, "user", user_id, "success",
                 reason=reason)


def record_login_attempt(store: PersistentStore, username: str, source_hash: str, success: bool,
                         reason: str = "") -> None:
    attempt_id = "la_" + secrets.token_hex(12)
    now = _now_utc()
    with store.connection() as conn:
        conn.execute(
            """
            INSERT INTO login_attempts (id, username_normalized, source_hash, success, attempted_at_utc, reason)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (attempt_id, _normalize(username), source_hash, 1 if success else 0, now, reason),
        )
