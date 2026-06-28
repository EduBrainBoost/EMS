import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GUARD = REPO_ROOT / "scripts" / "ems_static_guard.py"


def run_guard() -> dict:
    result = subprocess.run([sys.executable, str(GUARD)], capture_output=True, text=True)
    return json.loads(result.stdout)


def test_guard_passes():
    data = run_guard()
    assert data["status"] == "pass"


def test_no_structure_violations():
    data = run_guard()
    assert len(data.get("structure_findings", [])) == 0


def test_no_forbidden_files():
    data = run_guard()
    for finding in data.get("findings", []):
        assert finding["reason"] != "forbidden_file_detected"


def test_no_service_start_commands():
    data = run_guard()
    for finding in data.get("findings", []):
        assert finding["reason"] != "service_start_command_detected"


def test_no_contract_violations():
    data = run_guard()
    assert len(data.get("contract_violations", [])) == 0


def test_exit_code_is_zero():
    result = subprocess.run([sys.executable, str(GUARD)], capture_output=True, text=True)
    assert result.returncode == 0
