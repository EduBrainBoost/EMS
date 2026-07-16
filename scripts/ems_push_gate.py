"""
EMS Push Gate
Blocks all push activity unless a valid approval file exists.
Phase 2: Gate MUST block because approval file does not exist.

Exit codes:
  0 = ready_for_manual_push (only if approval is fully valid)
  21 = blocked (approval missing, invalid, or policy violation)
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
APPROVAL_FILE = REPO_ROOT / "approvals" / "ems_remote_push_approval.yaml"
MANIFEST_FILE = REPO_ROOT / "audit" / "evidence" / "ems_first_push_manifest.json"
EVIDENCE_FILE = REPO_ROOT / "audit" / "evidence" / "ems_phase2_push_gate.json"

EXPECTED_REMOTE = "https://github.com/EduBrainBoost/EMS.git"
EXPECTED_BRANCH = "main"


def load_approval() -> dict | None:
    if not APPROVAL_FILE.exists():
        return None
    try:
        import yaml
        return yaml.safe_load(APPROVAL_FILE.read_text(encoding="utf-8"))
    except Exception:
        return None


def load_manifest_tree_hash() -> str | None:
    if not MANIFEST_FILE.exists():
        return None
    try:
        data = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
        return data.get("repository_tree_hash")
    except Exception:
        return None


def validate_approval(approval: dict | None) -> tuple[bool, str]:
    if not approval:
        return False, "approval_missing"

    required = {
        "approval_id", "approved_by", "approved_at_utc", "allowed_repos",
        "allowed_remote", "allowed_branch", "approved_tree_hash",
        "pre_push_manifest_required", "expires_at_utc", "push_mode",
        "force_push_allowed", "pull_allowed", "fetch_allowed",
        "merge_allowed", "rebase_allowed",
    }
    if not required.issubset(approval.keys()):
        return False, "approval_incomplete"

    # Expiry
    try:
        expires = datetime.fromisoformat(approval["expires_at_utc"].replace("Z", "+00:00"))
        if datetime.now(timezone.utc) > expires:
            return False, "approval_expired"
    except Exception:
        return False, "approval_date_invalid"

    # Remote
    if approval.get("allowed_remote") != EXPECTED_REMOTE:
        return False, "remote_mismatch"

    # Branch
    if approval.get("allowed_branch") != EXPECTED_BRANCH:
        return False, "branch_not_main"

    # Tree hash
    actual_hash = load_manifest_tree_hash()
    if actual_hash and approval.get("approved_tree_hash"):
        if approval["approved_tree_hash"] != actual_hash:
            return False, "tree_hash_mismatch"

    # Force push
    if approval.get("force_push_allowed", True):
        return False, "force_push_not_allowed"

    # Pull/fetch/merge/rebase
    for action in ("pull_allowed", "fetch_allowed", "merge_allowed", "rebase_allowed"):
        if approval.get(action, True):
            return False, f"{action}_not_allowed"

    # Push mode
    if approval.get("push_mode") != "first_push_only":
        return False, "push_mode_not_first_push_only"

    return True, "approval_valid"


def main() -> int:
    approval = load_approval()
    is_valid, reason = validate_approval(approval)

    actual_hash = load_manifest_tree_hash()

    gate = {
        "gate_id": "ems_push_gate_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "gate_status": "ready_for_manual_push" if is_valid else "blocked",
        "push_allowed": is_valid,
        "approval_required": True,
        "approval_file_exists": APPROVAL_FILE.exists(),
        "approval_valid": is_valid,
        "block_reason": None if is_valid else reason,
        "remote": EXPECTED_REMOTE,
        "branch": EXPECTED_BRANCH,
        "approved_tree_hash": approval.get("approved_tree_hash") if approval else None,
        "actual_tree_hash": actual_hash,
    }

    EVIDENCE_FILE.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE_FILE.write_text(json.dumps(gate, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(gate, indent=2))

    return 0 if is_valid else 21


if __name__ == "__main__":
    sys.exit(main())
