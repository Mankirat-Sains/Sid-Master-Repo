import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LA_ROOT = ROOT / "Local Agent" / "info_retrieval" / "src"
BACKEND_ROOT = ROOT / "Backend"

# Single path injection to make Local Agent imports deterministic in tests.
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))
if str(BACKEND_ROOT) not in sys.path:
    sys.path.append(str(BACKEND_ROOT))
if LA_ROOT.exists() and str(LA_ROOT) not in sys.path:
    sys.path.append(str(LA_ROOT))
