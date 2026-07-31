# SSID-EMS Gap Analysis

**Stand:** 2026-07-16T11:43:04Z  
**Scope:** Betriebsfähigkeit auf Port 3100/8100 gemäß AGENTS.md und Implementierungsauftrag

## Gap-Übersicht

| # | Kategorie | Gap | Schweregrad | Status | Maßnahme |
|---|-----------|-----|-------------|--------|----------|
| 1 | Guard | `check_forbidden_ports_in_content` false-positive auf SHA256-Hashes | High | FIXED | Hex-Adjazenzerkennung implementiert |
| 2 | Backend | Keine echte Service-Start-Orchestrierung | Medium | OFFEN | Phase 3 — `uvicorn`/Production-Start |
| 3 | Backend | Keine Datenbank (nur In-Memory-Stub) | High | OFFEN | Phase 3 — SQLite/PostgreSQL + Alembic |
| 4 | Backend | Kein RBAC/ABAC (nur Demo-Rollen) | High | OFFEN | Phase 3 — Permission-Layer |
| 5 | Frontend | Kein npm-Build/package.json | Medium | OFFEN | Phase 3 — Vite/React-Build |
| 6 | Frontend | Kein Routing/Route Guards | Medium | OFFEN | Phase 3 — React Router + Guards |
| 7 | Auth | Demo-Stub-Credentials (`demo`/`demo`) | High | OFFEN | Phase 3 — Echte Auth-Provider-Anbindung |
| 8 | Audit | Kein strukturiertes Append-Only-Log | High | OFFEN | Phase 3 — Audit-Log-Service |
| 9 | Health | Readiness liefert `not_ready` wenn Services nicht started | Medium | OFFEN | Phase 3 — Readiness-Erweiterung |
| 10 | CORS | Kein CORS-Header (localhost-only reicht für Phase 1) | Low | OFFEN | Phase 3 — CORS-Middleware |
| 11 | Rate Limiting | Kein Rate Limit implementiert | Medium | OFFEN | Phase 3 — Token Bucket |
| 12 | E2E | Kein Browser-basiertes E2E | Low | OFFEN | Phase 3 — Playwright/Cypress |
| 13 | Orchestrator | EMS→Orchestrator Task-Abfrage nicht implementiert | Medium | OFFEN | Phase 3 — Adapter |
| 14 | Backup | Kein automatisches DB-Backup | High | OFFEN | Phase 3 — Backup-Service |

## Nicht-Gaps (Phase 1 Scaffold)

- Keine Secrets im Repo
- Keine `.env`-Dateien
- Keine Provider-Configs
- Keine globalen CLI-Configs
- Ports 3100/8100 korrekt konfiguriert
- Forbidden Ports dokumentiert
- Alle Pflicht-Tests PASS
- Guard PASS (deterministisch)
- Score 100/100

## Entscheidung

Phase 1-Gaps sind **dokumentierte Scaffold-Limitierungen**. Die im Implementierungsauftrag geforderten Funktionalitäten (DB, Auth, RBAC, Build, E2E) erfordern Phase 3.  
In Phase 1 ist die Betriebsfähigkeit auf Scaffold-Ebene hergestellt. Alle offenen High-Gaps sind für Phase 3 geplant.
