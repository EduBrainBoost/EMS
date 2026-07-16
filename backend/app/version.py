"""
SSID-EMS Version Module
"""

from backend.app.config import SERVICE_NAME, VERSION


def get_version() -> dict:
    return {
        "service": SERVICE_NAME,
        "version": VERSION,
    }
