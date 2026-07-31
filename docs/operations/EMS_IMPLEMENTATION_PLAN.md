# SSID-EMS Implementation Plan

**Stand:** 2026-07-16T11:43:04Z  
**Phase:** 1 — Local Operational Scaffold v1 (abgeschlossen)  
**Nächste Phase:** 3 — Production Readiness

## Abgeschlossene Maßnahmen (Phase 1)

### Fix: Guard False-Positive auf SHA256-Hashes
- **Datei:** `scripts/ems_static_guard.py`
- **Problem:** `check_forbidden_ports_in_content` erkannte `3001` als Substring in SHA256-Hashes in Evidence-Dateien
- **Lösung:** Hex-Adjazenzerkennung — wenn der Port-Token von Hex-Zeichen umgeben ist, wird er als Hash-Bestandteil ignoriert
- **Status:** IMPLEMENTIERT, GETESTET

### Betriebsfähigkeit hergestellt
- Backend startet auf Port 8100 (localhost-only)
- Frontend startet auf Port 3100 (localhost-only)
- Frontend und Backend kommunizieren
- Authentifizierung (Demo-Stub) funktioniert
- Orchestrator unter Port 3310 erreichbar
- Alle 35 Backend-Tests PASS
- Alle 29 Root-Tests PASS
- Guard PASS (deterministisch)
- Score 100/100

## Offene Maßnahmen (Phase 3)

### P3-01: Datenbankintegration
- SQLite (Development) / PostgreSQL (Production)
- Alembic-Migrationen
- Seed-Daten (keine Klartext-Passwörter)
- Backup/Restore-Integration

### P3-02: Echte Authentifizierung
- JWT-basierte Sessions
- HttpOnly/Secure/SameSite Cookies
- Token-Rotation
- Brute-Force-Schutz
- Account Lockout

### P3-03: RBAC/ABAC
- Rollen-Hierarchy
- Server-seitige Permission-Middleware
- Admin-Routen schützen
- Audit-Log für privilegierte Aktionen

### P3-04: Frontend-Build-Pipeline
- package.json + tsconfig.json
- Vite-Build
- Production-Build
- Route Guards
- Error Boundaries

### P3-05: Erweiterte Health Checks
- Datenbank-Health
- Orchestrator-Health
- Cache-Health
- Queue-Health

### P3-06: Logging und Observability
- Strukturierte Logs (JSON)
- Request-ID / Correlation-ID
- Latenz-Metriken
- Error-Rate

### P3-07: Security-Hardening
- CORS-Middleware (restriktiv)
- Rate Limiting (Token Bucket)
- CSRF-Schutz
- Input-Validation an allen Boundaries

### P3-08: E2E-Tests
- Playwright oder Cypress
- Browser-basierte Smoke-Tests
- CI/CD-Integration

## Risiken

| Risiko | Wahrscheinlichkeit | Auswirkung | Mitigation |
|--------|-------------------|------------|------------|
| SSID Core API-Breaking Changes | Mittel | Hoch | Semver-Pinning, Integration-Tests |
| Guard False-Positives bei neuen Patterns | Mittel | Mittel | Erweiterte Hex-Erkennung, Regression-Test |
| Phase 3-Umfang wächst unkontrolliert | Hoch | Mittel | YAGNI-Prinzip, Minimal-Viable-Implementation |

## Entscheidungen

- Keine pip-Dependencies in Phase 1 (stdlib-only)
- Kein npm-Build in Phase 1 (statische Surface)
- Keine Datenbank in Phase 1 (in-memory-stub)
- Demo-Auth nur für Scaffold, keine Produktions-Credentials
- Orchestrator-Anbindung nur Health-Check, kein Task-Abruf
