"""
EMS First Push Manifest
Deterministically inventories the entire repo for pre-push verification.
"""

import hashlib
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

EXCLUDES = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    ".env",
    ".env.local",
    ".env.production",
}


def output_root() -> Path:
    configured = os.environ.get("EMS_TEST_OUTPUT_ROOT")
    if configured:
        return Path(configured)
    return REPO_ROOT


def redacted_repo_reference(repo_root: Path) -> tuple[str, bool]:
    repo_text = str(repo_root)
    if "\\Users\\" in repo_text or "/home/" in repo_text:
        return "<REDACTED_LOCAL_PATH>", True
    return repo_text, False


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def generate_manifest(repo_root: Path) -> dict:
    files = []
    total_size = 0
    for p in sorted(repo_root.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(repo_root).as_posix()
        if any(part in EXCLUDES for part in p.parts):
            continue
        size = p.stat().st_size
        total_size += size
        files.append({
            "path": rel,
            "size_bytes": size,
            "sha256": sha256_file(p),
        })

    # Deterministic tree hash
    tree_input = json.dumps(
        {"files": files},
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    tree_hash = hashlib.sha256(tree_input.encode("utf-8")).hexdigest()

    repo_reference, path_redacted = redacted_repo_reference(repo_root)
    manifest = {
        "manifest_id": "ems_first_push_manifest",
        "timestamp_utc": "2026-05-10T20:00:00+00:00",
        "repo": repo_reference,
        "path_redacted": path_redacted,
        "redaction_reason": "LOCAL_ABSOLUTE_PATH_REMOVED" if path_redacted else None,
        "file_count": len(files),
        "total_size_bytes": total_size,
        "repository_tree_hash": tree_hash,
        "files": files,
    }
    return manifest


def main():
    manifest = generate_manifest(REPO_ROOT)
    out_path = output_root() / "audit/evidence/ems_first_push_manifest.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(json.dumps({
        "manifest_id": manifest["manifest_id"],
        "file_count": manifest["file_count"],
        "total_size_bytes": manifest["total_size_bytes"],
        "repository_tree_hash": manifest["repository_tree_hash"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
