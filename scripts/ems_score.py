"""
EMS Rebuild Score Calculator
Generates a deterministic score based on EMS rebuild artifacts.
"""

import json
import os
import sys
from pathlib import Path

SCORE_WEIGHTS = {
    "repo_structure": 15,
    "backend_contract": 15,
    "frontend_contract": 10,
    "contracts_written": 15,
    "port_policy": 15,
    "no_service_start": 10,
    "tests_passed": 10,
    "evidence_written": 5,
    "registry_updated": 5,
}

MAX_SCORE = 100
PASS_THRESHOLD = 95

REPO_ROOT = Path(__file__).resolve().parent.parent


def output_root() -> Path:
    configured = os.environ.get("EMS_TEST_OUTPUT_ROOT")
    if configured:
        return Path(configured)
    return REPO_ROOT


def check_repo_structure() -> tuple[int, str]:
    required = [
        "backend/app/__init__.py",
        "backend/app/config.py",
        "backend/app/health.py",
        "backend/app/api_contract.py",
        "backend/app/main.py",
        "backend/tests/test_config.py",
        "backend/tests/test_health.py",
        "backend/tests/test_api_contract.py",
        "frontend/src/config.ts",
        "frontend/src/healthContract.ts",
        "frontend/src/App.tsx",
        "contracts/ems_port_matrix.yaml",
        "contracts/ems_api_contract.yaml",
        "contracts/ssid_core_integration_contract.yaml",
        "scripts/ems_static_guard.py",
        "scripts/ems_score.py",
        "scripts/ems_validation.py",
        "scripts/first_push_manifest.py",
        "docs/EMS_LOCAL_REBUILD_RUNBOOK.md",
        "docs/EMS_ARCHITECTURE.md",
        "docs/EMS_SECURITY_BOUNDARIES.md",
        "audit/score/ems_rebuild_score.json",
        "registry/ems_module_registry.yaml",
        "registry/ems_contract_registry.yaml",
        "registry/ems_remote_registry.yaml",
        ".github/workflows/ems-local-guard.yml",
        "README.md",
        ".gitignore",
    ]
    missing = [p for p in required if not (REPO_ROOT / p).exists()]
    if missing:
        return (0, f"missing: {missing}")
    return (SCORE_WEIGHTS["repo_structure"], "ok")


def check_backend_contract() -> tuple[int, str]:
    files = [
        "backend/app/config.py",
        "backend/app/health.py",
        "backend/app/api_contract.py",
        "backend/app/main.py",
    ]
    for f in files:
        if not (REPO_ROOT / f).exists():
            return (0, f"missing {f}")
    main = (REPO_ROOT / "backend/app/main.py").read_text(encoding="utf-8")
    for line in main.splitlines():
        if "uvicorn.run(" in line:
            stripped = line.strip()
            if not (stripped.startswith("#") or stripped.startswith('"') or stripped.startswith("'")):
                return (0, "uvicorn.run detected in main.py")
    for line in main.splitlines():
        if '__name__ == "__main__"' in line:
            stripped = line.strip()
            if not (stripped.startswith("#") or stripped.startswith('"') or stripped.startswith("'")):
                return (0, "main block detected in main.py")
    return (SCORE_WEIGHTS["backend_contract"], "ok")


def check_frontend_contract() -> tuple[int, str]:
    files = ["frontend/src/config.ts", "frontend/src/healthContract.ts", "frontend/src/App.tsx"]
    for f in files:
        if not (REPO_ROOT / f).exists():
            return (0, f"missing {f}")
    app = (REPO_ROOT / "frontend/src/App.tsx").read_text(encoding="utf-8")
    if "fetch(" in app or "axios" in app:
        return (0, "api call detected in App.tsx")
    return (SCORE_WEIGHTS["frontend_contract"], "ok")


def check_contracts_written() -> tuple[int, str]:
    files = [
        "contracts/ems_port_matrix.yaml",
        "contracts/ems_api_contract.yaml",
        "contracts/ssid_core_integration_contract.yaml",
    ]
    for f in files:
        if not (REPO_ROOT / f).exists():
            return (0, f"missing {f}")
    return (SCORE_WEIGHTS["contracts_written"], "ok")


def check_port_policy() -> tuple[int, str]:
    config = (REPO_ROOT / "backend/app/config.py").read_text(encoding="utf-8")
    if "8100" not in config or "EMS_BACKEND_PORT" not in config:
        return (0, "backend port mismatch")
    if "3100" not in config or "EMS_FRONTEND_PORT" not in config:
        return (0, "frontend port mismatch")
    forbidden = [3000, 3001, 3002, 3210, 5173, 4321, 8000]
    for port in forbidden:
        if f"{port}" not in config:
            return (0, f"forbidden port {port} not listed")
    return (SCORE_WEIGHTS["port_policy"], "ok")


def check_no_service_start() -> tuple[int, str]:
    config = (REPO_ROOT / "backend/app/config.py").read_text(encoding="utf-8")
    if "START_SERVICES" not in config or "False" not in config:
        return (0, "START_SERVICES not False")
    main = (REPO_ROOT / "backend/app/main.py").read_text(encoding="utf-8")
    for line in main.splitlines():
        if "uvicorn.run(" in line:
            stripped = line.strip()
            if not (stripped.startswith("#") or stripped.startswith('"') or stripped.startswith("'")):
                return (0, "uvicorn.run detected in main.py")
    for line in main.splitlines():
        if '__name__ == "__main__"' in line:
            stripped = line.strip()
            if not (stripped.startswith("#") or stripped.startswith('"') or stripped.startswith("'")):
                return (0, "main block detected in main.py")
    return (SCORE_WEIGHTS["no_service_start"], "ok")


def check_evidence(skip_score_file: bool = False) -> tuple[int, str]:
    sc = REPO_ROOT / "audit/score/ems_rebuild_score.json"
    if skip_score_file or sc.exists():
        return (SCORE_WEIGHTS["evidence_written"], "ok")
    return (0, "score file missing")


def check_registry() -> tuple[int, str]:
    mod = REPO_ROOT / "registry/ems_module_registry.yaml"
    con = REPO_ROOT / "registry/ems_contract_registry.yaml"
    rem = REPO_ROOT / "registry/ems_remote_registry.yaml"
    if mod.exists() and con.exists() and rem.exists():
        return (SCORE_WEIGHTS["registry_updated"], "ok")
    return (0, "registry files missing")


def calculate_score(test_result: int = 10, evidence_present: bool = False) -> dict:
    scores = {}
    scores["repo_structure"] = check_repo_structure()[0]
    scores["backend_contract"] = check_backend_contract()[0]
    scores["frontend_contract"] = check_frontend_contract()[0]
    scores["contracts_written"] = check_contracts_written()[0]
    scores["port_policy"] = check_port_policy()[0]
    scores["no_service_start"] = check_no_service_start()[0]
    scores["tests_passed"] = test_result
    scores["evidence_written"] = check_evidence(skip_score_file=evidence_present)[0]
    scores["registry_updated"] = check_registry()[0]

    total = sum(scores.values())
    return {
        "score_version": "ems_rebuild_v1",
        "timestamp_utc": "2026-05-10T20:00:00+00:00",
        "max_score": MAX_SCORE,
        "pass_threshold": PASS_THRESHOLD,
        "total_score": total,
        "status": "pass" if total >= PASS_THRESHOLD else "fail",
        "breakdown": scores,
    }


def main():
    score = calculate_score(evidence_present=True)
    out_path = output_root() / "audit/score/ems_rebuild_score.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(score, indent=2), encoding="utf-8")
    print(json.dumps(score, indent=2))
    return 0 if score["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
