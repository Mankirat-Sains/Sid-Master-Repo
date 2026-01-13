"""
Utilities for deep desktop agent integration.

Provides helpers for feature flags, state safety, interrupt handling,
workspace operations, and user-facing action summaries.
"""
import json
import logging
from copy import deepcopy
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from config.settings import (
    DEEP_AGENT_ENABLED,
    WORKSPACE_BASE_PATH,
    WORKSPACE_RETENTION_HOURS,
    MAX_DEEP_AGENT_ITERATIONS,
    INTERRUPT_DESTRUCTIVE_ACTIONS,
)
from persistence.workspace_manager import get_workspace_manager

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Feature flag & state checks
# ---------------------------------------------------------------------------
def is_deep_agent_enabled() -> bool:
    """Check if deep agent feature is enabled."""
    try:
        return bool(DEEP_AGENT_ENABLED)
    except Exception as exc:  # pragma: no cover - defensive
        logger.error(f"Failed to read DEEP_AGENT_ENABLED: {exc}")
        return False


def should_use_deep_agent(state: Dict[str, Any]) -> bool:
    """
    Determine if the deep agent should be used based on workflow/task.
    Returns False if feature flag is off.
    """
    if not is_deep_agent_enabled():
        return False

    try:
        workflow = _get_state_value(state, "workflow", "")
        task_type = _get_state_value(state, "task_type", "")
        return workflow == "docgen" or task_type in {"doc_section", "doc_report"}
    except Exception as exc:  # pragma: no cover - defensive
        logger.error(f"Error determining deep agent usage: {exc}")
        return False


