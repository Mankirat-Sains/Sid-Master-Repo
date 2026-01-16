"""
Word Agent placeholder
Handles Word/DocX style desktop requests routed by the desktop router.
"""
from typing import Any, Dict

from models.desktop_agent_state import DesktopAgentState
from config.logging_config import log_route


def node_word_agent(state: DesktopAgentState) -> Dict[str, Any]:
    """
    Lightweight Word agent.
    Currently provides a structured stub so routing can complete without errors.
    Extend with real Word automation as needed.
    """
    log_route.info(">>> WORD AGENT (DesktopAgent) START")
    result = {
        "desktop_result": {
            "app": "word",
            "status": "stubbed",
            "message": "Word agent placeholder executed; add Word automation here.",
            "query": getattr(state, "user_query", ""),
        },
        "selected_app": "word",
    }
    log_route.info("<<< WORD AGENT (DesktopAgent) DONE")
    return result


__all__ = ["node_word_agent"]
