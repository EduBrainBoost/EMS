# SSID-EMS Local Build Runbook

## Phase
Phase 1 — Local Operational Scaffold v1

## Startstatus
- **Backend**: NOT STARTED (`START_SERVICES = False`)
- **Frontend**: NOT STARTED (`serviceStartAllowed = false`)
- **Remote**: UNCONFIRMED
- **Push**: BLOCKED

## Erlaubte Ports
| Service  | Port |
|----------|------|
| Frontend | 3100 |
| Backend  | 8100 |

## Verbotene Ports
3000, 3001, 3002, 3210, 5173, 4321, 8000

## Späterer Backend-Start
Wenn Phase 3 freigegeben wird:
```bash
cd backend
# uvicorn backend.app.main:create_app --port 8100
```

## Späterer Frontend-Start
Wenn Phase 3 freigegeben wird:
```bash
cd frontend
python server.py --port 3100
```

## Warum jetzt nicht gestartet wird
1. Phase 1 ist Scaffold-Phase: Struktur, Contracts, Guards, Tests.
2. Kein Push-Approval vorhanden.
3. Kein Remote-Create-Approval vorhanden.
4. EMS-EMS Remote ist unconfirmed.
5. Port-Bindung ohne vollständigen Guard-Pass ist verboten.
6. `frontend/package.json` ist absichtlich nicht vorhanden und als nicht-blockierende Scaffold-Limitierung dokumentiert.

## Testkommandos
```bash
# EMS Guard
python scripts/ems_static_guard.py

# Frontend Static Tests
python -m pytest -p no:cacheprovider tests/test_frontend_health_server.py -q
python -m pytest -p no:cacheprovider tests/test_runtime_ui_contract_static.py -q

# Compile Checks
python -m compileall frontend
python -m compileall backend
python -m compileall 24_meta_orchestration

# Backend Tests
python -m pytest backend/tests -q
python -m pytest backend/tests/test_auth_login.py -q

# Root Tests (Guard/Score)
python -m pytest tests -q

# Full Validation + Evidence + Score
python scripts/ems_validation.py
```

## Lokaler Demo-Auth-Check
```bash
curl -s -X POST http://127.0.0.1:8100/api/mvp/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"demo","password":"demo"}'

curl -s http://127.0.0.1:8100/api/mvp/auth/session
curl -s -X POST http://127.0.0.1:8100/api/mvp/auth/logout
```

## Persistence Boundary
- Modus: `no_persistence`
- Keine Dateien, keine DB, keine Tokens, keine externen Storage-Dienste
- Health- und Auth-Responses enthalten die Boundary explizit

## Remote-Blocker
- `EduBrainBoost/SSID-EMS` existiert nicht oder ist unconfirmed.
- Kein `origin` in `SSID-EMS` gesetzt.

## Push-Blocker
- Kein Push-Approval-File vorhanden.
- `scripts/ems_static_guard.py` muss PASS liefern.
- `SSID-EMS` muss >= 95 Punkte erreichen.

## Nächste Phase
**SSID-SWARM-EMS-PHASE-2** — EMS Remote Creation Approval Package
oder
**SSID-SWARM-EMS-PHASE-2** — EMS Local Origin Activation ohne Push
