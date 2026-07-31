# SSID-EMS Rollback Plan

**Stand:** 2026-07-16T11:43:04Z

## Rollback-Szenarien

### Szenario 1: Guard-Fix verursacht False Negatives
**Warscheinlichkeit:** Niedrig  
**Auswirkung:** Niedrig  
**Rollback:**
1. `git checkout scripts/ems_static_guard.py` (oder restore aus Backup)
2. Backup-Pfad: `C:\Users\bibel\SSID-Workspace\SSID-Arbeitsbereich\backups\SSID-EMS_20260716T114304Z`
3. Tests erneut ausführen: `python -m pytest tests -q`
4. Guard verifizieren: `python scripts/ems_static_guard.py`

### Szenario 2: SSID Core Dependency bricht
**Warscheinlichkeit:** Mittel  
**Auswirkung:** Hoch  
**Rollback:**
1. SSID Core Commit zurücksetzen (letzter bekannter guter Stand)
2. `pip install` oder Pfad-Anpassung in `sys.path`
3. Backend-Tests: `python -m pytest backend/tests -q`
4. Falls Core nicht verfügbar: Fallback auf lokale Demo-Fixtures

### Szenario 3: Port-Konflikt auf 8100 oder 3100
**Warscheinlichkeit:** Mittel  
**Auswirkung:** Mittel  
**Rollback:**
1. Prozess identifizieren: `netstat -ano | findstr :8100` (Windows)
2. SSID-Dienst von Prozess unterscheiden
3. Konflikt dokumentieren
4. Kein Ersatzport — Freigabe erforderlich oder Prozess stoppen
5. Dienst neustarten

### Szenario 4: Gesamter Rollback auf vorherigen Stand
**Schritte:**
1. Backup-Pfad: `C:\Users\bibel\SSID-Workspace\SSID-Arbeitsbereich\backups\SSID-EMS_20260716T114304Z`
2. Repository-Inhalt löschen (außer `.git`)
3. Backup-Inhalt kopieren: `xcopy /E /Y backup_path\* repo_path\`
4. Tests ausführen: `python -m pytest backend/tests tests -q`
5. Guard ausführen: `python scripts/ems_static_guard.py`
6. Services starten und verifizieren

## Backup-Informationen

| Property | Wert |
|----------|------|
| Backup-ID | `SSID-EMS_20260716T114304Z` |
| Backup-Pfad | `C:\Users\bibel\SSID-Workspace\SSID-Arbeitsbereich\backups\SSID-EMS_20260716T114304Z` |
| Dateien | 97 |
| Größe | 394133 Bytes |
| SHA256 | `fc1dc83e0cb340ef64fe84d7a3a277eb4d66df482d2e5f7ef9e39e0a19503922` |
| Restore-Befehl | `xcopy /E /Y "C:\Users\bibel\SSID-Workspace\SSID-Arbeitsbereich\backups\SSID-EMS_20260716T114304Z\*" "C:\Users\bibel\SSID-Workspace\SSID-Arbeitsbereich\Github\SSID-EMS\"` |

## Kontakt

Bei unklaren Rollback-Szenarien: SSID-EMS Phase 3 Approval erforderlich.
