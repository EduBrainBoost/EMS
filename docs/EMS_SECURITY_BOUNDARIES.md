# EMS Security Boundaries

## Phase 1 Boundaries
These boundaries are enforced by `scripts/ems_static_guard.py` and must hold for every commit.

### Root Structure
- Only allowed root items: backend, frontend, contracts, docs, audit, registry, scripts, tests, .github, README.md, .gitignore, .git

### No Secrets
- No `.env` files
- No hardcoded API keys, passwords, tokens
- No `private_key` strings in source

### No Provider Configs
- No `mcp.json`
- No `claude_desktop_config.json`
- No `provider_config.yaml` / `provider_config.json`

### No Global CLI Configs
- No `.claude/`, `.cursor/`, `.aider/`, `.kimi/` directories in repo

### No Service Start in Rebuild
- No `uvicorn.run(` in backend source
- No `npm start` / `npm run dev` in frontend source
- `START_SERVICES = False` in backend config
- `serviceStartAllowed = false` in frontend config

### Port Compliance
- Frontend must use `3100`
- Backend must use `8100`
- Forbidden ports: `3000, 3001, 3002, 3210, 5173, 4321, 8000`

### Tabu Paths
- No references to:
  - `C:\Users\bibel\Documents\Github`
  - `C:\Users\bibel\OneDrive\Dokumente\Github`

### No Direct Core Writes
- EMS must not write to `16_codex`
- EMS must not modify ROOT-24-LOCK
- EMS must not call external providers from core context

### Push Gate
- Push requires approval file
- Approval must be validated by guard
- Force push is forbidden
