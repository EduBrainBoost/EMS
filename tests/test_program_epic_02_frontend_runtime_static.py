from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_program_frontend_declares_release_runtime_states_and_safe_error_views():
    source = (REPO_ROOT / "frontend" / "src" / "runtimeClient.ts").read_text(encoding="utf-8")

    for state in ["PASS", "FAIL", "INSUFFICIENT", "ERROR", "LOADING", "NETWORK_ERROR", "AUTH_DENIED", "SCHEMA_INVALID"]:
        assert state in source
    assert "toRuntimeErrorView" in source
    assert "toNetworkErrorView" in source
    assert "auditEvidenceId" in source
    assert "correlationId" in source
    assert "NO_RAW_PII" in source
    assert "email" not in source.lower()
    assert "phone" not in source.lower()


def test_program_frontend_app_shows_release_evidence_and_error_state_labels():
    app = (REPO_ROOT / "frontend" / "src" / "App.tsx").read_text(encoding="utf-8")

    assert "Evidence ID" in app or "Audit Evidence ID" in app
    assert "Runtime Status" in app
    assert "Runtime Error" in app
    assert "correlation" in app.lower() or "Correlation" in app
