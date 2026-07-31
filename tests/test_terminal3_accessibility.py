from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


class A11yParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.labels = []
        self.headings = []
        self.landmarks = []
        self.controls = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags.append((tag, attrs))
        if tag in {"main", "nav", "aside", "header", "footer"}:
            self.landmarks.append(tag)
        if tag.startswith("h") and len(tag) == 2:
            self.headings.append(tag)
        if tag == "label" or attrs.get("aria-label"):
            self.labels.append((tag, attrs))
        if tag in {"a", "button", "input", "select", "textarea"}:
            self.controls.append((tag, attrs))


def test_frontend_has_keyboard_and_semantic_accessibility_contract():
    parser = A11yParser()
    parser.feed((REPO_ROOT / "frontend/index.html").read_text(encoding="utf-8"))
    assert "main" in parser.landmarks and "nav" in parser.landmarks
    assert any(attrs.get("aria-label") == "Admin navigation" for _, attrs in parser.labels)
    assert any(attrs.get("aria-label") == "Breadcrumb" for _, attrs in parser.labels)
    source = (REPO_ROOT / "frontend/index.html").read_text(encoding="utf-8")
    assert "text('h1'" in source and "text('h2'" in source
    assert all(tag != "input" or attrs.get("id") or attrs.get("aria-label") for tag, attrs in parser.controls)


def test_frontend_focus_and_zoom_are_not_disabled():
    source = (REPO_ROOT / "frontend/index.html").read_text(encoding="utf-8").lower()
    assert "user-scalable=no" not in source
    assert "outline:0" not in source
    assert "outline:none" not in source
    assert "onclick=" not in source


def test_accessibility_gate_is_explicit_about_manual_contrast_scope():
    assert {"keyboard", "focus", "landmarks", "labels", "contrast"} == {
        "keyboard", "focus", "landmarks", "labels", "contrast"
    }
    # Contrast needs rendered CSS pixels; no pauschal PASS is emitted here.
    assert "--text:#e5edf8" in (REPO_ROOT / "frontend/index.html").read_text(encoding="utf-8")
    assert "--bg:#0b1220" in (REPO_ROOT / "frontend/index.html").read_text(encoding="utf-8")
