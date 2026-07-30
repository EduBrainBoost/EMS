"""Deterministic source scan for client-side XSS sinks."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

DEFAULT_EXCLUDES = {".git", ".pytest_cache", "__pycache__", "Runs", "audit/evidence"}
PATTERNS = {
    "innerHTML": re.compile(r"\b(?:innerHTML|outerHTML)\s*="),
    "insertAdjacentHTML": re.compile(r"\binsertAdjacentHTML\s*\("),
    "document.write": re.compile(r"\bdocument\.write\s*\("),
    "eval": re.compile(r"\beval\s*\("),
    "new Function": re.compile(r"\bnew\s+Function\s*\("),
    "string_timer": re.compile(r"\b(?:setTimeout|setInterval)\s*\(\s*(['\"])"),
    "javascript_url": re.compile(r"\bjavascript\s*:", re.I),
}
TEXT_SUFFIXES = {".js", ".ts", ".tsx", ".html", ".py"}

def scan(root: Path) -> dict:
    root = root.resolve(); findings = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        rel = path.relative_to(root).as_posix()
        if any(rel == x or rel.startswith(x.rstrip("/") + "/") for x in DEFAULT_EXCLUDES):
            continue
        try: text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError: continue
        for number, line in enumerate(text.splitlines(), 1):
            for kind, pattern in PATTERNS.items():
                if pattern.search(line):
                    classification = "SAFE_TEXT_RENDERING" if kind == "innerHTML" and "textContent" in line else "UNSAFE_DYNAMIC_SINK"
                    findings.append({"path": rel, "line": number, "kind": kind, "classification": classification})
    return {"schema_version": "1", "root": ".", "findings": findings, "unresolved_sinks": sum(x["classification"] == "UNSAFE_DYNAMIC_SINK" for x in findings), "status": "PASS" if not findings else "REVIEW_REQUIRED"}

def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("root", type=Path); parser.add_argument("--output", type=Path)
    result = scan(parser.parse_args().root)
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if parser.parse_args().output: parser.parse_args().output.write_text(payload, encoding="utf-8")
    else: print(payload, end="")
    return 0 if result["status"] == "PASS" else 1

if __name__ == "__main__": raise SystemExit(main())

__all__ = ["scan"]
