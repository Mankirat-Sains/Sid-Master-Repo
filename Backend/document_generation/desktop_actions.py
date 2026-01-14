"""
Desktop action helpers used by document-generation workflows.

These functions are thin wrappers around the legacy docgen desktop planning/
execution placeholders. They remain intentionally lightweight while the real
desktop integrations live in the DesktopAgent tooling.
"""
from __future__ import annotations

from typing import Any, Dict, List

from models.rag_state import RAGState
from config.logging_config import log_query


def build_desktop_action_steps(state: RAGState) -> Dict[str, List[Dict[str, Any]]]:
    """
    Shape desktop action steps from a precomputed plan (if any).

    Keeps the legacy behaviour of returning an empty plan when no desktop
    actions were requested.
    """
    log_query.info("DOCGEN: entered build_desktop_action_steps")
    steps: List[Dict[str, Any]] = []
    plan = getattr(state, "desktop_action_plan", {}) or {}
    if plan:
        steps.append({"action": plan.get("action", "open"), "tool": plan.get("tool", "word")})
    return {"desktop_steps": steps}


def execute_desktop_actions(state: RAGState) -> Dict[str, Any]:
    """
    Execute prepared desktop steps.

    This is a no-op when no steps are present; otherwise it echoes the steps to
    mirror the previous placeholder implementation.
    """
    log_query.info("DOCGEN: entered execute_desktop_actions")
    steps: List[Dict[str, Any]] = getattr(state, "desktop_steps", []) or []
    if not steps:
        return {"desktop_execution": "noop"}
    return {
        "desktop_execution": "executed",
        "desktop_steps": steps,
    }


def run_desktop_execution(state: RAGState) -> Dict[str, Any]:
    """
    Run desktop execution if required.

    This wrapper preserves the legacy simulated execution behaviour, passing
    through any output artifact reference when present.
    """
    log_query.info("DOCGEN: entered run_desktop_execution (requires=%s)", getattr(state, "requires_desktop_action", None))
    if not getattr(state, "requires_desktop_action", False):
        return {}

    result = {
        "desktop_execution": "simulated",
        "desktop_action_plan": getattr(state, "desktop_action_plan", None),
    }
    if getattr(state, "output_artifact_ref", None):
        result["output_artifact_ref"] = state.output_artifact_ref
    return result


# Backwards-compatible aliases for existing graph wiring
node_doc_think = build_desktop_action_steps
node_doc_act = execute_desktop_actions
node_desktop_execute = run_desktop_execution

__all__ = [
    "build_desktop_action_steps",
    "execute_desktop_actions",
    "run_desktop_execution",
    "node_doc_think",
    "node_doc_act",
    "node_desktop_execute",
]
