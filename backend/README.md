# SSID-EMS Backend

## Status
Phase 1 — Local Operational Scaffold v1

## Ports
- Backend: `8100`
- Frontend: `3100` (configured, not started)

## Service Start
**NOT STARTED** — `START_SERVICES = False` in `app/config.py`

No `uvicorn.run()` call exists. The app factory (`main.py`) returns a descriptor dict only.

## Tests
```bash
python -m pytest backend/tests -q
python -m pytest backend/tests/test_auth_login.py -q
```

## Local Demo Auth
- `POST /api/mvp/auth/login` with `{"username": "demo", "password": "demo"}`
- `GET /api/mvp/auth/session`
- `POST /api/mvp/auth/logout`
- Demo-only, in-memory, no persistence, no real credentials
- Persistence boundary: `no_persistence` (no files, no DB, no token storage)

## Files
- `app/config.py` — Port config, forbidden ports, mode flags
- `app/health.py` — Health/readiness/version contracts
- `app/api_contract.py` — Self-describing API surface
- `app/http_server.py` — Local HTTP route surface, including demo auth
- `app/main.py` — App factory (no runtime start)
- `app/version.py` — Version module
