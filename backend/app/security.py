"""
SSID-EMS security controls: CORS, CSRF, rate limiting.

All stdlib. No wildcards. Origin allowlist only. Source hashes, no plaintext IP.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from typing import Any

from backend.app import config


# --- CORS -----------------------------------------------------------------
ALLOWED_HEADERS = ["Content-Type", "X-CSRF-Token", "X-Request-ID", "X-Correlation-ID"]
EXPOSED_HEADERS = ["X-Request-ID", "X-Correlation-ID"]
ALLOWED_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]


def normalize_origin(origin: str | None) -> str | None:
    if not origin:
        return None
    return origin.strip()


def is_origin_allowed(origin: str | None) -> bool:
    if origin is None:
        return False
    if origin == "null":
        return False
    # No wildcard in production; allowlist only.
    return origin in config.EMS_CORS_ALLOWED_ORIGINS


def cors_headers(origin: str | None) -> dict[str, str]:
    """Return CORS response headers for an allowed origin, empty otherwise."""
    headers: dict[str, str] = {}
    if is_origin_allowed(origin):
        headers["Access-Control-Allow-Origin"] = origin  # reflected only from allowlist
        headers["Access-Control-Allow-Methods"] = ", ".join(ALLOWED_METHODS)
        headers["Access-Control-Allow-Headers"] = ", ".join(ALLOWED_HEADERS)
        headers["Access-Control-Expose-Headers"] = ", ".join(EXPOSED_HEADERS)
        headers["Access-Control-Max-Age"] = "600"
        headers["Vary"] = "Origin"
        if "Authorization" in config.EMS_CORS_ALLOWED_ORIGINS:
            pass  # authorization added only if actually used; not in allowlist form
    return headers


# --- CSRF -----------------------------------------------------------------
def new_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def csrf_matches(provided: str | None, expected_hash: str) -> bool:
    if not provided:
        return False
    import hashlib
    provided_hash = hashlib.sha256(provided.encode("utf-8")).hexdigest()
    return hmac.compare_digest(provided_hash, expected_hash)


# --- Rate limiting --------------------------------------------------------
class RateLimiter:
    """In-memory sliding-window limiter. Persistent login attempts are also
    recorded in the DB; this is the supplementary fast path."""

    def __init__(self) -> None:
        self._buckets: dict[str, list[float]] = {}
        self._lock = __import__("threading").Lock()

    def _trim(self, key: str, window: int) -> list[float]:
        now = time.time()
        bucket = [t for t in self._buckets.get(key, []) if now - t < window]
        self._buckets[key] = bucket
        return bucket

    def check(self, key: str, limit: int, window: int) -> tuple[bool, int]:
        with self._lock:
            bucket = self._trim(key, window)
            remaining = limit - len(bucket)
            return remaining > 0, max(0, remaining)

    def hit(self, key: str, window: int) -> None:
        with self._lock:
            bucket = self._trim(key, window)
            bucket.append(time.time())
            self._buckets[key] = bucket


def source_hash(identifier: str) -> str:
    """Hash a source identifier (IP/proxy) so plaintext is never stored."""
    return hashlib.sha256(identifier.encode("utf-8")).hexdigest()


def user_agent_hash(ua: str) -> str:
    return hashlib.sha256((ua or "unknown").encode("utf-8")).hexdigest()
