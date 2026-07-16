import sys
from pathlib import Path

# Add repo root so 'backend.app' imports work during pytest
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
