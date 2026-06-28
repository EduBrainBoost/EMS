import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCORER = REPO_ROOT / "scripts" / "ems_score.py"


def run_score(output_root: Path) -> dict:
    env = os.environ.copy()
    env["EMS_TEST_OUTPUT_ROOT"] = str(output_root)
    result = subprocess.run([sys.executable, str(SCORER)], capture_output=True, text=True, env=env)
    return json.loads(result.stdout)


def test_score_status_is_pass(tmp_path):
    data = run_score(tmp_path)
    assert data["status"] == "pass"


def test_score_at_least_95(tmp_path):
    data = run_score(tmp_path)
    assert data["total_score"] >= 95


def test_max_score_is_100(tmp_path):
    data = run_score(tmp_path)
    assert data["max_score"] == 100


def test_breakdown_has_all_dimensions(tmp_path):
    data = run_score(tmp_path)
    dims = [
        "repo_structure", "backend_contract", "frontend_contract",
        "contracts_written", "port_policy", "no_service_start",
        "tests_passed", "evidence_written", "registry_updated",
    ]
    for d in dims:
        assert d in data["breakdown"]
