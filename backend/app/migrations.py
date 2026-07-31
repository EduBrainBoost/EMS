"""
SSID-EMS deterministic migration set.

Each migration is applied exactly once. Checksums are verified on every
startup to detect tampering or drift. No applied migration is ever altered:
changing SQL changes the checksum, which fails startup.
"""

from __future__ import annotations

import hashlib


def _checksum(sql: str) -> str:
    return hashlib.sha256(sql.encode("utf-8")).hexdigest()


MIGRATIONS: list[dict] = []


def _add(migration_id: str, sql: str) -> None:
    MIGRATIONS.append(
        {
            "migration_id": migration_id,
            "sql": sql,
            "checksum": _checksum(sql),
        }
    )


_add(
    "0001_core_schema",
    """
CREATE TABLE IF NOT EXISTS schema_migrations (
    migration_id TEXT PRIMARY KEY,
    checksum TEXT NOT NULL,
    applied_at_utc TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username_normalized TEXT NOT NULL UNIQUE,
    username_display TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    created_at_utc TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL,
    disabled_at_utc TEXT,
    session_version INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS roles (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    system_role BOOLEAN NOT NULL DEFAULT 0,
    created_at_utc TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS permissions (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE IF NOT EXISTS user_roles (
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id TEXT NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);

CREATE TABLE IF NOT EXISTS role_permissions (
    role_id TEXT NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id TEXT NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL,
    csrf_token_hash TEXT NOT NULL,
    created_at_utc TEXT NOT NULL,
    expires_at_utc TEXT NOT NULL,
    last_seen_at_utc TEXT NOT NULL,
    revoked_at_utc TEXT,
    source_hash TEXT NOT NULL,
    user_agent_hash TEXT NOT NULL,
    session_version INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS login_attempts (
    id TEXT PRIMARY KEY,
    username_normalized TEXT NOT NULL,
    source_hash TEXT NOT NULL,
    success BOOLEAN NOT NULL,
    attempted_at_utc TEXT NOT NULL,
    reason TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS audit_events (
    sequence_number INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL UNIQUE,
    timestamp_utc TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    actor_role TEXT NOT NULL,
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id TEXT NOT NULL,
    result TEXT NOT NULL,
    reason TEXT NOT NULL DEFAULT '',
    request_id TEXT NOT NULL DEFAULT '',
    correlation_id TEXT NOT NULL DEFAULT '',
    source_service TEXT NOT NULL DEFAULT 'ssid-ems',
    previous_hash TEXT NOT NULL,
    event_hash TEXT NOT NULL,
    payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS service_state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at_utc TEXT NOT NULL
);
    """,
)

# Record the initial schema version once core schema exists.
_add(
    "0002_schema_version_seed",
    """
INSERT INTO schema_migrations (migration_id, checksum, applied_at_utc)
SELECT 'v1_initial_schema', '', datetime('now')
WHERE NOT EXISTS (SELECT 1 FROM schema_migrations WHERE migration_id = 'v1_initial_schema');
    """,
)

