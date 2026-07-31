import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_runtime_client_declares_local_api_paths_and_statuses_without_pii_or_providers():
    source = (REPO_ROOT / "frontend" / "src" / "runtimeClient.ts").read_text(encoding="utf-8")

    for path in ["/api/mvp/health", "/api/mvp/demo", "/api/mvp/verify", "/api/mvp/auth/login", "/api/mvp/auth/session", "/api/mvp/auth/logout"]:
        assert path in source
    for status in ["PASS", "FAIL", "INSUFFICIENT", "ERROR"]:
        assert status in source
    assert "openrouter" not in source.lower()
    assert "ollama" not in source.lower()
    assert "sk-" not in source
    assert "BEGIN PRIVATE KEY" not in source
    assert not re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", source)
    assert "fetch(" in source


def test_app_is_wired_to_runtime_client_and_renders_evidence_id():
    source = (REPO_ROOT / "frontend" / "src" / "App.tsx").read_text(encoding="utf-8")

    assert "runtimeClient" in source or "getRuntimeEndpoints" in source
    assert "Audit Evidence ID" in source
    assert "Verification Status" in source
    assert "PASS" in source


def test_frontend_package_manifest_is_absent_and_documented():
    manifest = REPO_ROOT / "frontend" / "package.json"
    readme = (REPO_ROOT / "frontend" / "README.md").read_text(encoding="utf-8")
    runbook = (REPO_ROOT / "docs" / "EMS_LOCAL_BUILD_RUNBOOK.md").read_text(encoding="utf-8")

    assert not manifest.exists()
    assert "package.json" in readme
    assert "package.json" in runbook
    assert "documented absence of package manifest" in readme or "package manifest" in runbook
