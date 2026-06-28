import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCORER = REPO_ROOT / "scripts" / "ems_score.py"


def run_score() -> dict:
    result = subprocess.run([sys.executable, str(SCORER)], capture_output=True, text=True)
    return json.loads(result.stdout)


def test_score_status_is_pass():
    data = run_score()
    assert data["status"] == "pass"


def test_score_at_least_95():
    data = run_score()
    assert data["total_score"] >= 95


def test_max_score_is_100():
    data = run_score()
    assert data["max_score"] == 100


def test_breakdown_has_all_dimensions():
    data = run_score()
    dims = [
        "repo_structure", "backend_contract", "frontend_contract",
        "contracts_written", "port_policy", "no_service_start",
        "tests_passed", "evidence_written", "registry_updated",
    ]
    for d in dims:
        assert d in data["breakdown"]
