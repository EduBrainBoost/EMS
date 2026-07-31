"""Run EMS-local validation with an explicit optional SSID preflight."""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from scripts import ems_score
except ModuleNotFoundError:  # Direct script execution from the repository root.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import ems_score

REPO_ROOT = Path(__file__).resolve().parent.parent
SSID_SCRIPTS = ("structure_guard.py", "secret_scan.py", "forbidden_path_scan.py")


def _portable(value: Any) -> Any:
    """Remove machine-specific repository paths from persisted evidence."""
    if isinstance(value, str):
        replacements = {
            str(REPO_ROOT): ".",
            str(REPO_ROOT).replace("\\", "/"): ".",
        }
        for source, target in replacements.items():
            value = value.replace(source, target)
        return value
    if isinstance(value, list):
        return [_portable(item) for item in value]
    if isinstance(value, dict):
        return {key: _portable(item) for key, item in value.items()}
    return value


def _run_json(command: list[str], *, cwd: Path | None = None) -> tuple[dict, int]:
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    try:
        data = json.loads(result.stdout)
        if not isinstance(data, dict):
            raise ValueError("JSON result is not an object")
    except (json.JSONDecodeError, ValueError):
        data = {"status": "TOOL_ERROR", "raw": result.stdout, "stderr": result.stderr}
    return _portable(data), result.returncode


def run_guard() -> dict:
    guard = REPO_ROOT / "scripts/ems_static_guard.py"
    data, exit_code = _run_json([sys.executable, str(guard)])
    data["exit_code"] = exit_code
    return data


def _run_pytest(path: Path) -> dict:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(path), "-q"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    return {
        "exit_code": result.returncode,
        "stdout": _portable(result.stdout),
        "stderr": _portable(result.stderr),
        "pass": result.returncode == 0,
    }


def run_pytest_backend() -> dict:
    return _run_pytest(REPO_ROOT / "backend/tests")


def run_pytest_root() -> dict:
    tests = REPO_ROOT / "tests"
    if not tests.exists() or not any(tests.iterdir()):
        return {"exit_code": 0, "pass": True, "note": "no root tests"}
    return _run_pytest(tests)


def run_ssid_preflight() -> dict:
    """Run SSID checks only when SSID_REPO explicitly enables connected mode."""
    configured = os.environ.get("SSID_REPO", "").strip()
    if not configured:
        return {
            "status": "NOT_CONFIGURED",
            "required": False,
            "executed": False,
            "checks": {},
            "exit_codes": {},
            "reason_code": "SSID_REPO_NOT_CONFIGURED",
        }

    root = Path(configured).expanduser()
    if not root.is_dir():
        return {
            "status": "FAIL",
            "required": True,
            "executed": False,
            "checks": {},
            "exit_codes": {},
            "reason_code": "SSID_REPOSITORY_NOT_FOUND",
        }

    checks: dict[str, dict] = {}
    exit_codes: dict[str, int] = {}
    for script in SSID_SCRIPTS:
        path = root / "12_tooling/scripts" / script
        if not path.is_file():
            checks[script] = {"status": "TOOL_ERROR", "reason_code": "SSID_SCRIPT_NOT_FOUND"}
            exit_codes[script] = 2
            continue
        data, exit_code = _run_json([sys.executable, str(path)], cwd=root)
        status = data.get("status")
        passed = exit_code == 0 and status in {"ok", "pass", "PASS"}
        checks[script] = {
            "status": "PASS" if passed else "FAIL",
            "reported_status": status,
        }
        exit_codes[script] = exit_code

    all_pass = all(item["status"] == "PASS" for item in checks.values()) and len(checks) == len(SSID_SCRIPTS)
    return {
        "status": "PASS" if all_pass else "FAIL",
        "required": True,
        "executed": True,
        "configured": True,
        "repository": ".",
        "checks": checks,
        "exit_codes": exit_codes,
        "reason_code": "SSID_PREFLIGHT_PASS" if all_pass else "SSID_PREFLIGHT_FAILED",
    }


def main() -> int:
    now = datetime.now(timezone.utc).isoformat()
    ssid_preflight = run_ssid_preflight()
    guard_result = run_guard()
    backend_tests = run_pytest_backend()
    root_tests = run_pytest_root()

    local_tests_ok = backend_tests["pass"] and root_tests["pass"]
    score = ems_score.calculate_score(test_result=15 if local_tests_ok else 0, evidence_present=True)
    guard_ok = guard_result.get("status") == "pass" and guard_result.get("exit_code") == 0
    score_ok = score["status"] == "pass"
    local_ok = guard_ok and local_tests_ok and score_ok
    connected_ok = ssid_preflight["status"] == "PASS" if ssid_preflight["required"] else True
    overall_ok = local_ok and connected_ok

    evidence = _portable({
        "evidence_id": "ems_phase1_build_evidence",
        "timestamp_utc": now,
        "mode": "connected" if ssid_preflight["required"] else "standalone",
        "ssid_repository": {
            "configured": ssid_preflight["required"],
            "resolved_path": "." if ssid_preflight["required"] else None,
        },
        "ssid_preflight": ssid_preflight,
        "ems_guard": guard_result,
        "backend_tests": backend_tests,
        "root_tests": root_tests,
        "score": score,
        "overall_status": "PASS" if overall_ok else "FAIL",
        "overall_exit_code": 0 if overall_ok else 1,
    })
    (REPO_ROOT / "audit/evidence/ems_phase1_build_evidence.json").write_text(
        json.dumps(evidence, indent=2), encoding="utf-8"
    )
    (REPO_ROOT / "audit/score/ems_phase1_score.json").write_text(
        json.dumps(score, indent=2), encoding="utf-8"
    )
    print(json.dumps({"validation": "complete", "score": score["total_score"], "status": evidence["overall_status"]}, indent=2))
    return evidence["overall_exit_code"]


# Tiny executable contract check for the mode decision.
def _self_check() -> None:
    assert run_ssid_preflight()["status"] in {"NOT_CONFIGURED", "FAIL", "PASS"}


if __name__ == "__main__":
    _self_check()
    sys.exit(main())
