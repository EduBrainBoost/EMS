import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = REPO_ROOT / "scripts" / "first_push_manifest.py"


def run_manifest() -> dict:
    result = subprocess.run([sys.executable, str(MANIFEST)], capture_output=True, text=True)
    return json.loads(result.stdout)


def test_manifest_runs_successfully():
    data = run_manifest()
    assert "manifest_id" in data
    assert data["file_count"] > 0
    assert data["total_size_bytes"] > 0
    assert len(data["repository_tree_hash"]) == 64


def test_manifest_file_created():
    run_manifest()
    path = REPO_ROOT / "audit/evidence/ems_first_push_manifest.json"
    assert path.exists()
    content = json.loads(path.read_text(encoding="utf-8"))
    assert content["manifest_id"] == "ems_first_push_manifest"
    assert len(content["files"]) > 0


def test_manifest_excludes_git():
    run_manifest()
    path = REPO_ROOT / "audit/evidence/ems_first_push_manifest.json"
    content = json.loads(path.read_text(encoding="utf-8"))
    paths = [f["path"] for f in content["files"]]
    assert not any(".git/" in p for p in paths)
    assert not any("__pycache__" in p for p in paths)
