import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GATE = REPO_ROOT / "scripts" / "ems_push_gate.py"
APPROVAL_FILE = REPO_ROOT / "approvals" / "ems_remote_push_approval.yaml"


def run_gate(output_root: Path) -> dict:
    env = os.environ.copy()
    env["EMS_TEST_OUTPUT_ROOT"] = str(output_root)
    result = subprocess.run([sys.executable, str(GATE)], capture_output=True, text=True, env=env)
    return json.loads(result.stdout)


def test_gate_blocks_without_approval(tmp_path):
    # Ensure approval file does not exist for this test
    if APPROVAL_FILE.exists():
        APPROVAL_FILE.rename(APPROVAL_FILE.with_suffix(".yaml.bak"))
    try:
        data = run_gate(tmp_path)
        assert data["gate_status"] == "blocked"
        assert data["push_allowed"] is False
        assert data["approval_file_exists"] is False
        assert data["block_reason"] == "approval_missing"
    finally:
        if APPROVAL_FILE.with_suffix(".yaml.bak").exists():
            APPROVAL_FILE.with_suffix(".yaml.bak").rename(APPROVAL_FILE)


def test_gate_approval_required(tmp_path):
    data = run_gate(tmp_path)
    assert data["approval_required"] is True


def test_gate_remote_matches(tmp_path):
    data = run_gate(tmp_path)
    assert data["remote"] == "https://github.com/EduBrainBoost/EMS.git"


def test_gate_branch_is_main(tmp_path):
    data = run_gate(tmp_path)
    assert data["branch"] == "main"


def test_exit_code_is_21_when_blocked(tmp_path):
    if APPROVAL_FILE.exists():
        APPROVAL_FILE.rename(APPROVAL_FILE.with_suffix(".yaml.bak"))
    try:
        env = os.environ.copy()
        env["EMS_TEST_OUTPUT_ROOT"] = str(tmp_path)
        result = subprocess.run([sys.executable, str(GATE)], capture_output=True, text=True, env=env)
        assert result.returncode == 21
    finally:
        if APPROVAL_FILE.with_suffix(".yaml.bak").exists():
            APPROVAL_FILE.with_suffix(".yaml.bak").rename(APPROVAL_FILE)
