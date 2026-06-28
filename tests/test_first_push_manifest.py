import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = REPO_ROOT / "scripts" / "first_push_manifest.py"


def run_manifest(output_root: Path) -> dict:
    env = os.environ.copy()
    env["EMS_TEST_OUTPUT_ROOT"] = str(output_root)
    result = subprocess.run([sys.executable, str(MANIFEST)], capture_output=True, text=True, env=env)
    return json.loads(result.stdout)


def test_manifest_runs_successfully(tmp_path):
    data = run_manifest(tmp_path)
    assert "manifest_id" in data
    assert data["file_count"] > 0
    assert data["total_size_bytes"] > 0
    assert len(data["repository_tree_hash"]) == 64


def test_manifest_file_created(tmp_path):
    run_manifest(tmp_path)
    path = tmp_path / "audit/evidence/ems_first_push_manifest.json"
    assert path.exists()
    content = json.loads(path.read_text(encoding="utf-8"))
    assert content["manifest_id"] == "ems_first_push_manifest"
    assert len(content["files"]) > 0


def test_manifest_excludes_git(tmp_path):
    run_manifest(tmp_path)
    path = tmp_path / "audit/evidence/ems_first_push_manifest.json"
    content = json.loads(path.read_text(encoding="utf-8"))
    paths = [f["path"] for f in content["files"]]
    assert not any(".git/" in p for p in paths)
    assert not any("__pycache__" in p for p in paths)
