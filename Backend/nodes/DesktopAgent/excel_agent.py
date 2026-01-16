"""
Excel Agent wrapper
Routes desktop Excel requests through the existing Excel KB agent implementation.
"""
from models.desktop_agent_state import DesktopAgentState
from config.logging_config import log_route
from nodes.DesktopAgent.excel_kb_agent import node_excel_kb_agent


def node_excel_agent(state: DesktopAgentState) -> dict:
    """Delegate to the Excel KB agent while preserving desktop agent routing metadata."""
    log_route.info(">>> EXCEL AGENT (DesktopAgent) START")
    result = node_excel_kb_agent(state)
    log_route.info("<<< EXCEL AGENT (DesktopAgent) DONE")
    return result


__all__ = ["node_excel_agent"]
