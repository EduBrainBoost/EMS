import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from scripts import ems_static_guard


REPO_ROOT = Path(__file__).resolve().parent.parent
LOCAL_USER_PATH_RE = re.compile(r"[A-Za-z]:\\Users\\")

EVIDENCE_FILES_WITH_LOCAL_PATHS = [
    REPO_ROOT / "audit" / "evidence" / "ems_first_push_manifest.json",
    REPO_ROOT / "audit" / "evidence" / "ems_phase2_approval_validation.json",
    REPO_ROOT / "audit" / "evidence" / "ems_rebuild_evidence.json",
]

TRACKED_EVIDENCE_FILES = [
    REPO_ROOT / "audit" / "evidence" / "ems_first_push_manifest.json",
    REPO_ROOT / "audit" / "evidence" / "ems_phase2_approval_validation.json",
    REPO_ROOT / "audit" / "evidence" / "ems_phase2_push_gate.json",
    REPO_ROOT / "audit" / "evidence" / "ems_rebuild_evidence.json",
    REPO_ROOT / "audit" / "score" / "ems_rebuild_score.json",
]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def walk_json_values(value):
    if isinstance(value, dict):
        for nested in value.values():
            yield from walk_json_values(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from walk_json_values(nested)
    else:
        yield value


def contains_redaction_marker(value) -> bool:
    if isinstance(value, dict):
        if value.get("path_redacted") is True:
            return True
        return any(contains_redaction_marker(nested) for nested in value.values())
    if isinstance(value, list):
        return any(contains_redaction_marker(nested) for nested in value)
    if isinstance(value, str):
        return value == "<REDACTED_LOCAL_PATH>" or value.startswith("<REDACTED_LOCAL_PATH>")
    return False


def run_script(script: str, output_root: Path) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["EMS_TEST_OUTPUT_ROOT"] = str(output_root)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / script)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=env,
    )


def test_license_is_explicitly_allowed_but_other_root_files_remain_blocked(tmp_path):
    allowed_root = tmp_path / "repo"
    allowed_root.mkdir()
    for name in ems_static_guard.ALLOWED_ROOT_ITEMS:
        if name in {".git", "LICENSE"}:
            continue
        path = allowed_root / name
        if "." in name and not name.startswith(".github"):
            path.write_text("placeholder", encoding="utf-8")
        else:
            path.mkdir(parents=True, exist_ok=True)

    (allowed_root / "LICENSE").write_text("license text", encoding="utf-8")
    assert ems_static_guard.check_root_items(allowed_root) == []

    (allowed_root / "unexpected-root-file.txt").write_text("blocked", encoding="utf-8")
    findings = ems_static_guard.check_root_items(allowed_root)
    assert findings == [
        {"item": "unexpected-root-file.txt", "reason": "unexpected_root_item"}
    ]


def test_root_license_in_recovered_repo_is_not_reported_as_unexpected():
    findings = ems_static_guard.check_root_items(REPO_ROOT)
    assert not [
        finding for finding in findings
        if finding["item"] == "LICENSE" and finding["reason"] == "unexpected_root_item"
    ]


def test_versioned_evidence_contains_no_raw_local_user_paths_and_keeps_redaction_context():
    affected_files = []
    for path in EVIDENCE_FILES_WITH_LOCAL_PATHS:
        data = json.loads(path.read_text(encoding="utf-8"))
        raw_local_path_values = [
            value for value in walk_json_values(data)
            if isinstance(value, str) and LOCAL_USER_PATH_RE.search(value)
        ]
        assert len(raw_local_path_values) == 0, f"raw local path values remain in {path.relative_to(REPO_ROOT)}"
        assert contains_redaction_marker(data), f"missing redaction context in {path.relative_to(REPO_ROOT)}"
        affected_files.append(path)

    assert len(affected_files) == 3


def test_versioned_text_files_contain_no_raw_local_user_paths():
    findings = []
    for path in REPO_ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(REPO_ROOT)
        if any(part in {".git", ".pytest_cache", "__pycache__", ".venv", "venv", "node_modules"} for part in rel.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for line_number, line in enumerate(text.splitlines(), start=1):
            if LOCAL_USER_PATH_RE.search(line):
                findings.append((rel.as_posix(), line_number))
    assert findings == []


def test_recovery_writer_scripts_do_not_mutate_tracked_evidence_when_output_root_is_temp(tmp_path):
    before = {path: sha256_file(path) for path in TRACKED_EVIDENCE_FILES}

    manifest_result = run_script("first_push_manifest.py", tmp_path)
    score_result = run_script("ems_score.py", tmp_path)
    gate_result = run_script("ems_push_gate.py", tmp_path)

    assert manifest_result.returncode == 0
    assert score_result.returncode == 0
    assert gate_result.returncode == 21
    assert (tmp_path / "audit" / "evidence" / "ems_first_push_manifest.json").exists()
    assert (tmp_path / "audit" / "score" / "ems_rebuild_score.json").exists()
    assert (tmp_path / "audit" / "evidence" / "ems_phase2_push_gate.json").exists()

    after = {path: sha256_file(path) for path in TRACKED_EVIDENCE_FILES}
    assert after == before
