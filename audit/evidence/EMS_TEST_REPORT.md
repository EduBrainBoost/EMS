# SSID-EMS Test Report

**Stand:** 2026-07-16T11:43:04Z  
**Ausgeführt:** Lokal auf Windows 10, Python 3.14.4

## Test-Übersicht

| Test-Suite | Tests | Pass | Fail | Status |
|-----------|-------|------|------|--------|
| Backend Unit Tests | 35 | 35 | 0 | PASS |
| Root Tests (Guard/Score/Static) | 29 | 29 | 0 | PASS |
| Frontend Server Tests | 1 | 1 | 0 | PASS |
| Frontend Contract Tests (statisch) | 5 | 5 | 0 | PASS |
| Import Smoke Test | 1 | 1 | 0 | PASS |
| **Gesamt** | **71** | **71** | **0** | **PASS** |

## Backend Unit Tests

### test_config.py
- `test_frontend_port_is_allowed` — PASS
- `test_backend_port_is_allowed` — PASS
- `test_forbidden_ports_listed` — PASS
- `test_env_mode_is_scaffold` — PASS
- `test_start_services_is_false` — PASS
- `test_validate_ports_passes` — PASS

### test_health.py
- `test_health_status` — PASS
- `test_readiness_status` — PASS
- `test_version_status` — PASS
- `test_full_status` — PASS

### test_api_contract.py
- `test_get_api_contract_returns_dict` — PASS
- `test_api_contract_has_required_endpoints` — PASS
- `test_api_contract_policies` — PASS
- `test_validate_contract_valid` — PASS
- `test_validate_contract_invalid_type` — PASS
- `test_validate_contract_missing_keys` — PASS
- `test_validate_contract_bad_backend_port` — PASS
- `test_backend_http_server_contract_surface_roundtrip` — PASS

### test_auth_login.py
- `test_auth_login_session_logout_demo_flow` — PASS (Login 200, Bad-Login 401, Logout 200)

### test_persistence_boundary.py
- `test_no_persistence_boundary_is_explicit_and_restart_unsafed` — PASS
- `test_no_persistence_boundary_survives_http_roundtrip_without_writing_state` — PASS

### test_mvp_productization_api.py
- `test_ems_contract_exposes_productization_endpoints` — PASS
- `test_ems_app_routes_include_productization_handlers_without_starting_services` — PASS
- `test_demo_fixture_and_verification_result_are_deterministic_and_pii_safe` — PASS
- `test_invalid_requests_get_fail_closed_error_responses` — PASS

### test_runtime_http_adapter.py
- `test_runtime_adapter_handles_health_demo_and_verify_without_external_services` — PASS
- `test_runtime_adapter_rejects_negative_runtime_cases_fail_closed` — PASS
- `test_runtime_http_server_roundtrip_uses_localhost_only_and_returns_json` — PASS

### test_program_epic_02_api_release.py
- `test_program_api_errors_include_stable_release_schema_and_correlation_id` — PASS
- `test_program_api_rejects_auth_bypass_and_production_like_auth` — PASS
- `test_program_api_health_exposes_release_diagnostics_without_external_services` — PASS

### test_full_program_order_api_abuse.py
- `test_pre_release_api_abuse_cases_are_rejected_consistently` — PASS

### test_release_candidate_runtime_api.py
- `test_release_candidate_backend_rejects_oversized_payload_and_keeps_error_schema` — PASS
- `test_release_candidate_backend_rejects_production_like_auth_call` — PASS
- `test_release_candidate_health_contains_diagnostics_without_external_services` — PASS

## Root Tests

### test_ems_static_guard.py
- `test_guard_passes` — PASS
- `test_no_forbidden_files` — PASS
- `test_no_service_start_commands` — PASS
- `test_no_contract_violations` — PASS

### test_ems_score.py
- `test_score_status_is_pass` — PASS
- `test_score_at_least_95` — PASS (Score: 100)
- `test_max_score_is_100` — PASS
- `test_breakdown_has_all_dimensions` — PASS

### test_ems_push_gate.py
- `test_push_gate_blocks_without_approval` — PASS

### test_first_push_manifest.py
- `test_manifest_runs_successfully` — PASS
- `test_manifest_file_created` — PASS
- `test_manifest_excludes_git` — PASS

### test_frontend_health_server.py
- `test_frontend_static_server_compiles_exposes_health_and_index_links` — PASS

### test_runtime_ui_contract_static.py
- `test_runtime_client_declares_local_api_paths_and_statuses_without_pii_or_providers` — PASS
- `test_app_is_wired_to_runtime_client_and_renders_evidence_id` — PASS
- `test_frontend_package_manifest_is_absent_and_documented` — PASS

### test_full_program_order_dom_e2e.py
- `test_pre_release_dom_e2e_renders_all_release_states_and_no_sensitive_text` — PASS
- `test_pre_release_dom_harness_documents_binary_browser_status` — PASS

## Integration / Smoke Tests (manuell verifiziert)

| Check | Ergebnis |
|-------|----------|
| Backend auf Port 8100 startet | PASS |
| Frontend auf Port 3100 startet | PASS |
| Backend Health Check (`/health`) | PASS |
| Backend Readiness (`/readiness`) | PASS |
| Backend Version (`/version`) | PASS |
| Backend Status (`/status`) | PASS |
| Backend API Contract (`/api/contract`) | PASS |
| Backend Demo Health (`/api/mvp/health`) | PASS |
| Backend Demo (`/api/mvp/demo`) | PASS |
| Backend Login (demo/demo) | PASS |
| Backend Session | PASS |
| Backend Logout | PASS |
| Backend Bad-Login | PASS (401) |
| Frontend Health (`/health`) | PASS |
| Frontend Index (`/`) | PASS |
| Frontend API Health (`/api/health`) | PASS |
| Orchestrator Health (`http://localhost:3310/health`) | PASS |
| Import Smoke (SSID Core + EMS Module) | PASS |

## Negative Tests (abgedeckt in pytest)

| Szenario | Test | Ergebnis |
|----------|------|----------|
| Falsche Login-Credentials | `test_auth_login_session_logout_demo_flow` | PASS (401) |
| Oversized Payload | `test_release_candidate_backend_rejects_oversized_payload` | PASS (413) |
| Production-Like Auth | `test_release_candidate_backend_rejects_production_like_auth_call` | PASS (403) |
| Auth Bypass (kein Token) | `test_program_api_rejects_auth_bypass_and_production_like_auth` | PASS (403) |
| Unknown Fields | `test_pre_release_api_abuse_cases_are_rejected_consistently` | PASS (400) |
| Invalid Status Injection | `test_pre_release_api_abuse_cases_are_rejected_consistently` | PASS (400) |
| Wrong Content-Type | `test_pre_release_api_abuse_cases_are_rejected_consistently` | PASS (415) |
| Invalid JSON | `test_program_api_errors_include_stable_release_schema_and_correlation_id` | PASS (400) |
| 404-Route | `test_backend_http_server_contract_surface_roundtrip` | PASS (404) |

## Offene Tests (Phase 3)

- E2E-Browser-Tests (Playwright/Cypress)
- Last-/Performance-Tests
- Shutdown/Restart-Zyklus-Tests
- Backup/Restore-Integrationstests
- RBAC-Eskalationstests
- IDOR-Tests
- CSRF-Tests
- CORS-Konfigurationstests
