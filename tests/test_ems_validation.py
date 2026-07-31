import json
from pathlib import Path

import pytest

from scripts import ems_validation


@pytest.fixture
def connected_repo(tmp_path, monkeypatch):
    scripts = tmp_path / "12_tooling" / "scripts"
    scripts.mkdir(parents=True)
    monkeypatch.setenv("SSID_REPO", str(tmp_path))
    return scripts


def write_check(scripts: Path, name: str, payload: str = '{"status":"ok"}', exit_code: int = 0):
    path = scripts / name
    path.write_text(
        "import sys\n"
        f"print({payload!r})\n"
        f"sys.exit({exit_code})\n",
        encoding="utf-8",
    )


def test_standalone_does_not_probe_sibling(monkeypatch):
    monkeypatch.delenv("SSID_REPO", raising=False)
    result = ems_validation.run_ssid_preflight()
    assert result == {
        "status": "NOT_CONFIGURED",
        "required": False,
        "executed": False,
        "checks": {},
        "exit_codes": {},
        "reason_code": "SSID_REPO_NOT_CONFIGURED",
    }


def test_connected_missing_path_fails_closed(monkeypatch, tmp_path):
    monkeypatch.setenv("SSID_REPO", str(tmp_path / "missing"))
    result = ems_validation.run_ssid_preflight()
    assert result["status"] == "FAIL"
    assert result["required"] is True
    assert result["reason_code"] == "SSID_REPOSITORY_NOT_FOUND"
    assert result["executed"] is False


def test_connected_runs_all_three_checks(connected_repo):
    for name in ems_validation.SSID_SCRIPTS:
        write_check(connected_repo, name)
    result = ems_validation.run_ssid_preflight()
    assert result["status"] == "PASS"
    assert result["executed"] is True
    assert all(result["exit_codes"][name] == 0 for name in ems_validation.SSID_SCRIPTS)
    assert all(result["checks"][name]["status"] == "PASS" for name in ems_validation.SSID_SCRIPTS)


def test_connected_failed_script_fails(connected_repo):
    for name in ems_validation.SSID_SCRIPTS:
        write_check(connected_repo, name, exit_code=1 if name == "secret_scan.py" else 0)
    result = ems_validation.run_ssid_preflight()
    assert result["status"] == "FAIL"
    assert result["checks"]["secret_scan.py"]["status"] == "FAIL"


def test_connected_invalid_json_is_not_pass(connected_repo):
    for name in ems_validation.SSID_SCRIPTS:
        write_check(connected_repo, name, payload="not-json")
    result = ems_validation.run_ssid_preflight()
    assert result["status"] == "FAIL"
    assert all(result["checks"][name]["status"] == "FAIL" for name in ems_validation.SSID_SCRIPTS)


def test_connected_missing_script_is_tool_error(connected_repo):
    write_check(connected_repo, ems_validation.SSID_SCRIPTS[0])
    result = ems_validation.run_ssid_preflight()
    assert result["status"] == "FAIL"
    assert result["checks"]["secret_scan.py"]["status"] == "TOOL_ERROR"


def test_main_status_and_exit_code_match(monkeypatch, tmp_path):
    monkeypatch.delenv("SSID_REPO", raising=False)
    monkeypatch.setattr(ems_validation, "REPO_ROOT", tmp_path)
    (tmp_path / "audit/evidence").mkdir(parents=True)
    (tmp_path / "audit/score").mkdir(parents=True)
    (tmp_path / "scripts").mkdir()
    (tmp_path / "backend/tests").mkdir(parents=True)
    (tmp_path / "tests").mkdir()
    monkeypatch.setattr(ems_validation, "run_guard", lambda: {"status": "pass", "exit_code": 0})
    monkeypatch.setattr(ems_validation, "run_pytest_backend", lambda: {"pass": True, "exit_code": 0})
    monkeypatch.setattr(ems_validation, "run_pytest_root", lambda: {"pass": True, "exit_code": 0})
    monkeypatch.setattr(
        ems_validation,
        "SSID_SCRIPTS",
        ("structure_guard.py", "secret_scan.py", "forbidden_path_scan.py"),
    )
    exit_code = ems_validation.main()
    evidence = json.loads((tmp_path / "audit/evidence/ems_phase1_build_evidence.json").read_text())
    assert exit_code == evidence["overall_exit_code"] == 0
    assert evidence["overall_status"] == "PASS"
    assert "C:\\Users\\" not in json.dumps(evidence)


def test_local_gate_failure_is_fail(monkeypatch, tmp_path):
    monkeypatch.delenv("SSID_REPO", raising=False)
    monkeypatch.setattr(ems_validation, "REPO_ROOT", tmp_path)
    (tmp_path / "audit/evidence").mkdir(parents=True)
    (tmp_path / "audit/score").mkdir(parents=True)
    (tmp_path / "scripts").mkdir()
    monkeypatch.setattr(ems_validation, "run_guard", lambda: {"status": "fail", "exit_code": 1})
    monkeypatch.setattr(ems_validation, "run_pytest_backend", lambda: {"pass": True, "exit_code": 0})
    monkeypatch.setattr(ems_validation, "run_pytest_root", lambda: {"pass": True, "exit_code": 0})
    assert ems_validation.main() == 1


def test_backend_failure_is_fail(monkeypatch, tmp_path):
    monkeypatch.delenv("SSID_REPO", raising=False)
    monkeypatch.setattr(ems_validation, "REPO_ROOT", tmp_path)
    (tmp_path / "audit/evidence").mkdir(parents=True)
    (tmp_path / "audit/score").mkdir(parents=True)
    (tmp_path / "scripts").mkdir()
    monkeypatch.setattr(ems_validation, "run_guard", lambda: {"status": "pass", "exit_code": 0})
    monkeypatch.setattr(ems_validation, "run_pytest_backend", lambda: {"pass": False, "exit_code": 1})
    monkeypatch.setattr(ems_validation, "run_pytest_root", lambda: {"pass": True, "exit_code": 0})
    assert ems_validation.main() == 1


def test_score_failure_is_fail(monkeypatch, tmp_path):
    monkeypatch.delenv("SSID_REPO", raising=False)
    monkeypatch.setattr(ems_validation, "REPO_ROOT", tmp_path)
    (tmp_path / "audit/evidence").mkdir(parents=True)
    (tmp_path / "audit/score").mkdir(parents=True)
    (tmp_path / "scripts").mkdir()
    monkeypatch.setattr(ems_validation, "run_guard", lambda: {"status": "pass", "exit_code": 0})
    monkeypatch.setattr(ems_validation, "run_pytest_backend", lambda: {"pass": True, "exit_code": 0})
    monkeypatch.setattr(ems_validation, "run_pytest_root", lambda: {"pass": True, "exit_code": 0})
    class FailingScore:
        @staticmethod
        def calculate_score(**_):
            return {"total_score": 50, "status": "fail"}
    monkeypatch.setattr(ems_validation.ems_score, "calculate_score", FailingScore.calculate_score)
    assert ems_validation.main() == 1
