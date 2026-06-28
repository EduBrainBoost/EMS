"""
EMS Static Guard
Checks the EMS repo for policy violations before any service start or push.

Exit codes:
  0 = PASS
  21 = secret/path/port violation
  22 = contract violation
  23 = structure violation
"""

import json
import sys
from pathlib import Path

EXIT_PASS = 0
EXIT_VIOLATION = 21
EXIT_CONTRACT = 22
EXIT_STRUCTURE = 23

REPO_ROOT = Path(__file__).resolve().parent.parent

FORBIDDEN_PORTS = {3000, 3001, 3002, 3210, 5173, 4321, 8000}
ALLOWED_PORTS = {3100, 8100}

TABU_PATH_MARKERS = [
    r"Documents\Github",
    r"OneDrive\Dokumente\Github",
]

FORBIDDEN_FILES = {
    ".env",
    ".env.local",
    ".env.production",
    ".env.staging",
}

FORBIDDEN_DIRS = {
    "node_modules",
    "dist",
    "build",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
}

SERVICE_START_PATTERNS = ["uvicorn.run(", "npm start", "npm run dev"]

SECRET_PATTERNS = [
    "api_key",
    "apikey",
    "secret_key",
    "secretkey",
    "password=",
    "passwd=",
    "private_key",
    "token=",
    "auth_token",
]

ALLOWED_ROOT_ITEMS = {
    "backend",
    "frontend",
    "contracts",
    "docs",
    "audit",
    "registry",
    "scripts",
    "tests",
    "schemas",
    "approvals",
    ".github",
    "README.md",
    ".gitignore",
    "LICENSE",
    ".git",
    ".pytest_cache",
}

DOC_REL_PREFIXES = (
    "README",
    "docs/",
    "contracts/",
    "backend/README",
    "frontend/README",
)

GUARD_REL_PATHS = (
    "scripts/ems_static_guard.py",
    "scripts/ems_score.py",
    "scripts/ems_validation.py",
    "scripts/first_push_manifest.py",
)

TEST_REL_PREFIXES = (
    "backend/tests/",
    "tests/",
    "frontend/tests/",
)


def is_doc_or_guard(rel: str) -> bool:
    rel_fwd = rel.replace("\\", "/")
    if any(rel_fwd.startswith(p) for p in DOC_REL_PREFIXES):
        return True
    if rel_fwd in GUARD_REL_PATHS:
        return True
    if any(rel_fwd.startswith(p) for p in TEST_REL_PREFIXES):
        return True
    return False


def check_root_items(root: Path) -> list[dict]:
    findings = []
    for item in root.iterdir():
        name = item.name
        if name not in ALLOWED_ROOT_ITEMS:
            findings.append({
                "item": name,
                "reason": "unexpected_root_item",
            })
    return findings


def find_files(root: Path) -> list[Path]:
    files = []
    for p in root.rglob("*"):
        if p.is_file():
            skip_parts = {".git", ".pytest_cache", "__pycache__", ".venv", "node_modules", "dist", "build"}
            if any(part in skip_parts for part in p.parts):
                continue
            files.append(p)
    return files


def check_forbidden_ports_in_content(text: str, rel_path: str) -> list[dict]:
    if is_doc_or_guard(rel_path):
        return []
    findings = []
    for port in FORBIDDEN_PORTS:
        if str(port) not in text:
            continue
        lines = text.splitlines()
        for i, line in enumerate(lines, start=1):
            if str(port) in line:
                lower = line.lower()
                if "forbidden" in lower or "verboten" in lower or "port" in lower:
                    continue
                findings.append({
                    "file": rel_path,
                    "line": i,
                    "port": port,
                    "reason": "forbidden_port_in_source",
                })
    return findings


def check_service_start_commands(text: str, rel_path: str) -> list[dict]:
    if is_doc_or_guard(rel_path):
        return []
    findings = []
    for pattern in SERVICE_START_PATTERNS:
        if pattern not in text:
            continue
        lines = text.splitlines()
        for i, line in enumerate(lines, start=1):
            if pattern in line:
                stripped = line.strip()
                if stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("*"):
                    continue
                findings.append({
                    "file": rel_path,
                    "line": i,
                    "reason": "service_start_command_detected",
                    "match": pattern,
                })
    return findings


def check_secrets(text: str, rel_path: str) -> list[dict]:
    rel_fwd = rel_path.replace("\\", "/")
    if rel_fwd in GUARD_REL_PATHS or is_doc_or_guard(rel_path):
        return []
    findings = []
    lower_text = text.lower()
    for pattern in SECRET_PATTERNS:
        if pattern not in lower_text:
            continue
        lines = text.splitlines()
        for i, line in enumerate(lines, start=1):
            if pattern in line.lower():
                stripped = line.strip().lower()
                if stripped.startswith("#") or stripped.startswith("//") or "assert" in stripped or "forbidden" in stripped:
                    continue
                findings.append({
                    "file": rel_path,
                    "line": i,
                    "reason": "potential_secret",
                    "match": pattern,
                })
    return findings


def check_tabu_paths(text: str, rel_path: str) -> list[dict]:
    rel_fwd = rel_path.replace("\\", "/")
    if rel_fwd in GUARD_REL_PATHS or is_doc_or_guard(rel_path):
        return []
    findings = []
    for marker in TABU_PATH_MARKERS:
        if marker in text:
            findings.append({
                "file": rel_path,
                "reason": "tabu_path_detected",
                "path_marker": marker,
            })
    return findings


