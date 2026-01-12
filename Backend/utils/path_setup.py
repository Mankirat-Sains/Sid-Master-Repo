"""
Shared path setup utilities to make sure optional packages (e.g., info_retrieval/src)
are importable before doc generation modules load.
"""
from __future__ import annotations

import sys
from pathlib import Path


def ensure_info_retrieval_on_path() -> None:
    """Idempotently add info_retrieval/src to sys.path when it exists."""
    repo_root = Path(__file__).resolve().parents[2]
    ir_src = (repo_root / "info_retrieval" / "src").resolve()
    if ir_src.exists() and str(ir_src) not in sys.path:
        sys.path.insert(0, str(ir_src))

