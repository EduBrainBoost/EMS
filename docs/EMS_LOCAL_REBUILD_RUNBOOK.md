# EMS Local Rebuild Runbook

## Phase
Phase 1 — Local Rebuild v1

## Datum
2026-05-10

## Startstatus
- **Backend**: NOT STARTED (`START_SERVICES = False`)
- **Frontend**: NOT STARTED (`serviceStartAllowed = false`)
- **Remote**: `https://github.com/EduBrainBoost/EMS.git` (origin configured)
- **Push**: BLOCKED

## Erlaubte Ports
| Service  | Port |
|----------|------|
| Frontend | 3100 |
| Backend  | 8100 |

## Verbotene Ports
3000, 3001, 3002, 3210, 5173, 4321, 8000

## Späterer Backend-Start
Wenn Phase 4 freigegeben wird:
```bash
cd backend
# uvicorn backend.app.main:create_app --port 8100
```

## Späterer Frontend-Start
Wenn Phase 4 freigegeben wird:
```bash
cd frontend
# npm run dev -- --port 3100
```

## Warum jetzt nicht gestartet wird
1. Phase 1 ist Rebuild-Phase: Struktur, Contracts, Guards, Tests.
2. Kein Push-Approval vorhanden.
3. EMS-Repo ist lokal aufgebaut, aber noch nicht gepusht.
4. Port-Bindung ohne vollständigen Guard-Pass ist verboten.

## Testkommandos
```bash
# EMS Guard
python scripts/ems_static_guard.py

# Backend Tests
python -m pytest backend/tests -q

# Root Tests (Guard/Score/Manifest)
python -m pytest tests -q

# First Push Manifest
python scripts/first_push_manifest.py

# Full Validation + Evidence + Score
python scripts/ems_validation.py
```

## Push-Blocker
- Kein Push-Approval-File vorhanden.
- `scripts/ems_static_guard.py` muss PASS liefern.
- EMS muss >= 95 Punkte erreichen.

## Nächste Phase
**EMS-PHASE-2** — Explicit First Push Approval Package