def check_file_names(root: Path) -> list[dict]:
    findings = []
    for p in root.rglob("*"):
        if p.name in FORBIDDEN_FILES:
            rel = p.relative_to(root).as_posix()
            findings.append({"file": rel, "reason": "forbidden_file_detected"})
    return findings


def check_provider_configs(root: Path) -> list[dict]:
    findings = []
    provider_files = ["mcp.json", "claude_desktop_config.json", "provider_config.yaml", "provider_config.json"]
    for p in root.rglob("*"):
        if p.name.lower() in [f.lower() for f in provider_files]:
            rel = p.relative_to(root).as_posix()
            findings.append({"file": rel, "reason": "provider_config_detected"})
    return findings


def check_global_cli_configs(root: Path) -> list[dict]:
    findings = []
    cli_configs = [".claude", ".cursor", ".aider", ".kimi"]
    for p in root.rglob("*"):
        if p.name.lower() in cli_configs and p.is_dir():
            rel = p.relative_to(root).as_posix()
            findings.append({"dir": rel, "reason": "global_cli_config_detected"})
    return findings


def check_contracts() -> list[dict]:
    violations = []
    config_py = REPO_ROOT / "backend" / "app" / "config.py"
    if config_py.exists():
        content = config_py.read_text(encoding="utf-8")
        if "8100" not in content or "EMS_BACKEND_PORT" not in content:
            violations.append({"file": "backend/app/config.py", "reason": "backend_port_mismatch"})
        if "3100" not in content or "EMS_FRONTEND_PORT" not in content:
            violations.append({"file": "backend/app/config.py", "reason": "frontend_port_mismatch"})
        if "START_SERVICES" not in content or "False" not in content:
            violations.append({"file": "backend/app/config.py", "reason": "service_start_not_false"})
        if "https://github.com/EduBrainBoost/EMS.git" not in content:
            violations.append({"file": "backend/app/config.py", "reason": "remote_url_mismatch"})

    config_ts = REPO_ROOT / "frontend" / "src" / "config.ts"
    if config_ts.exists():
        content = config_ts.read_text(encoding="utf-8")
        if "8100" not in content or "EMS_BACKEND_PORT" not in content:
            violations.append({"file": "frontend/src/config.ts", "reason": "backend_port_mismatch"})
        if "3100" not in content or "EMS_FRONTEND_PORT" not in content:
            violations.append({"file": "frontend/src/config.ts", "reason": "frontend_port_mismatch"})
        if "serviceStartAllowed" not in content or "false" not in content:
            violations.append({"file": "frontend/src/config.ts", "reason": "service_start_not_false"})
        if "https://github.com/EduBrainBoost/EMS.git" not in content:
            violations.append({"file": "frontend/src/config.ts", "reason": "remote_url_mismatch"})

    main_py = REPO_ROOT / "backend" / "app" / "main.py"
    if main_py.exists():
        content = main_py.read_text(encoding="utf-8")
        if "uvicorn.run(" in content:
            for i, line in enumerate(content.splitlines(), start=1):
                if "uvicorn.run(" in line:
                    stripped = line.strip()
                    if not (stripped.startswith("#") or stripped.startswith('"') or stripped.startswith("'")):
                        violations.append({"file": "backend/app/main.py", "line": i, "reason": "uvicorn_run_detected"})
        if '__name__ == "__main__"' in content:
            for i, line in enumerate(content.splitlines(), start=1):
                if '__name__ == "__main__"' in line:
                    stripped = line.strip()
                    if not (stripped.startswith("#") or stripped.startswith('"') or stripped.startswith("'")):
                        violations.append({"file": "backend/app/main.py", "line": i, "reason": "main_block_detected"})

    return violations


def main() -> int:
    all_findings = []

    all_findings.extend(check_root_items(REPO_ROOT))
    all_findings.extend(check_file_names(REPO_ROOT))
    all_findings.extend(check_provider_configs(REPO_ROOT))
    all_findings.extend(check_global_cli_configs(REPO_ROOT))

    files = find_files(REPO_ROOT)
    for fpath in files:
        rel = fpath.relative_to(REPO_ROOT).as_posix()
        try:
            text = fpath.read_text(encoding="utf-8")
        except Exception:
            continue
        all_findings.extend(check_forbidden_ports_in_content(text, rel))
        all_findings.extend(check_service_start_commands(text, rel))
        all_findings.extend(check_secrets(text, rel))
        all_findings.extend(check_tabu_paths(text, rel))

    contract_violations = check_contracts()

    # Categorize findings
    structure_findings = [f for f in all_findings if f.get("reason") == "unexpected_root_item"]
    other_findings = [f for f in all_findings if f.get("reason") != "unexpected_root_item"]

    result = {
        "scan": "ems_static_guard",
        "timestamp": "2026-05-10T20:00:00+00:00",
        "repo": str(REPO_ROOT),
        "findings_count": len(all_findings) + len(contract_violations),
        "structure_findings": structure_findings,
        "findings": other_findings,
        "contract_violations": contract_violations,
        "status": "pass" if (len(all_findings) == 0 and len(contract_violations) == 0) else "fail",
    }

    print(json.dumps(result, indent=2))

    if structure_findings:
        return EXIT_STRUCTURE
    if contract_violations:
        return EXIT_CONTRACT
    if other_findings:
        return EXIT_VIOLATION
    return EXIT_PASS


if __name__ == "__main__":
    sys.exit(main())
