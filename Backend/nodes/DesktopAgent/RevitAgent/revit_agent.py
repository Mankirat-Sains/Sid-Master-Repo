"""
Revit Agent placeholder
Handles Revit desktop routing targets. Extend with real Revit automation tools.
"""
from typing import Any, Dict

from models.desktop_agent_state import DesktopAgentState
from config.logging_config import log_route


def node_revit_agent(state: DesktopAgentState) -> Dict[str, Any]:
    """
    Lightweight Revit agent stub so routing has a valid target.
    """
    log_route.info(">>> REVIT AGENT (DesktopAgent) START")
    result = {
        "desktop_result": {
            "app": "revit",
            "status": "stubbed",
            "message": "Revit agent placeholder executed; add Revit automation hooks here.",
            "query": getattr(state, "user_query", ""),
        },
        "selected_app": "revit",
    }
    log_route.info("<<< REVIT AGENT (DesktopAgent) DONE")
    return result


__all__ = ["node_revit_agent"]
