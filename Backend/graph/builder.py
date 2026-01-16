"""
LangGraph Builder
Constructs the parent graph that orchestrates subgraphs (DBRetrieval, DesktopAgent/DocGeneration, WebCalcs, etc.)
"""
import time
from dataclasses import MISSING, asdict, fields

from langgraph.graph import StateGraph, END

from models.orchestration_state import OrchestrationState
from config.logging_config import log_query
from utils.path_setup import ensure_info_retrieval_on_path

ensure_info_retrieval_on_path()
from nodes.plan import node_plan
from nodes.router_dispatcher import node_router_dispatcher
from graph.subgraphs import (
    call_db_retrieval_subgraph,
    call_desktop_agent_subgraph,
)


def _get_state_field(state, field, default=None):
    """Return a field from either a dataclass state or a dict state."""
    if isinstance(state, dict):
        return state.get(field, default)
    return getattr(state, field, default)


def _router_route(state: OrchestrationState) -> str:
    """
    Planner routing:
    - If the plan selected any routers, run router_dispatcher first.
    - Otherwise go straight to db_retrieval subgraph.
    """
    selected_routers = _get_state_field(state, "selected_routers", []) or []
    if selected_routers:
        return "router_dispatcher"
    return "db_retrieval"


def _log_node_state(node_name: str, state) -> None:
    def get(field, default=None):
        if isinstance(state, dict):
            return state.get(field, default)
        return getattr(state, field, default)

    log_query.info(
        "ROUTE TRACE | node=%s | task_type=%s | requires_desktop_action=%s | doc_type=%s | section_type=%s | desktop_plan=%s",
        node_name,
        get("task_type"),
        get("requires_desktop_action"),
        get("doc_type"),
        get("section_type"),
        "yes" if get("desktop_action_plan") else "no",
    )


def _wrap_node(node_name: str, fn):
    def _merge_trace(parent_trace, result_trace):
        parent_trace = list(parent_trace or [])
        result_trace = list(result_trace or [])

        if result_trace:
            if parent_trace and result_trace[: len(parent_trace)] == parent_trace:
                merged = list(result_trace)
                insert_at = len(parent_trace)
                if node_name not in merged[insert_at : insert_at + 1]:
                    merged.insert(insert_at, node_name)
                return merged
            return parent_trace + [node_name] + result_trace
        return parent_trace + [node_name]

    def _merge_verbose(parent_verbose, node_entry, result_verbose):
        parent_verbose = list(parent_verbose or [])
        result_verbose = list(result_verbose or [])

        if result_verbose:
            if parent_verbose and result_verbose[: len(parent_verbose)] == parent_verbose:
                merged = list(result_verbose)
                merged.insert(len(parent_verbose), node_entry)
                return merged
            return parent_verbose + [node_entry] + result_verbose
        return parent_verbose + [node_entry]

    def _wrapped(state: OrchestrationState, *args, **kwargs):
        # Ensure state is OrchestrationState (or convert from dict)
        if isinstance(state, dict):
            # Convert dict to OrchestrationState with defaults
            state_dict = state
            orch_fields = {f.name: f for f in fields(OrchestrationState)}
            normalized = {}
            for key, value in state_dict.items():
                if key in orch_fields:
                    normalized[key] = value
            for name, f in orch_fields.items():
                if name not in normalized:
                    if f.default_factory is not MISSING:
                        normalized[name] = f.default_factory()
                    elif f.default is not MISSING:
                        normalized[name] = f.default
                    else:
                        normalized[name] = None
            state = OrchestrationState(**normalized)
        elif not isinstance(state, OrchestrationState):
            # Convert other state types to OrchestrationState
            state_dict = asdict(state) if hasattr(state, '__dict__') else dict(state)
            orch_fields = {f.name: f for f in fields(OrchestrationState)}
            normalized = {}
            for key, value in state_dict.items():
                if key in orch_fields:
                    normalized[key] = value
            for name, f in orch_fields.items():
                if name not in normalized:
                    if f.default_factory is not MISSING:
                        normalized[name] = f.default_factory()
                    elif f.default is not MISSING:
                        normalized[name] = f.default
                    else:
                        normalized[name] = None
            state = OrchestrationState(**normalized)
        
        _log_node_state(node_name, state)

        def get(field, default=None):
            if isinstance(state, dict):
                return state.get(field, default)
            return getattr(state, field, default)

        parent_trace = list(get("execution_trace", []) or [])
        parent_verbose = list(get("execution_trace_verbose", []) or [])

        current_verbose_entry = {
            "node": node_name,
            "task_type": get("task_type"),
            "workflow": get("workflow"),
            "desktop_policy": get("desktop_policy"),
            "requires_desktop_action": get("requires_desktop_action"),
            "doc_type": get("doc_type"),
            "section_type": get("section_type"),
            "has_desktop_plan": bool(get("desktop_action_plan")),
            "timestamp": time.time(),
        }

        result = fn(state, *args, **kwargs)
        if not isinstance(result, dict):
            result = {"_raw_result": result}

        result_trace = result.get("execution_trace", []) or []
        result_verbose = result.get("execution_trace_verbose", []) or []

        merged_trace = _merge_trace(parent_trace, result_trace)
        merged_verbose = _merge_verbose(parent_verbose, current_verbose_entry, result_verbose)

        return {
            **result,
            "execution_trace": merged_trace,
            "execution_trace_verbose": merged_verbose,
        }

    return _wrapped


def build_graph():
    """Build the parent LangGraph workflow."""
    g = StateGraph(OrchestrationState)

    g.add_node("plan", _wrap_node("plan", node_plan))
    g.add_node("desktop_agent", _wrap_node("desktop_agent", call_desktop_agent_subgraph))
    g.add_node("db_retrieval", _wrap_node("db_retrieval", call_db_retrieval_subgraph))
    g.add_node("router_dispatcher", _wrap_node("router_dispatcher", node_router_dispatcher))

    g.set_entry_point("plan")

    # Route directly from plan based on selected_routers
    g.add_conditional_edges(
        "plan",
        _router_route,
        {
            "router_dispatcher": "router_dispatcher",
            "db_retrieval": "db_retrieval",
        },
    )

    g.add_edge("desktop_agent", END)
    g.add_edge("router_dispatcher", END)
    g.add_edge("db_retrieval", END)

    from graph.checkpointer import checkpointer

    return g.compile(checkpointer=checkpointer)