# Seed system roles, permissions, and role->permission bindings.
_add(
    "0003_rbac_seed",
    """
INSERT INTO roles (id, name, description, system_role, created_at_utc) VALUES
('role_super_admin', 'super_admin', 'Full system control', 1, datetime('now')),
('role_security_admin', 'security_admin', 'Security administration', 1, datetime('now')),
('role_compliance_admin', 'compliance_admin', 'Compliance administration', 1, datetime('now')),
('role_operations_admin', 'operations_admin', 'Operations administration', 1, datetime('now')),
('role_support_admin', 'support_admin', 'Support administration', 1, datetime('now')),
('role_auditor', 'auditor', 'Read-only audit access', 1, datetime('now')),
('role_viewer', 'viewer', 'Read-only basic access', 1, datetime('now'))
ON CONFLICT(name) DO NOTHING;

INSERT INTO permissions (id, name, description) VALUES
('perm_system_read', 'system.read', 'Read system status'),
('perm_users_read', 'users.read', 'Read user directory'),
('perm_users_manage', 'users.manage', 'Create/disable users'),
('perm_roles_read', 'roles.read', 'Read roles'),
('perm_roles_manage', 'roles.manage', 'Manage role assignments'),
('perm_sessions_read', 'sessions.read', 'Read sessions'),
('perm_sessions_revoke', 'sessions.revoke', 'Revoke sessions'),
('perm_audit_read', 'audit.read', 'Read audit log'),
('perm_audit_export', 'audit.export', 'Export audit log'),
('perm_security_read', 'security.read', 'Read security config'),
('perm_security_manage', 'security.manage', 'Manage security config'),
('perm_compliance_read', 'compliance.read', 'Read compliance data'),
('perm_compliance_manage', 'compliance.manage', 'Manage compliance data'),
('perm_jobs_read', 'jobs.read', 'Read jobs'),
('perm_jobs_manage', 'jobs.manage', 'Manage jobs'),
('perm_providers_read', 'providers.read', 'Read providers'),
('perm_providers_manage', 'providers.manage', 'Manage providers'),
('perm_incidents_read', 'incidents.read', 'Read incidents'),
('perm_incidents_manage', 'incidents.manage', 'Manage incidents'),
('perm_registry_read', 'registry.read', 'Read registry'),
('perm_registry_manage', 'registry.manage', 'Manage registry')
ON CONFLICT(name) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id) VALUES
('role_super_admin', 'perm_system_read'),
('role_super_admin', 'perm_users_read'),
('role_super_admin', 'perm_users_manage'),
('role_super_admin', 'perm_roles_read'),
('role_super_admin', 'perm_roles_manage'),
('role_super_admin', 'perm_sessions_read'),
('role_super_admin', 'perm_sessions_revoke'),
('role_super_admin', 'perm_audit_read'),
('role_super_admin', 'perm_audit_export'),
('role_super_admin', 'perm_security_read'),
('role_super_admin', 'perm_security_manage'),
('role_super_admin', 'perm_compliance_read'),
('role_super_admin', 'perm_compliance_manage'),
('role_super_admin', 'perm_jobs_read'),
('role_super_admin', 'perm_jobs_manage'),
('role_super_admin', 'perm_providers_read'),
('role_super_admin', 'perm_providers_manage'),
('role_super_admin', 'perm_incidents_read'),
('role_super_admin', 'perm_incidents_manage'),
('role_super_admin', 'perm_registry_read'),
('role_super_admin', 'perm_registry_manage'),
('role_security_admin', 'perm_system_read'),
('role_security_admin', 'perm_users_read'),
('role_security_admin', 'perm_roles_read'),
('role_security_admin', 'perm_sessions_read'),
('role_security_admin', 'perm_sessions_revoke'),
('role_security_admin', 'perm_audit_read'),
('role_security_admin', 'perm_security_read'),
('role_security_admin', 'perm_security_manage'),
('role_security_admin', 'perm_compliance_read'),
('role_security_admin', 'perm_incidents_read'),
('role_security_admin', 'perm_incidents_manage'),
('role_security_admin', 'perm_registry_read'),
('role_compliance_admin', 'perm_system_read'),
('role_compliance_admin', 'perm_users_read'),
('role_compliance_admin', 'perm_roles_read'),
('role_compliance_admin', 'perm_audit_read'),
('role_compliance_admin', 'perm_audit_export'),
('role_compliance_admin', 'perm_compliance_read'),
('role_compliance_admin', 'perm_compliance_manage'),
('role_compliance_admin', 'perm_registry_read'),
('role_operations_admin', 'perm_system_read'),
('role_operations_admin', 'perm_users_read'),
('role_operations_admin', 'perm_roles_read'),
('role_operations_admin', 'perm_sessions_read'),
('role_operations_admin', 'perm_jobs_read'),
('role_operations_admin', 'perm_jobs_manage'),
('role_operations_admin', 'perm_providers_read'),
('role_operations_admin', 'perm_providers_manage'),
('role_operations_admin', 'perm_incidents_read'),
('role_operations_admin', 'perm_incidents_manage'),
('role_operations_admin', 'perm_registry_read'),
('role_operations_admin', 'perm_registry_manage'),
('role_support_admin', 'perm_system_read'),
('role_support_admin', 'perm_users_read'),
('role_support_admin', 'perm_roles_read'),
('role_support_admin', 'perm_sessions_read'),
('role_support_admin', 'perm_sessions_revoke'),
('role_support_admin', 'perm_incidents_read'),
('role_support_admin', 'perm_incidents_manage'),
('role_auditor', 'perm_system_read'),
('role_auditor', 'perm_users_read'),
('role_auditor', 'perm_roles_read'),
('role_auditor', 'perm_sessions_read'),
('role_auditor', 'perm_audit_read'),
('role_auditor', 'perm_audit_export'),
('role_auditor', 'perm_compliance_read'),
('role_auditor', 'perm_registry_read'),
('role_viewer', 'perm_system_read'),
('role_viewer', 'perm_users_read'),
('role_viewer', 'perm_roles_read'),
('role_viewer', 'perm_audit_read'),
('role_viewer', 'perm_registry_read')
ON CONFLICT(role_id, permission_id) DO NOTHING;
    """,
)

_add(
    "0004_service_state_seed",
    """
INSERT INTO service_state (key, value, updated_at_utc)
VALUES ('bootstrap', 'pending', datetime('now'))
ON CONFLICT(key) DO NOTHING;
    """,
)
