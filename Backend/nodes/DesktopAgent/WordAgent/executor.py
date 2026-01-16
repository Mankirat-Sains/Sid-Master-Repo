"""
DOCGEN: Execution wrapper for desktop actions.
This node never decides flow; it only executes requested desktop actions (if any) and records results.
"""
from __future__ import annotations

from models.desktop_agent_state import DesktopAgentState
from config.logging_config import log_query


def node_desktop_execute(state: DesktopAgentState) -> dict:
    """Execute desktop plan when requested; no-op otherwise."""
    log_query.info(f"DOCGEN: entered node_desktop_execute (requires={state.requires_desktop_action})")
    if not state.requires_desktop_action:
        return {}

    # Placeholder: hook Desktop Agent here. Respect execution-only constraint.
    result = {
        "desktop_execution": "simulated",
        "desktop_action_plan": state.desktop_action_plan,
    }
    if state.output_artifact_ref:
        result["output_artifact_ref"] = state.output_artifact_ref
    return result

