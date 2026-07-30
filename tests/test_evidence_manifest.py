from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.generate_evidence_manifest import build_manifest, write_manifest


def test_manifest_is_sorted_and_excludes_runtime_dirs(tmp_path: Path):
    (tmp_path / "z.txt").write_text("z", encoding="utf-8")
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "hidden").write_text("x", encoding="utf-8")
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "x.pyc").write_bytes(b"x")
    manifest = build_manifest(tmp_path)
    assert [item["path"] for item in manifest["files"]] == ["a.txt", "z.txt"]


def test_identical_inputs_and_output_exclusion_are_idempotent(tmp_path: Path):
    output = tmp_path / "manifest.json"
    write_manifest(tmp_path, output)
    first = output.read_bytes()
    write_manifest(tmp_path, output)
    assert output.read_bytes() == first
    assert "manifest.json" not in [item["path"] for item in json.loads(first)["files"]]


def test_content_change_changes_manifest(tmp_path: Path):
    output = tmp_path / "manifest.json"
    (tmp_path / "data.bin").write_bytes(b"one")
    write_manifest(tmp_path, output)
    first = output.read_text(encoding="utf-8")
    (tmp_path / "data.bin").write_bytes(b"two")
    write_manifest(tmp_path, output)
    assert output.read_text(encoding="utf-8") != first


def test_symlink_escape_is_rejected(tmp_path: Path, tmp_path_factory):
    outside = tmp_path_factory.mktemp("outside") / "secret.txt"
    outside.write_text("x", encoding="utf-8")
    link = tmp_path / "escape.txt"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable")
    with pytest.raises(ValueError, match="escapes"):
        build_manifest(tmp_path)


def test_output_must_be_inside_root(tmp_path: Path, tmp_path_factory):
    outside = tmp_path_factory.mktemp("outside") / "manifest.json"
    with pytest.raises(ValueError, match="inside"):
        write_manifest(tmp_path, outside)


def test_binary_unicode_and_no_absolute_paths(tmp_path: Path):
    name = "ü.bin"
    (tmp_path / name).write_bytes(b"\x00\xff")
    manifest = build_manifest(tmp_path)
    assert manifest["files"][0]["path"] == name
    assert not Path(manifest["files"][0]["path"]).is_absolute()
