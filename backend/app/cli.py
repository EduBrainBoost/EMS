"""
SSID-EMS operational CLI.

Commands:
  migrate
  migration-status
  create-admin
  verify-audit-chain
  backup
  restore-test
"""

from __future__ import annotations

import argparse
import getpass
import sys

from backend.app import config
from backend.app.audit import verify_chain
from backend.app.backup import create_backup, restore_test
from backend.app.database import Database
from backend.app.password import hash_password, validate_password_strength
from backend.app.repository import (
    count_active_super_admins, count_users, create_user, get_user_by_username,
)


def _db() -> Database:
    return Database(config.EMS_DATABASE_PATH)


def cmd_migrate() -> int:
    db = _db()
    db._ensure_schema()
    print("migrations applied")
    return 0


def cmd_migration_status() -> int:
    db = _db()
    rows = db.fetchall("SELECT migration_id, checksum, applied_at_utc FROM schema_migrations")
    for r in rows:
        print(r["migration_id"], r["applied_at_utc"])
    return 0


def cmd_create_admin() -> int:
    db = _db()
    if count_active_super_admins(db) > 0:
        print("super_admin already exists; bootstrap blocked")
        return 1
    username = input("Admin username: ").strip()
    password = getpass.getpass("Admin password: ")
    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        print("passwords do not match")
        return 1
    validate_password_strength(password)
    user = create_user(db, username, password, actor_id="bootstrap", actor_role="bootstrap", roles=["super_admin"])
    print("created", user["username_display"], user["id"])
    return 0


def cmd_verify_audit_chain() -> int:
    db = _db()
    result = verify_chain(db)
    print("event_count", result["event_count"])
    print("first_event_id", result["first_event_id"])
    print("last_event_id", result["last_event_id"])
    print("last_event_hash", result["last_event_hash"])
    print("chain_valid", result["chain_valid"])
    return 0 if result["chain_valid"] else 1


def cmd_backup() -> int:
    db = _db()
    result = create_backup(db)
    print(result["path"])
    print(result["sha256"])
    print(result["size_bytes"])
    return 0


def cmd_restore_test() -> int:
    db = _db()
    backup_path = input("Backup path: ").strip()
    isolated_path = input("Isolated DB path: ").strip()
    result = restore_test(db, backup_path, isolated_path)
    print("integrity", result["integrity_check"])
    print("schema_version", result["schema_version"])
    print("user_count", result["user_count"])
    print("audit_chain_valid", result["audit_chain"]["chain_valid"])
    return 0 if result["integrity_check"] and result["audit_chain"]["chain_valid"] else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="SSID-EMS operational CLI")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("migrate")
    sub.add_parser("migration-status")
    sub.add_parser("create-admin")
    sub.add_parser("verify-audit-chain")
    sub.add_parser("backup")
    sub.add_parser("restore-test")

    args = parser.parse_args(argv)
    if args.command == "migrate":
        return cmd_migrate()
    if args.command == "migration-status":
        return cmd_migration_status()
    if args.command == "create-admin":
        return cmd_create_admin()
    if args.command == "verify-audit-chain":
        return cmd_verify_audit_chain()
    if args.command == "backup":
        return cmd_backup()
    if args.command == "restore-test":
        return cmd_restore_test()
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
