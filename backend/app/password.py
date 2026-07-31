"""
SSID-EMS password hashing — scrypt via stdlib hashlib.

Format: scrypt$v1$<n>$<r>$<p>$<salt_b64>$<hash_b64>
Random salt via secrets.token_bytes. Configurable cost. Constant-time verify.
No plaintext. No SHA256-only password hashes.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets

from backend.app import config

HASH_FORMAT = "scrypt"
HASH_VERSION = "v1"


def hash_password(password: str) -> str:
    """Return a versioned scrypt hash string for the given plaintext password."""
    if not isinstance(password, str) or not password:
        raise ValueError("password must be a non-empty string")
    salt = secrets.token_bytes(16)
    dk = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=config.EMS_SCRYPT_N,
        r=config.EMS_SCRYPT_R,
        p=config.EMS_SCRYPT_P,
        maxmem=config.EMS_SCRYPT_MAXMEM,
        dklen=config.EMS_SCRYPT_KEYLEN,
    )
    return _encode(salt, dk)


def _encode(salt: bytes, dk: bytes) -> str:
    return "$".join(
        [
            HASH_FORMAT,
            HASH_VERSION,
            str(config.EMS_SCRYPT_N),
            str(config.EMS_SCRYPT_R),
            str(config.EMS_SCRYPT_P),
            base64.b64encode(salt).decode("ascii"),
            base64.b64encode(dk).decode("ascii"),
        ]
    )


def verify_password(password: str, stored: str) -> bool:
    """Constant-time verification of a plaintext password against a stored hash."""
    try:
        parts = stored.split("$")
        if len(parts) != 7 or parts[0] != HASH_FORMAT or parts[1] != HASH_VERSION:
            return False
        n, r, p = int(parts[2]), int(parts[3]), int(parts[4])
        salt = base64.b64decode(parts[5])
        expected = base64.b64decode(parts[6])
        dk = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=n,
            r=r,
            p=p,
            maxmem=config.EMS_SCRYPT_MAXMEM,
            dklen=len(expected),
        )
        return hmac.compare_digest(dk, expected)
    except Exception:
        return False


def validate_password_strength(password: str) -> None:
    if not isinstance(password, str) or len(password) < config.EMS_MIN_PASSWORD_LENGTH:
        raise ValueError(
            f"password must be at least {config.EMS_MIN_PASSWORD_LENGTH} characters"
        )
