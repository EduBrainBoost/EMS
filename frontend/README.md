# SSID-EMS Frontend

## Status
Phase 1 — Local Operational Scaffold v1

## Scaffold Limitierung
- `frontend/package.json` ist absichtlich nicht vorhanden.
- Die aktuelle Frontend-Surface ist stdlib/static und wird über Python- und statische Contract-Tests abgesichert.
- Node/Jest ist für diesen Lauf nicht erforderlich.
- This is the documented absence of package manifest for the current scaffold.

## Ports
- Frontend: `3100`
- Backend: `8100` (configured, not started)

## Service Start
**NOT STARTED** — `serviceStartAllowed = false` in `src/config.ts`

No `npm start` or `npm run dev` is triggered. The App is a static status screen.
Local runtime validation is available via `python server.py --port 3100`.

## Local Demo Auth References
- Frontend shell links health routes only: `/health` and `/api/health`
- Demo auth lives on the backend: `/api/mvp/auth/login`, `/api/mvp/auth/session`, `/api/mvp/auth/logout`
- Runtime client exports the auth paths for static contract checks, but no real credentials are used

## Files
- `src/config.ts` — Port config, forbidden ports, mode flags
- `src/healthContract.ts` — TypeScript validators for health responses
- `src/runtimeClient.ts` — Runtime endpoints including local demo auth paths
- `src/App.tsx` — Static status screen (no API calls)

## Tests
Preferred local tests:
```bash
python -m pytest -p no:cacheprovider tests/test_frontend_health_server.py -q
python -m pytest -p no:cacheprovider tests/test_runtime_ui_contract_static.py -q
```

If Node.js/Jest is available in a later scaffold phase:
```bash
npx jest frontend/tests/healthContract.test.ts
```
Otherwise see `frontend/tests/TESTPLAN.md`.
