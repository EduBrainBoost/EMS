"""
SSID-EMS Backend Configuration

Operational hardening phase (Phase 2/3): production-grade, stdlib-only.
No secrets. No .env. No provider configs committed.
"""

from __future__ import annotations

import os
from pathlib import Path

EMS_FRONTEND_PORT: int = 3100
EMS_BACKEND_PORT: int = 8100
FORBIDDEN_PORTS: list[int] = [3000, 3001, 3002, 3210, 5173, 4321, 8000]
ENV_MODE: str = os.environ.get("EMS_ENV_MODE", "local_scaffold")
START_SERVICES: bool = False
SERVICE_NAME: str = "SSID-EMS"
VERSION: str = "0.1.0-scaffold"

# --- Persistence ---------------------------------------------------------
_STATE_ROOT = Path(os.environ.get("EMS_STATE_ROOT", str(Path(__file__).resolve().parents[2] / "state")))
EMS_DATABASE_PATH: str = os.environ.get("EMS_DATABASE_PATH", str(_STATE_ROOT / "ems.db"))

# --- Demo auth gate ------------------------------------------------------
# Demo credentials are ONLY permitted in development/test. Production startup
# fails when demo auth is enabled.
EMS_DEMO_AUTH_ENABLED: bool = os.environ.get("EMS_DEMO_AUTH", "0") in ("1", "true", "True")
EMS_ALLOW_DEMO_IN_PRODUCTION: bool = os.environ.get("EMS_ALLOW_DEMO_IN_PRODUCTION", "0") in ("1", "true", "True")

# --- CORS ----------------------------------------------------------------
EMS_CORS_ALLOWED_ORIGINS: list[str] = [
    o.strip()
    for o in os.environ.get(
        "EMS_CORS_ALLOWED_ORIGINS",
        "http://127.0.0.1:3100,http://localhost:3100",
    ).split(",")
    if o.strip()
]

# --- Session -------------------------------------------------------------
EMS_SESSION_TTL_SECONDS: int = int(os.environ.get("EMS_SESSION_TTL_SECONDS", "3600"))
EMS_SECURE_COOKIES: bool = os.environ.get("EMS_SECURE_COOKIES", "0") in ("1", "true", "True")
EMS_COOKIE_SAMESITE: str = os.environ.get("EMS_COOKIE_SAMESITE", "Lax")

# --- Password hashing (scrypt) ------------------------------------------
EMS_SCRYPT_N: int = int(os.environ.get("EMS_SCRYPT_N", "16384"))
EMS_SCRYPT_R: int = int(os.environ.get("EMS_SCRYPT_R", "8"))
EMS_SCRYPT_P: int = int(os.environ.get("EMS_SCRYPT_P", "1"))
EMS_SCRYPT_MAXMEM: int = int(os.environ.get("EMS_SCRYPT_MAXMEM", str(64 * 1024 * 1024)))
EMS_SCRYPT_KEYLEN: int = int(os.environ.get("EMS_SCRYPT_KEYLEN", "64"))

# --- Rate limiting -------------------------------------------------------
EMS_LOGIN_RATE_LIMIT: int = int(os.environ.get("EMS_LOGIN_RATE_LIMIT", "5"))
EMS_LOGIN_RATE_WINDOW_SECONDS: int = int(os.environ.get("EMS_LOGIN_RATE_WINDOW_SECONDS", "300"))
EMS_API_RATE_LIMIT: int = int(os.environ.get("EMS_API_RATE_LIMIT", "120"))
EMS_API_RATE_WINDOW_SECONDS: int = int(os.environ.get("EMS_API_RATE_WINDOW_SECONDS", "60"))
EMS_ADMIN_RATE_LIMIT: int = int(os.environ.get("EMS_ADMIN_RATE_LIMIT", "30"))
EMS_ADMIN_RATE_WINDOW_SECONDS: int = int(os.environ.get("EMS_ADMIN_RATE_WINDOW_SECONDS", "60"))

