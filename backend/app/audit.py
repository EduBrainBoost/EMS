"""
SSID-EMS append-only hash-chained audit log.

Each event is SHA256-chained over a canonical JSON payload. Tampering with any
stored event (or its previous_hash) breaks the chain and fails verification.

No passwords, cookies, session tokens, or CSRF tokens in payloads.
"""

from __future__ import annotations

import hashlib
import json
import secrets
from datetime import datetime, timezone
from typing import Any

from backend.app.persistence import PersistentStore, ZERO_HASH

ZERO_HASH_REF = ZERO_HASH


def _now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _canonical(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _redact(payload: dict[str, Any]) -> dict[str, Any]:
    """Remove any sensitive keys before storing."""
    blocked = {
        "password", "password_hash", "session_token", "session_cookie",
        "csrf_token", "authorization", "cookie", "set_cookie",
        "token", "secret",
    }
    cleaned = {}
    for k, v in payload.items():
        if k.lower() in blocked:
            cleaned[k] = "[REDACTED]"
        else:
            cleaned[k] = v
    return cleaned


def _event_hash(event: dict[str, Any]) -> str:
    canonical = _canonical(
        {
            "sequence_number": event["sequence_number"],
            "event_id": event["event_id"],
            "timestamp_utc": event["timestamp_utc"],
            "actor_id": event["actor_id"],
            "action": event["action"],
            "resource_type": event["resource_type"],
            "resource_id": event["resource_id"],
            "result": event["result"],
            "request_id": event["request_id"],
            "previous_hash": event["previous_hash"],
            "canonical_payload": event["canonical_payload"],
        }
    )
    return hashlib.sha256(canonical).hexdigest()


def record_event(
    store: PersistentStore,
    action: str,
    actor_id: str,
    actor_role: str,
    resource_type: str,
    resource_id: str,
    result: str,
    *,reason: str = "",
    request_id: str = "",
    correlation_id: str = "",
    source_service: str = "ssid-ems",
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Append a hash-chained audit event inside its own transaction."""
    payload = payload or {}
    safe_payload = _redact(payload)
    with store.connection() as conn:
        last = conn.execute(
            "SELECT event_hash FROM audit_events ORDER BY sequence_number DESC LIMIT 1"
        ).fetchone()
        previous_hash = last["event_hash"] if last else ZERO_HASH
        event_id = "aud_" + secrets.token_hex(16)
        event = {
            "event_id": event_id,
            "timestamp_utc": _now_utc(),
            "actor_id": actor_id,
            "actor_role": actor_role,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "result": result,
            "reason": reason,
            "request_id": request_id,
            "correlation_id": correlation_id,
            "source_service": source_service,
            "previous_hash": previous_hash,
            "canonical_payload": _canonical(safe_payload).decode("utf-8"),
        }
        cursor = conn.execute(
            """
            INSERT INTO audit_events (
                event_id, timestamp_utc, actor_id, actor_role, action,
                resource_type, resource_id, result, reason, request_id,
                correlation_id, source_service, previous_hash, event_hash, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event["event_id"],
                event["timestamp_utc"],
                event["actor_id"],
                event["actor_role"],
                event["action"],
                event["resource_type"],
                event["resource_id"],
                event["result"],
                event["reason"],
                event["request_id"],
                event["correlation_id"],
                event["source_service"],
                event["previous_hash"],
                "",  # filled after hash
                json.dumps(safe_payload, sort_keys=True),
            ),
        )
        seq = cursor.lastrowid
        event["sequence_number"] = seq
        event_hash = _event_hash(event)
        conn.execute(
            "UPDATE audit_events SET event_hash = ? WHERE sequence_number = ?",
            (event_hash, seq),
        )
    event["event_hash"] = event_hash
    return event


def verify_chain(store: PersistentStore) -> dict[str, Any]:
    """Walk the chain and confirm every event_hash is valid and links correctly."""
    with store.connection() as conn:
        rows = conn.execute(
            "SELECT sequence_number, event_id, timestamp_utc, actor_id, action, "
            "resource_type, resource_id, result, request_id, previous_hash, "
            "event_hash, payload_json FROM audit_events ORDER BY sequence_number ASC"
        ).fetchall()
    previous_hash = ZERO_HASH
    chain_valid = True
    last_hash = ZERO_HASH
    for r in rows:
        payload = json.loads(r["payload_json"])
        event = {
            "sequence_number": r["sequence_number"],
            "event_id": r["event_id"],
            "timestamp_utc": r["timestamp_utc"],
            "actor_id": r["actor_id"],
            "action": r["action"],
            "resource_type": r["resource_type"],
            "resource_id": r["resource_id"],
            "result": r["result"],
            "request_id": r["request_id"],
            "previous_hash": r["previous_hash"],
            "canonical_payload": _canonical(payload).decode("utf-8"),
        }
        computed = _event_hash(event)
        if computed != r["event_hash"] or r["previous_hash"] != previous_hash:
            chain_valid = False
        previous_hash = r["event_hash"]
        last_hash = r["event_hash"]
    return {
        "event_count": len(rows),
        "first_event_id": rows[0]["event_id"] if rows else None,
        "last_event_id": rows[-1]["event_id"] if rows else None,
        "last_event_hash": last_hash,
        "chain_valid": chain_valid,
    }
