# SSID-EMS Architecture

## Overview
SSID-EMS (Educational Management System) is the operational layer that manages SSID Core execution tasks, user interactions, and observability without modifying core logic.

## Phase 1 Scope
- Local scaffold only
- No service start
- No external dependencies

## Components

### Backend (`backend/`)
- **config.py**: Port matrix, forbidden ports, mode flags
- **health.py**: Liveness/readiness/version contracts
- **api_contract.py**: Self-describing API surface
- **main.py**: App factory placeholder (no runtime)
- **version.py**: Version descriptor

### Frontend (`frontend/`)
- **config.ts**: Port matrix, forbidden ports, mode flags
- **healthContract.ts**: TypeScript validators for API responses
- **App.tsx**: Static status screen

### Contracts (`contracts/`)
- **ems_port_matrix.yaml**: Canonical port configuration
- **ems_api_contract.yaml**: API endpoint schemas
- **ssid_core_integration_contract.yaml**: Boundary rules between EMS and SSID Core

### Guard / Score / Validation (`scripts/`)
- **ems_static_guard.py**: Policy enforcement scan
- **ems_score.py**: Deterministic score calculator
- **ems_validation.py**: Orchestrator for all checks

## Integration with SSID Core
- EMS reads from Core registries and ledgers.
- EMS writes evidence/scores only to its own namespaces.
- EMS never modifies 16_codex or ROOT-24-LOCK.

## Data Flow (Future)
```
User -> Frontend (3100) -> Backend (8100)
                                    |
                                    v
                           SSID Core Registry / Ledger (read-only)
                                    |
                                    v
                           EMS Evidence / Score (write)
```
