from backend.app.api_contract import API_CONTRACT_SCHEMA, get_api_contract, validate_contract


def test_get_api_contract_returns_dict():
    contract = get_api_contract()
    assert isinstance(contract, dict)
    assert contract["service"] == "EMS"


def test_api_contract_has_required_endpoints():
    endpoints = API_CONTRACT_SCHEMA["endpoints"]
    assert "/health" in endpoints
    assert "/readiness" in endpoints
    assert "/version" in endpoints
    assert "/api/contract" in endpoints


def test_api_contract_policies():
    policies = API_CONTRACT_SCHEMA["policies"]
    assert policies["no_auth_in_scaffold"] is True
    assert policies["no_pii"] is True
    assert policies["no_secrets"] is True
    assert policies["no_provider_calls"] is True
    assert policies["no_service_start"] is True
    assert policies["backend_port"] == 8100
    assert policies["frontend_port"] == 3100


def test_validate_contract_valid():
    assert validate_contract(API_CONTRACT_SCHEMA) is True


def test_validate_contract_invalid_type():
    assert validate_contract("not a dict") is False


def test_validate_contract_missing_keys():
    assert validate_contract({"service": "x"}) is False


def test_validate_contract_bad_backend_port():
    bad = dict(API_CONTRACT_SCHEMA)
    bad["policies"] = dict(bad["policies"])
    bad["policies"]["backend_port"] = 8000
    assert validate_contract(bad) is False
