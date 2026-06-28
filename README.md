# EMS

Enterprise Management System — SSID-compatible operational layer.

## Status
- Phase: Local Rebuild v1
- Services: NOT STARTED
- Push: BLOCKED
- Remote: `https://github.com/EduBrainBoost/EMS.git`

## Ports
| Service  | Port | Status                 |
|----------|------|------------------------|
| Frontend | 3100 | Configured, not started |
| Backend  | 8100 | Configured, not started |

## Forbidden Ports
3000, 3001, 3002, 3210, 5173, 4321, 8000

## Quick Start (Validation Only)
```bash
python scripts/ems_static_guard.py
python -m pytest backend/tests -q
python -m pytest tests -q
python scripts/ems_validation.py
```

## Structure
- `backend/` — Python skeleton (no start)
- `frontend/` — TypeScript skeleton (no start)
- `contracts/` — Port matrix, API contract, Core integration contract
- `scripts/` — Guard, score, manifest, validation
- `tests/` — Guard, score, manifest tests
- `docs/` — Runbook, architecture, security boundaries
- `registry/` — Module, contract, and remote registry
- `audit/` — Evidence and score artifacts
- `.github/workflows/` — CI guard workflow

## Policies
- No `.env` files
- No secrets
- No provider configs
- No global CLI configs
- No service start in rebuild phase
- No push without approval
