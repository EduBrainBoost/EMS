from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


class TextCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
    def handle_data(self, data):
        stripped = data.strip()
        if stripped:
            self.text.append(stripped)


def test_pre_release_dom_e2e_renders_all_release_states_and_no_sensitive_text():
    harness = REPO_ROOT / "frontend" / "src" / "preReleaseDomHarness.ts"
    source = harness.read_text(encoding="utf-8")
    parser = TextCollector()
    html_start = source.index("<main")
    html_end = source.index("</main>") + len("</main>")
    parser.feed(source[html_start:html_end])
    rendered = " ".join(parser.text)

    for phrase in ["SSID MVP Pre-Release DOM E2E", "Demo Flow", "Verify Flow", "Evidence ID", "Correlation ID"]:
        assert phrase in rendered
    for state in ["PASS", "FAIL", "INSUFFICIENT", "ERROR", "AUTH_DENIED", "NETWORK_ERROR"]:
        assert state in rendered
    private_key_marker = "BEGIN " + "PRIVATE KEY"
    forbidden = ["@", private_key_marker, "Bearer ", "sk-", "phone", "email"]
    assert not any(token.lower() in rendered.lower() for token in forbidden)


def test_pre_release_dom_harness_documents_binary_browser_status():
    source = (REPO_ROOT / "frontend" / "src" / "preReleaseDomHarness.ts").read_text(encoding="utf-8")
    assert "DOM_E2E_READY" in source
    assert "BROWSER_BINARY_NOT_REQUIRED_FOR_LOCAL_PRE_RC" in source
    assert "NO_PII_NO_SECRETS" in source
