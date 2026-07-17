"""
SSID-EMS RBAC role->permission matrix.

Single source of truth for role grants. Seeded into the database
deterministically. Backend is the enforcement authority.
"""

from __future__ import annotations

# role_name -> set of permission names
ROLE_PERMISSIONS: dict[str, set[str]] = {
    "super_admin": {
        "system.read", "users.read", "users.manage", "roles.read", "roles.manage",
        "sessions.read", "sessions.revoke", "audit.read", "audit.export",
        "security.read", "security.manage", "compliance.read", "compliance.manage",
        "jobs.read", "jobs.manage", "providers.read", "providers.manage",
        "incidents.read", "incidents.manage", "registry.read", "registry.manage",
    },
    "security_admin": {
        "system.read", "users.read", "roles.read", "sessions.read", "sessions.revoke",
        "audit.read", "security.read", "security.manage", "compliance.read",
        "incidents.read", "incidents.manage", "registry.read",
    },
    "compliance_admin": {
        "system.read", "users.read", "roles.read", "audit.read", "audit.export",
        "compliance.read", "compliance.manage", "registry.read",
    },
    "operations_admin": {
        "system.read", "users.read", "roles.read", "sessions.read", "jobs.read",
        "jobs.manage", "providers.read", "providers.manage", "incidents.read",
        "incidents.manage", "registry.read", "registry.manage",
    },
    "support_admin": {
        "system.read", "users.read", "roles.read", "sessions.read", "sessions.revoke",
        "incidents.read", "incidents.manage",
    },
    "auditor": {
        "system.read", "users.read", "roles.read", "sessions.read", "audit.read",
        "audit.export", "compliance.read", "registry.read",
    },
    "viewer": {
        "system.read", "users.read", "roles.read", "audit.read", "registry.read",
    },
}

ALL_ROLES = list(ROLE_PERMISSIONS.keys())
ALL_PERMISSIONS = sorted(
    {p for perms in ROLE_PERMISSIONS.values() for p in perms}
)
