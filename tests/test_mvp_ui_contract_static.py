from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_frontend_mvp_result_contract_source_contains_required_statuses_and_no_api_calls():
    source = (REPO_ROOT / "frontend" / "src" / "mvpResultContract.ts").read_text(encoding="utf-8")

    for status in ["PASS", "FAIL", "INSUFFICIENT", "ERROR"]:
        assert status in source
    assert "fetch(" not in source
    assert "axios" not in source
    assert "email" not in source.lower()


def test_frontend_app_renders_mvp_result_and_audit_evidence_labels():
    source = (REPO_ROOT / "frontend" / "src" / "App.tsx").read_text(encoding="utf-8")

    assert "MVP Verification Result" in source
    assert "Verification Status" in source
    assert "Audit Evidence ID" in source
    assert "renderMvpResultViewModel" in source
    assert "mvpResult.auditEvidenceRef" in source
