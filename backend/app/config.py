"""
EMS Backend Configuration — Local Rebuild Only
No secrets. No .env. No provider configs.
"""

EMS_FRONTEND_PORT: int = 3100
EMS_BACKEND_PORT: int = 8100
FORBIDDEN_PORTS: list[int] = [3000, 3001, 3002, 3210, 5173, 4321, 8000]
SERVICE_NAME: str = "EMS"
MODE: str = "local_rebuild"
START_SERVICES: bool = False
REMOTE_URL: str = "https://github.com/EduBrainBoost/EMS.git"
VERSION: str = "0.1.0-rebuild"


def validate_ports() -> dict:
    violations = []
    for port in (EMS_FRONTEND_PORT, EMS_BACKEND_PORT):
        if port in FORBIDDEN_PORTS:
            violations.append(port)
    return {
        "frontend_port": EMS_FRONTEND_PORT,
        "backend_port": EMS_BACKEND_PORT,
        "forbidden_ports": FORBIDDEN_PORTS,
        "violations": violations,
        "valid": len(violations) == 0,
    }
