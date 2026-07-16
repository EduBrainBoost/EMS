from __future__ import annotations

from backend.app.api_contract import API_CONTRACT_SCHEMA, get_api_contract, validate_contract
from backend.app.main import create_app
from backend.app.mvp_productization import (
    build_error_response,
    get_demo_fixture,
    get_verification_result,
    validate_mvp_request,
)


def test_ems_contract_exposes_productization_endpoints():
    contract = get_api_contract()
    endpoints = contract["endpoints"]

    assert "/api/mvp/demo" in endpoints
    assert "/api/mvp/verify" in endpoints
    assert endpoints["/api/mvp/demo"]["method"] == "GET"
    assert endpoints["/api/mvp/verify"]["method"] == "POST"
    assert validate_contract(API_CONTRACT_SCHEMA) is True


def test_ems_app_routes_include_productization_handlers_without_starting_services():
    app = create_app()

    assert app["started"] is False
    assert callable(app["routes"]["/api/mvp/demo"])
    assert callable(app["routes"]["/api/mvp/verify"])


def test_demo_fixture_and_verification_result_are_deterministic_and_pii_safe():
    first = get_demo_fixture()
    second = get_demo_fixture()
    result = get_verification_result(first["request"])

    assert first == second
    assert result["status"] == "PASS"
    assert result["api_response"]["verification_result"]["status"] == "VALID"
    assert result["ui_result"]["status_label"] == "PASS"
    assert result["privacy_boundary"] == "NO_RAW_PII_NO_PRIVATE_KEY_MATERIAL"


def test_invalid_requests_get_fail_closed_error_responses():
    bad = {"request_id": "bad"}

    assert validate_mvp_request(bad) is False
    error = build_error_response("schema_violation", "invalid mvp request")
    assert error["status"] == "ERROR"
    assert error["error_code"] == "schema_violation"
    assert "email" not in str(error).lower()