# --- Minimum password policy --------------------------------------------
EMS_MIN_PASSWORD_LENGTH: int = int(os.environ.get("EMS_MIN_PASSWORD_LENGTH", "12"))


def validate_ports() -> dict:
    """
    Ensures configured ports are not in the forbidden list.
    Returns a status dict for audit/evidence.
    """
    violations = []
    for port in (EMS_FRONTEND_PORT, EMS_BACKEND_PORT):
        if port in FORBIDDEN_PORTS:
            violations.append(port)
    return {
        "frontend_port": EMS_FRONTEND_PORT,
        "backend_port": EMS_BACKEND_PORT,
        "forbidden_ports": FORBIDDEN_PORTS,
        "violations": violations,
        "valid": len(violations) == 0,
    }


def is_production() -> bool:
    return ENV_MODE in ("production", "prod")


# --- Operational hardening env vars (Phase 2/3) --------------------------
# These defaults preserve existing scaffold behavior.
EMS_DEMO_AUTH_ENABLED: bool = os.environ.get("EMS_DEMO_AUTH", "0") in ("1", "true", "True")
EMS_ALLOW_DEMO_IN_PRODUCTION: bool = os.environ.get("EMS_ALLOW_DEMO_IN_PRODUCTION", "0") in ("1", "true", "True")
EMS_CORS_ALLOWED_ORIGINS: list[str] = [
    o.strip()
    for o in os.environ.get(
        "EMS_CORS_ALLOWED_ORIGINS",
        "http://127.0.0.1:3100,http://localhost:3100",
    ).split(",")
    if o.strip()
]
EMS_SESSION_TTL_SECONDS: int = int(os.environ.get("EMS_SESSION_TTL_SECONDS", "3600"))
EMS_SECURE_COOKIES: bool = os.environ.get("EMS_SECURE_COOKIES", "0") in ("1", "true", "True")
EMS_COOKIE_SAMESITE: str = os.environ.get("EMS_COOKIE_SAMESITE", "Lax")
EMS_SCRYPT_N: int = int(os.environ.get("EMS_SCRYPT_N", "16384"))
EMS_SCRYPT_R: int = int(os.environ.get("EMS_SCRYPT_R", "8"))
EMS_SCRYPT_P: int = int(os.environ.get("EMS_SCRYPT_P", "1"))
EMS_SCRYPT_MAXMEM: int = int(os.environ.get("EMS_SCRYPT_MAXMEM", str(64 * 1024 * 1024)))
EMS_SCRYPT_KEYLEN: int = int(os.environ.get("EMS_SCRYPT_KEYLEN", "64"))
EMS_LOGIN_RATE_LIMIT: int = int(os.environ.get("EMS_LOGIN_RATE_LIMIT", "5"))
EMS_LOGIN_RATE_WINDOW_SECONDS: int = int(os.environ.get("EMS_LOGIN_RATE_WINDOW_SECONDS", "300"))
EMS_API_RATE_LIMIT: int = int(os.environ.get("EMS_API_RATE_LIMIT", "120"))
EMS_API_RATE_WINDOW_SECONDS: int = int(os.environ.get("EMS_API_RATE_WINDOW_SECONDS", "60"))
EMS_ADMIN_RATE_LIMIT: int = int(os.environ.get("EMS_ADMIN_RATE_LIMIT", "30"))
EMS_ADMIN_RATE_WINDOW_SECONDS: int = int(os.environ.get("EMS_ADMIN_RATE_WINDOW_SECONDS", "60"))
EMS_MIN_PASSWORD_LENGTH: int = int(os.environ.get("EMS_MIN_PASSWORD_LENGTH", "12"))
_STATE_ROOT = Path(os.environ.get("EMS_STATE_ROOT", str(Path(__file__).resolve().parents[2] / "state")))
EMS_DATABASE_PATH: str = os.environ.get("EMS_DATABASE_PATH", str(_STATE_ROOT / "ems.db"))
