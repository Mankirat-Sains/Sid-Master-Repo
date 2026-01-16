"""
DOCGEN: Act node.
Executes prepared desktop steps via Desktop Agent adapter (noop if no steps).
No high-level decisions; execution-only.
"""
from __future__ import annotations

from typing import List, Dict, Any
from models.desktop_agent_state import DesktopAgentState
from config.logging_config import log_query


def node_doc_act(state: DesktopAgentState) -> dict:
    """Execute desktop steps (placeholder)."""
    log_query.info("DOCGEN: entered node_doc_act")
    steps: List[Dict[str, Any]] = getattr(state, "desktop_steps", []) or []
    if not steps:
        return {"desktop_execution": "noop"}
    return {
        "desktop_execution": "executed",
        "desktop_steps": steps,
    }

