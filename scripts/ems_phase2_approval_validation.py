"""
EMS Phase 2 Approval Validation Orchestrator
Runs all checks and produces evidence + report.
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
APPROVAL_FILE = REPO_ROOT / "approvals" / "ems_remote_push_approval.yaml"


def run_script(name: str, *args) -> dict:
    script = REPO_ROOT / "scripts" / name
    result = subprocess.run([sys.executable, str(script), *args], capture_output=True, text=True)
    try:
        data = json.loads(result.stdout)
    except Exception:
        data = {"status": "error", "raw": result.stdout, "stderr": result.stderr}
    data["exit_code"] = result.returncode
    return data


def run_pytest(path: str) -> dict:
    target = REPO_ROOT / path
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(target), "-q"],
        capture_output=True,
        text=True,
    )
    return {
        "exit_code": result.returncode,
        "pass": result.returncode == 0,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def main():
    now = datetime.now(timezone.utc).isoformat()

    guard = run_script("ems_static_guard.py")
    backend_tests = run_pytest("backend/tests")
    root_tests = run_pytest("tests")
    manifest = run_script("first_push_manifest.py")
    gate = run_script("ems_push_gate.py")
    score = run_script("ems_score.py")

    approval_exists = APPROVAL_FILE.exists()

    evidence = {
        "evidence_id": "ems_phase2_approval_validation",
        "timestamp_utc": now,
        "phase": "2",
        "checks": {
            "ems_static_guard": guard,
            "backend_tests": backend_tests,
            "root_tests": root_tests,
            "first_push_manifest": manifest,
            "ems_push_gate": gate,
            "ems_score": score,
        },
        "approval_file_exists": approval_exists,
        "approval_file_expected": False,
        "all_checks_pass": (
            guard.get("status") == "pass"
            and backend_tests["pass"]
            and root_tests["pass"]
            and manifest.get("exit_code", 1) == 0
            and gate.get("exit_code", 0) == 21
            and not approval_exists
        ),
    }

    ev_path = REPO_ROOT / "audit/evidence/ems_phase2_approval_validation.json"
    ev_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")

    print(json.dumps({
        "validation": "complete",
        "all_checks_pass": evidence["all_checks_pass"],
        "approval_exists": approval_exists,
        "gate_blocked": gate.get("exit_code") == 21,
    }, indent=2))

    return 0 if evidence["all_checks_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
