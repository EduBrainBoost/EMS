"""Create a deterministic, repository-contained SHA256 evidence manifest."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path

EXCLUDED_DIRS = {".git", ".pytest_cache", "__pycache__"}


def _inside(root: Path, path: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(root.resolve())
        return True
    except ValueError:
        return False


def collect_files(root: Path, output: Path | None = None) -> list[Path]:
    root = root.resolve()
    if not root.is_dir():
        raise ValueError("repository root must be a directory")
    files: list[Path] = []
    for current, dirs, names in os.walk(root, followlinks=False):
        current_path = Path(current)
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDED_DIRS)
        for name in sorted(names):
            path = current_path / name
            if any(part in EXCLUDED_DIRS for part in path.relative_to(root).parts):
                continue
            if path.is_symlink():
                target = path.resolve(strict=False)
                if not _inside(root, target):
                    raise ValueError(f"symlink escapes repository root: {path}")
                continue
            if output is not None and path.resolve() == output.resolve():
                continue
            if path.is_file():
                files.append(path)
    return sorted(files, key=lambda p: p.relative_to(root).as_posix())


def build_manifest(root: Path, output: Path | None = None) -> dict:
    root = root.resolve()
    entries = []
    for path in collect_files(root, output):
        relative = path.relative_to(root).as_posix()
        if Path(relative).is_absolute():
            raise ValueError("absolute path in manifest")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        entries.append({"path": relative, "sha256": digest, "size_bytes": path.stat().st_size})
    return {"schema_version": "1", "root": ".", "files": entries}


def write_manifest(root: Path, output: Path) -> None:
    root = root.resolve()
    output = output.resolve()
    if not _inside(root, output):
        raise ValueError("output must be inside repository root")
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(build_manifest(root, output), ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    fd, temporary = tempfile.mkstemp(prefix=f".{output.name}.", dir=output.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, output)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    write_manifest(args.root, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

__all__ = ["build_manifest", "collect_files", "write_manifest"]
