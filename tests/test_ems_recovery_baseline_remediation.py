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

CURATED_MANIFEST_REL = "audit/evidence/ems_recovery_curated_manifest_2026-06-28.json"
CURATION_LEDGER = REPO_ROOT / "audit" / "evidence" / "EMS_RECOVERY_CURATION_LEDGER_2026-06-28.md"
CURATED_MANIFEST = REPO_ROOT / CURATED_MANIFEST_REL
CURATED_MANIFEST_SELF_EXCLUSION = {
    "path": CURATED_MANIFEST_REL,
    "reason": "SELF_DESCRIBING_MANIFEST_EXCLUDED_TO_AVOID_RECURSIVE_HASH_PARADOX",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_lines(*args: str) -> list[str]:
    return subprocess.check_output(
        ["git", *args],
        cwd=REPO_ROOT,
        text=True,
    ).splitlines()


def git_bytes(relative_path: str) -> bytes:
    return subprocess.check_output(
        ["git", "show", f":{relative_path}"],
        cwd=REPO_ROOT,
    )


def git_object_id(relative_path: str) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", f"HEAD:{relative_path}"],
        cwd=REPO_ROOT,
        text=True,
    ).strip()


def load_curated_manifest() -> dict:
    return json.loads(CURATED_MANIFEST.read_text(encoding="utf-8"))


def ledger_text() -> str:
    return CURATION_LEDGER.read_text(encoding="utf-8")


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


def test_curated_manifest_declares_exact_scope_and_self_exclusion_only():
    manifest = load_curated_manifest()

    assert manifest["hash_algorithm"] == "SHA-256"
    assert manifest["hash_input"] == "canonical_git_blob_content_bytes"
    assert manifest["scope"] == "tracked_recovery_tree_except_explicit_scope_exclusions"
    assert manifest["scope_exclusions"] == [CURATED_MANIFEST_SELF_EXCLUSION]

    tracked_files = set(git_lines("ls-tree", "-r", "--name-only", "HEAD"))
    manifest_files = [entry["relative_path"] for entry in manifest["files"]]

    assert manifest_files == sorted(manifest_files)
    assert len(manifest_files) == len(set(manifest_files))
    assert set(manifest_files) == tracked_files - {CURATED_MANIFEST_REL}
    assert CURATED_MANIFEST_REL not in manifest_files


def test_curated_manifest_hashes_canonical_git_file_content_bytes_not_git_object_ids():
    manifest = load_curated_manifest()

    for entry in manifest["files"]:
        content = git_bytes(entry["relative_path"])
        assert entry["size_bytes"] == len(content)
        assert entry["sha256"] == hashlib.sha256(content).hexdigest()
        assert len(entry["sha256"]) == 64
        assert entry["sha256"] != git_object_id(entry["relative_path"])


def test_curation_ledger_declares_required_delta_categories_and_all_manifest_paths():
    manifest = load_curated_manifest()
    text = ledger_text()

    required_categories = {
        "LINE_ENDING_ONLY",
        "TRANSPORT_MUTATION_REPAIRED",
        "LOCAL_PATH_REDACTION",
        "TEST_OUTPUT_ISOLATION",
        "LICENSE_GUARD_POLICY_ALIGNMENT",
        "RECOVERY_ASSURANCE_ARTIFACT_ADDED",
    }
    for category in required_categories:
        assert category in text

    assert "UNEXPLAINED_MISMATCH_COUNT:\n0" in text
    assert "PASS_WITH_DECLARED_CURATION_DELTAS" in text

    documented_paths = set(
        re.findall(r"relative_path:\s+([^\n]+)", text)
    )
    for entry in manifest["files"]:
        assert entry["relative_path"] in documented_paths

    assert CURATED_MANIFEST_REL in documented_paths
