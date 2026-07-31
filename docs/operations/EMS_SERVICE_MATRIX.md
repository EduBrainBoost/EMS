# SSID-EMS Service Matrix

**Stand:** 2026-07-16T11:43:04Z

## Dienste

| Dienst | Komponente | Port | Host | Start-Befehl | Stop-Befehl | Health-Endpoint | PID-Erkennung | Status |
|--------|-----------|------|------|-------------|-------------|-----------------|---------------|--------|
| SSID-EMS Backend | `backend/app/http_server.py` | 8100 | 127.0.0.1 | `python backend/app/http_server.py --port 8100` | `kill PID` oder `Ctrl+C` | `http://127.0.0.1:8100/health` | ThreadingHTTPServer in Python-Prozess | RUNNING (wenn gestartet) |
| SSID-EMS Frontend | `frontend/server.py` | 3100 | 127.0.0.1 | `python frontend/server.py --port 3100` | `kill PID` oder `Ctrl+C` | `http://127.0.0.1:3100/health` | ThreadingHTTPServer in Python-Prozess | RUNNING (wenn gestartet) |
| SSID-Orchestrator API | extern | 3310 | 127.0.0.1 | extern | extern | `http://localhost:3310/health` | extern | ERREICHBAR |

## Abhängigkeiten

| Dienst | Benötigt | Bemerkung |
|--------|----------|-----------|
| Backend | SSID Core (`ssid_production`) | Python-Path, lokale Module |
| Frontend | Backend (Port 8100) | Port-Referenz in Config |
| Orchestrator | Keine EMS-Abhängigkeit | Health-Check möglich |

## Startreihenfolge

1. SSID-Orchestrator API (Port 3310)
2. SSID-EMS Backend (Port 8100)
3. SSID-EMS Frontend (Port 3100)

## Umgebungsvariablen

| Variable | Backend | Frontend | Bemerkung |
|----------|---------|----------|-----------|
| `ENV_MODE` | `local_scaffold` | `local_scaffold` | Phase 1 |
| `FRONTEND_PORT` | 3100 | 3100 | Konstant |
| `BACKEND_PORT` | 8100 | 8100 | Konstant |
| `START_SERVICES` | `False` | `false` | Phase 1 |

## Health Contract

```json
{
  "service": "SSID-EMS",
  "status": "ok",
  "started": false,
  "mode": "local_scaffold"
}
```

```json
{
  "service": "SSID-EMS",
  "status": "not_ready",
  "reason": "local_scaffold_no_service_start",
  "started": false,
  "mode": "local_scaffold"
}
```

## Port-Konflikte

Bei Konflikt auf Port 3100 oder 8100:
1. `netstat -ano | findstr :8100` (Windows) — Prozess identifizieren
2. Prüfen ob SSID-Dienst
3. Dokumentieren
4. Kein Ersatzport — Freigabe erforderlich
