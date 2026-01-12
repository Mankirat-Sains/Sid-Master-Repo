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
    candidates = [
        (repo_root / "Backend" / "desktop_agent" / "info_retrieval" / "src").resolve(),
        (repo_root / "info_retrieval" / "src").resolve(),  # fallback for legacy layouts
    ]
    for ir_src in candidates:
        if ir_src.exists() and str(ir_src) not in sys.path:
            sys.path.insert(0, str(ir_src))