def get_deep_agent_state_summary(state: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a summary of deep agent state for logging/display."""
    safe_state = _safe_state_copy(state)
    try:
        return {
            "workflow": safe_state.get("workflow"),
            "task_type": safe_state.get("task_type"),
            "desktop_policy": safe_state.get("desktop_policy"),
            "requires_desktop_action": safe_state.get("requires_desktop_action"),
            "desktop_plan_steps": len(safe_state.get("desktop_plan_steps", []) or []),
            "desktop_iteration_count": safe_state.get("desktop_iteration_count", 0),
            "workspace_dir": safe_state.get("desktop_workspace_dir"),
            "workspace_files": len(safe_state.get("desktop_workspace_files", []) or []),
            "interrupt_pending": safe_state.get("desktop_interrupt_pending", False),
            "approved_actions": len(safe_state.get("desktop_approved_actions", []) or []),
        }
    except Exception as exc:  # pragma: no cover - defensive
        logger.error(f"Failed to build deep agent summary: {exc}")
        return {"error": str(exc)}


# ---------------------------------------------------------------------------
# Interrupt handling
# ---------------------------------------------------------------------------
def extract_interrupt_data(interrupt_exception) -> Dict[str, Any]:
    """Extract and format interrupt data from GraphInterrupt."""
    try:
        if hasattr(interrupt_exception, "interrupt_data"):
            data = interrupt_exception.interrupt_data or {}
        elif hasattr(interrupt_exception, "data"):
            data = interrupt_exception.data or {}
        else:
            data = {}

        data = _safe_state_copy(data)
        data.setdefault("action_id", "unknown")
        data.setdefault("action", "unknown")
        data.setdefault("timestamp", datetime.utcnow().isoformat())
        return data
    except Exception as exc:  # pragma: no cover - defensive
        logger.error(f"Error extracting interrupt data: {exc}")
        return {"error": str(exc), "action_id": "error"}


def create_approval_payload(action_id: str, approved: bool, reason: str = "") -> Dict[str, Any]:
    """Create payload for action approval API."""
    return {
        "action_id": action_id,
        "approved": bool(approved),
        "reason": reason or "",
        "timestamp": datetime.utcnow().isoformat(),
    }


def validate_action_approval(state: Dict[str, Any], action_id: str) -> bool:
    """Check if an action has been approved in the state."""
    try:
        approved_actions = _get_state_value(state, "desktop_approved_actions", []) or []
        return isinstance(approved_actions, list) and action_id in approved_actions
    except Exception as exc:  # pragma: no cover - defensive
        logger.error(f"Error validating action approval: {exc}")
        return False


# ---------------------------------------------------------------------------
# Workspace management
# ---------------------------------------------------------------------------
def get_workspace_summary(thread_id: str) -> Dict[str, Any]:
    """Get summary of workspace contents for a thread."""
    try:
        mgr = get_workspace_manager()
        snapshot = mgr.get_workspace_snapshot(thread_id)
        size_stats = mgr.get_size_stats(thread_id)
        return {
            "workspace_path": snapshot.get("workspace_path"),
            "file_count": snapshot.get("file_count"),
            "files": snapshot.get("files", []),
            "size_bytes": size_stats.get("total_size_bytes"),
            "size_mb": size_stats.get("total_size_mb"),
        }
    except Exception as exc:  # pragma: no cover - defensive
        logger.error(f"Failed to build workspace summary for {thread_id}: {exc}")
        return {"error": str(exc), "workspace_path": None}


def cleanup_old_workspaces(hours: Optional[int] = None) -> Dict[str, Any]:
    """Clean up workspace directories older than specified hours."""
    retention = hours if hours is not None else WORKSPACE_RETENTION_HOURS
    base = Path(WORKSPACE_BASE_PATH)
    removed: List[str] = []

    try:
        if not base.exists():
            return {"removed": [], "base": str(base), "note": "base_missing"}

        cutoff = datetime.utcnow() - timedelta(hours=retention)
        for child in base.iterdir():
            if not child.is_dir():
                continue
            try:
                modified = datetime.utcfromtimestamp(child.stat().st_mtime)
                if modified < cutoff:
                    for path in child.rglob("*"):
                        if path.is_file():
                            path.unlink(missing_ok=True)
                    child.rmdir()
                    removed.append(str(child))
            except Exception as exc:
                logger.warning(f"Failed to clean workspace {child}: {exc}")

        return {"removed": removed, "base": str(base)}
    except Exception as exc:  # pragma: no cover - defensive
        logger.error(f"Workspace cleanup failed: {exc}")
        return {"error": str(exc), "removed": removed, "base": str(base)}


# ---------------------------------------------------------------------------
# Action processing
# ---------------------------------------------------------------------------
def format_desktop_action_for_display(action_data: Dict[str, Any]) -> Dict[str, Any]:
    """Format desktop action data for user display."""
    data = _safe_state_copy(action_data)
    try:
        return {
            "action_id": data.get("action_id") or data.get("id") or "unknown",
            "action": data.get("action") or data.get("type") or "unknown",
            "reasoning": data.get("reasoning") or data.get("thought"),
            "params": data.get("params", {}),
            "timestamp": data.get("timestamp") or datetime.utcnow().isoformat(),
        }
    except Exception as exc:  # pragma: no cover - defensive
        logger.error(f"Failed to format desktop action: {exc}")
        return {"error": str(exc)}


def generate_action_summary(action_result: Dict[str, Any]) -> str:
    """Generate human-readable summary of action results."""
    data = _safe_state_copy(action_result)
    try:
        action = data.get("action", {})
        observation = data.get("observation", {})
        status = observation.get("status") or observation.get("summary") or "completed"
        action_name = action.get("action") or action.get("type") or "action"
        tool_result = action.get("result") or data.get("desktop_loop_result") or ""
        if isinstance(tool_result, (dict, list)):
            try:
                tool_result = json.dumps(tool_result)[:300]
            except Exception:
                tool_result = str(tool_result)[:300]

        parts = [
            f"Action: {action_name}",
            f"Status: {status}",
        ]
        if observation.get("has_error"):
            parts.append(f"Error: {observation.get('error')}")
        if tool_result:
            parts.append(f"Result: {str(tool_result)[:200]}")

        return " | ".join(parts)
    except Exception as exc:  # pragma: no cover - defensive
        logger.error(f"Failed to generate action summary: {exc}")
        return f"Action summary unavailable: {exc}"


# ---------------------------------------------------------------------------
# State conversion & validation
# ---------------------------------------------------------------------------
def ensure_rag_state_compatibility(state: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure state has all required RAGState fields with defaults."""
    base = _safe_state_copy(state)

    defaults = {
        "desktop_plan_steps": [],
        "desktop_current_step": 0,
        "desktop_iteration_count": 0,
        "desktop_workspace_dir": None,
        "desktop_workspace_files": [],
        "desktop_memories": [],
        "desktop_context": {},
        "desktop_interrupt_pending": False,
        "desktop_approved_actions": [],
        "desktop_interrupt_data": None,
        "tool_execution_log": [],
        "large_output_refs": {},
        "desktop_loop_result": None,
        "workflow": base.get("workflow", "qa"),
        "task_type": base.get("task_type", "qa"),
        "doc_type": base.get("doc_type", ""),
        "section_type": base.get("section_type", ""),
        "desktop_policy": base.get("desktop_policy", "never"),
        "requires_desktop_action": base.get("requires_desktop_action", False),
        "desktop_action_plan": base.get("desktop_action_plan", {}),
    }

    for key, default in defaults.items():
        if key not in base:
            base[key] = deepcopy(default)
    return base


def validate_deep_agent_state(state: Dict[str, Any]) -> List[str]:
    """Validate deep agent state fields, return list of issues."""
    issues: List[str] = []
    try:
        if not isinstance(state.get("desktop_plan_steps", []), list):
            issues.append("desktop_plan_steps should be a list")
        if not isinstance(state.get("desktop_iteration_count", 0), int):
            issues.append("desktop_iteration_count should be an int")
        if not isinstance(state.get("desktop_workspace_files", []), list):
            issues.append("desktop_workspace_files should be a list")
        if not isinstance(state.get("desktop_context", {}), dict):
            issues.append("desktop_context should be a dict")
        if not isinstance(state.get("desktop_approved_actions", []), list):
            issues.append("desktop_approved_actions should be a list")
        if not isinstance(state.get("tool_execution_log", []), list):
            issues.append("tool_execution_log should be a list")

        iter_count = state.get("desktop_iteration_count", 0)
        if isinstance(iter_count, int) and iter_count > MAX_DEEP_AGENT_ITERATIONS:
            issues.append("desktop_iteration_count exceeds MAX_DEEP_AGENT_ITERATIONS")

        if INTERRUPT_DESTRUCTIVE_ACTIONS and not isinstance(
            state.get("desktop_interrupt_pending", False), bool
        ):
            issues.append("desktop_interrupt_pending should be a bool")
    except Exception as exc:  # pragma: no cover - defensive
        logger.error(f"Error validating deep agent state: {exc}")
        issues.append(f"validation_error: {exc}")

    return issues


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
def _safe_state_copy(state: Any) -> Dict[str, Any]:
    """Return a shallow copy of state as dict without mutating the input."""
    if isinstance(state, dict):
        return dict(state)
    if hasattr(state, "__dict__"):
        return dict(state.__dict__)
    return {}


def _get_state_value(state: Any, key: str, default: Any = None) -> Any:
    """Safely get a value from dict or dataclass-like state."""
    if isinstance(state, dict):
        return state.get(key, default)
    return getattr(state, key, default)
