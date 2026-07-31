# SSID-EMS Frontend Testplan

## Umgebung
- Keine Node.js-Runtime ist für den Scaffold-Phase zwingend erforderlich.
- Die TypeScript-Dateien sind statisch validiert und enthalten keine Laufzeitabhängigkeiten.

## Manuelle Validierung
1. `frontend/src/config.ts` — Prüfe Port 3100/8100, forbiddenPorts, serviceStartAllowed=false
2. `frontend/src/healthContract.ts` — Prüfe Typen und Validator-Funktionen
3. `frontend/src/App.tsx` — Prüfe, dass keine fetch()-Calls existieren

## Automatisierte Tests (falls Node verfügbar)
```bash
npx jest frontend/tests/healthContract.test.ts
```

## Akzeptanzkriterien
- Keine verbotenen Ports in der Config
- Keine API-Calls in App.tsx
- Validatoren akzeptieren nur erwartete Scaffold-Werte
