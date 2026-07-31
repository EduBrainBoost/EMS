# SSID-EMS Compliance Report

**Stand:** 2026-07-16T11:43:04Z  
**Scope:** Phase 1 — Local Operational Scaffold v1

## Compliance Gate

| Framework | Prüfung | Ergebnis | Bemerkung |
|-----------|---------|----------|-----------|
| DSGVO | Datenminimierung | PASS | Keine PII, keine personenbezogenen Daten |
| DSGVO | Zugriff | PARTIAL | Demo-Auth ohne echte Identitätsprüfung |
| DSGVO | Logging | PARTIAL | Audit-Boundary dokumentiert, kein Append-Only-Log |
| DSGVO | Export | NOT_APPLICABLE | Keine Datenbank |
| DSGVO | Löschung | NOT_APPLICABLE | Keine Datenbank |
| eIDAS | Identitätsprozesse | NOT_APPLICABLE | Keine eIDAS-Identitätsprüfung in Phase 1 |
| MiCA | Token-Anzeigen | NOT_APPLICABLE | Keine Token-Transaktionen |
| AMLD6 | Monitoring | PARTIAL | Kein AML-Monitoring, Rollenkonzept als Stub |
| AMLD6 | Rollen | PARTIAL | Rollen dokumentiert, nicht implementiert |
| AMLD6 | Evidence | PARTIAL | Audit-Boundary dokumentiert |
| AMLD6 | Eskalation | NOT_APPLICABLE | Kein Incident-Management in Phase 1 |
| DORA | Betriebsstabilität | PARTIAL | Health-Checks vorhanden, kein Recovery-Test |
| DORA | Incidents | NOT_APPLICABLE | Kein Incident-Management |
| DORA | Recovery | PARTIAL | Backup/Restore-Plan dokumentiert, nicht getestet |
| DORA | Drittanbieter | PASS | Keine externen Drittanbieter |
| NIS2 | Security Governance | PARTIAL | Security-Boundaries dokumentiert |
| NIS2 | Incident Management | NOT_APPLICABLE | Kein Incident-Management |
| EU AI Act | Menschliche Kontrolle | NOT_APPLICABLE | Keine AI-Komponenten in EMS |
| Open-Source-Lizenzen | Dependency-Prüfung | PASS | Keine externen Dependencies, nur stdlib + SSID Core |

## Fazit

Die Compliance-Statuswerte entsprechen der Scaffold-Natur von Phase 1.  
Alle kritischen Prüfungen (Secret Leakage, PII, Dritt-Anbieter) sind PASS.  
Offene Prüfungen sind für Phase 3 geplant.

**Status: PARTIAL** (erwartet für Phase 1)
