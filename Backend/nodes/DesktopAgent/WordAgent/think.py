"""
DOCGEN: Think node.
Converts doc_request + desktop routing context into a simple action plan (steps).
No high-level decisions; purely shapes execution steps.
"""
from __future__ import annotations

from typing import List, Dict, Any
from models.desktop_agent_state import DesktopAgentState
from config.logging_config import log_query


def node_doc_think(state: DesktopAgentState) -> dict:
    """Produce execution steps for desktop actions (placeholder)."""
    log_query.info("DOCGEN: entered node_doc_think")
    steps: List[Dict[str, Any]] = []
    plan = state.desktop_action_plan or {}
    if plan:
        steps.append({"action": plan.get("action", "open"), "tool": plan.get("tool", "word")})
    return {"desktop_steps": steps}

