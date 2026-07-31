from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_runtime_client_declares_all_release_candidate_states_and_error_mapper():
    source = (REPO_ROOT / "frontend" / "src" / "runtimeClient.ts").read_text(encoding="utf-8")

    for status in ["PASS", "FAIL", "INSUFFICIENT", "ERROR"]:
        assert status in source
    assert "toRuntimeErrorView" in source
    assert "auditEvidenceId" in source
    assert "runtime_error_evidence" in source
    assert "openrouter" not in source.lower()
    assert "ollama" not in source.lower()
    assert "email" not in source.lower()


def test_app_renders_release_candidate_runtime_paths_and_no_pii_labels():
    source = (REPO_ROOT / "frontend" / "src" / "App.tsx").read_text(encoding="utf-8")

    assert "LOCAL RUNTIME READY" in source
    assert "Runtime Health" in source
    assert "Runtime Demo" in source
    assert "Runtime Verify" in source
    assert "Audit Evidence ID" in source
    assert "email" not in source.lower()
