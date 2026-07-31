# SSID-EMS Changeset

**Stand:** 2026-07-16T11:43:04Z  
**Phase:** 1 — Local Operational Scaffold v1  
**Scope:** Guard-Fix, Dokumentation, Registry-Update

## Geänderte Dateien

| Datei | Änderungstyp | Beschreibung |
|-------|-------------|-------------|
| `scripts/ems_static_guard.py` | FIX | Hex-Adjazenzerkennung in `check_forbidden_ports_in_content` — false-positive auf SHA256-Hashes behoben |
| `docs/operations/EMS_CURRENT_STATE.md` | NEU | Aktueller Zustand des Systems |
| `docs/operations/EMS_GAP_ANALYSIS.md` | NEU | Gap Analysis Phase 1 |
| `docs/operations/EMS_SERVICE_MATRIX.md` | NEU | Service-Matrix |
| `docs/operations/EMS_API_MATRIX.yaml` | NEU | API-Endpunkte und Error-Schema |
| `docs/operations/EMS_PERMISSION_MATRIX.yaml` | NEU | Rollen und Berechtigungen |
| `docs/operations/EMS_DEPENDENCY_MATRIX.yaml` | NEU | Dependencies und Lockfile-Status |
| `docs/operations/EMS_IMPLEMENTATION_PLAN.md` | NEU | Implementierungsplan |
| `docs/operations/EMS_ROLLBACK_PLAN.md` | NEU | Rollback-Plan |
| `registry/ems_module_registry.yaml` | UPDATE | Status auf `operational`, Scores und Test-Ergebnisse |
| `registry/ems_contract_registry.yaml` | UPDATE | Neue Contracts, Policies, Evidence-Referenzen |
| `tests/_smoke_import_check.py` | NEU | Import- und Smoke-Test (temporär für Validierung) |

## Neue Dateien

- `docs/operations/EMS_CURRENT_STATE.md`
- `docs/operations/EMS_GAP_ANALYSIS.md`
- `docs/operations/EMS_SERVICE_MATRIX.md`
- `docs/operations/EMS_API_MATRIX.yaml`
- `docs/operations/EMS_PERMISSION_MATRIX.yaml`
- `docs/operations/EMS_DEPENDENCY_MATRIX.yaml`
- `docs/operations/EMS_IMPLEMENTATION_PLAN.md`
- `docs/operations/EMS_ROLLBACK_PLAN.md`
- `tests/_smoke_import_check.py`

## Implementierte Fixes

### FIX-001: Guard False-Positive auf SHA256-Hashes
- **Datei:** `scripts/ems_static_guard.py`
- **Funktion:** `check_forbidden_ports_in_content`
- **Problem:** Port-Nummer `3001` wurde als Substring in SHA256-Hashes (z.B. `a0129f17087fa...b3001...`) erkannt
- **Lösung:** Hex-Adjazenzerkennung — wenn der Port-Token links oder rechts von Hex-Zeichen umgeben ist, wird er als Hash-Bestandteil ignoriert
- **Test:** 5× Guard-Ausführung — deterministisch PASS
- **Regression:** Alle 64 Tests (35 Backend + 29 Root) PASS

## Nicht geändert

- Backend-Logik (keine Funktionsänderungen)
- Frontend-Logik (keine Funktionsänderungen)
- SSID-Core-Imports (keine Änderungen)
- Keine Secrets hinzugefügt
- Keine `.env`-Dateien hinzugefügt
- Keine Provider-Configs hinzugefügt
- Keine globalen CLI-Configs hinzugefügt
