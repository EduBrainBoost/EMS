"""
SSID-EMS Backend Configuration — Local Scaffold Only
No secrets. No .env. No provider configs.
"""

EMS_FRONTEND_PORT: int = 3100
EMS_BACKEND_PORT: int = 8100
FORBIDDEN_PORTS: list[int] = [3000, 3001, 3002, 3210, 5173, 4321, 8000]
ENV_MODE: str = "local_scaffold"
START_SERVICES: bool = False
SERVICE_NAME: str = "SSID-EMS"
VERSION: str = "0.1.0-scaffold"


def validate_ports() -> dict:
    """
    Ensures configured ports are not in the forbidden list.
    Returns a status dict for audit/evidence.
    """
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
