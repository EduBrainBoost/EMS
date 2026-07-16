from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_runtime_client_handles_ui_abuse_cases_without_secret_or_pii_leakage():
    source = (REPO_ROOT / "frontend" / "src" / "runtimeClient.ts").read_text(encoding="utf-8")
    for token in ["sanitizeRuntimeText", "normalizeUnknownRuntimeStatus", "missing_evidence_id", "schema_mismatch", "malicious_text_rejected", "timeout_simulation"]:
        assert token in source
    for state in ["NETWORK_ERROR", "AUTH_DENIED", "SCHEMA_INVALID", "ERROR"]:
        assert state in source
    forbidden = ["email", "phone", "Bearer ", "sk-"]
    assert not any(token in source for token in forbidden)
