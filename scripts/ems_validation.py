"""
SSID-EMS Phase 1 Validation Orchestrator
Runs all checks and produces evidence + report.
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SSID_ROOT = REPO_ROOT.parent / "SSID"


def run_guard() -> dict:
    guard = REPO_ROOT / "scripts/ems_static_guard.py"
    result = subprocess.run([sys.executable, str(guard)], capture_output=True, text=True)
    try:
        data = json.loads(result.stdout)
    except Exception:
        data = {"status": "error", "raw": result.stdout, "stderr": result.stderr}
    data["exit_code"] = result.returncode
    return data


def run_pytest_backend() -> dict:
    tests = REPO_ROOT / "backend/tests"
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(tests), "-q"],
        capture_output=True,
        text=True,
    )
    return {
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "pass": result.returncode == 0,
    }


def run_pytest_root() -> dict:
    tests = REPO_ROOT / "tests"
    if not tests.exists() or not any(tests.iterdir()):
        return {"exit_code": 0, "pass": True, "note": "no root tests"}
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(tests), "-q"],
        capture_output=True,
        text=True,
    )
    return {
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "pass": result.returncode == 0,
    }


def run_ssid_preflight() -> dict:
    checks = {}
    for script in ["structure_guard.py", "secret_scan.py", "forbidden_path_scan.py"]:
        path = SSID_ROOT / "12_tooling/scripts" / script
        result = subprocess.run([sys.executable, str(path)], capture_output=True, text=True)
        try:
            data = json.loads(result.stdout)
        except Exception:
            data = {"status": "unknown", "raw": result.stdout}
        checks[script] = {"exit_code": result.returncode, "status": data.get("status", "unknown")}
    return checks


def main():
    now = datetime.now(timezone.utc).isoformat()

    ssid_checks = run_ssid_preflight()
    guard_result = run_guard()
    backend_tests = run_pytest_backend()
    root_tests = run_pytest_root()

    # Calculate test score dynamically
    test_score = 15 if (backend_tests["pass"] and root_tests["pass"]) else 0

    # Run scorer with dynamic test result
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import ems_score

    score = ems_score.calculate_score(test_result=test_score, evidence_present=True)

    evidence = {
        "evidence_id": "ems_phase1_build_evidence",
        "timestamp_utc": now,
        "ssid_preflight": ssid_checks,
        "ems_guard": guard_result,
        "backend_tests": backend_tests,
        "root_tests": root_tests,
        "score": score,
        "repo_root": str(REPO_ROOT),
    }

    ev_path = REPO_ROOT / "audit/evidence/ems_phase1_build_evidence.json"
    ev_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")

    sc_path = REPO_ROOT / "audit/score/ems_phase1_score.json"
    sc_path.write_text(json.dumps(score, indent=2), encoding="utf-8")

    print(json.dumps({"validation": "complete", "score": score["total_score"], "status": score["status"]}, indent=2))

    # Overall pass requires SSID preflight + EMS guard + tests + score
    ssid_ok = all(c["status"] == "ok" or c["status"] == "pass" for c in ssid_checks.values())
    guard_ok = guard_result.get("status") == "pass" and guard_result.get("exit_code", 1) == 0
    tests_ok = backend_tests["pass"] and root_tests["pass"]
    score_ok = score["status"] == "pass"

    if ssid_ok and guard_ok and tests_ok and score_ok:
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
