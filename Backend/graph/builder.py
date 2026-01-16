"""
LangGraph Builder
Constructs the parent graph that orchestrates subgraphs (DBRetrieval, DesktopAgent/DocGeneration, WebCalcs, etc.)
"""
import time
from dataclasses import MISSING, asdict, fields

from langgraph.graph import StateGraph, END

from models.parent_state import ParentState
from models.rag_state import RAGState
from config.logging_config import log_query
from config.settings import DEEP_AGENT_ENABLED
from utils.path_setup import ensure_info_retrieval_on_path

ensure_info_retrieval_on_path()
from nodes.plan import node_plan
from nodes.router_dispatcher import node_router_dispatcher


def _get_state_field(state, field, default=None):
    """Return a field from either a dataclass state or a dict state."""
    if isinstance(state, dict):
        return state.get(field, default)
    return getattr(state, field, default)


def _convert_to_rag_state(state) -> RAGState:
    """Convert a dict or ParentState-like object into RAGState with defaults."""
    if isinstance(state, RAGState):
        return state

    state_dict = state if isinstance(state, dict) else asdict(state)
    rag_fields = {f.name: f for f in fields(RAGState)}

    normalized = {}
    extras = {}
    for key, value in state_dict.items():
        if key in rag_fields:
            normalized[key] = value
        else:
            extras[key] = value

    for name, f in rag_fields.items():
        if name in normalized:
            continue
        if f.default_factory is not MISSING:  # type: ignore[attr-defined]
            normalized[name] = f.default_factory()  # type: ignore[call-arg]
        elif f.default is not MISSING:
            normalized[name] = f.default
        else:
            normalized[name] = None

    rag_state = RAGState(**normalized)
    for key, value in extras.items():
        setattr(rag_state, key, value)
    return rag_state


<<<<<<< HEAD
def _router_route(state: RAGState) -> str:
    """
    Planner routing:
    - If the plan selected any routers, run router_dispatcher first.
    - Otherwise go straight to db_retrieval subgraph.
    """
    selected_routers = _get_state_field(state, "selected_routers", []) or []
    if selected_routers:
        return "router_dispatcher"
    return "db_retrieval"


def _plan_to_router_or_doc_classifier(state: RAGState) -> str:
    """
    After plan node: Check if planner selected RAG router.
    - If planner selected "rag", go directly to router_dispatcher (skip doc classifier)
    - Otherwise, check doc_task_classifier to see if it's a doc generation request
    """
    selected_routers = _get_state_field(state, "selected_routers", []) or []
    # If planner explicitly selected RAG, respect that decision and skip doc classifier
    if "rag" in selected_routers:
        return "router_dispatcher"
    # Otherwise, let doc classifier determine if it's doc generation
    return "doc_task_classifier"


def _doc_or_router(state: RAGState) -> str:
    """
    Route to desktop/doc generation when requested; otherwise follow router/db_retrieval flow.
    """
    workflow = _get_state_field(state, "workflow")
    task_type = _get_state_field(state, "task_type")
    if workflow == "docgen" or task_type in {"doc_section", "doc_report"}:
        return "desktop_agent"
    return _router_route(state)
=======
>>>>>>> 069be303bd5b6910ab2e1a78bc142bfbafba3541


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

    def _wrapped(state: RAGState, *args, **kwargs):
        state = _convert_to_rag_state(state)
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
    g = StateGraph(RAGState)

    g.add_node("plan", _wrap_node("plan", node_plan))
    g.add_node("router_dispatcher", _wrap_node("router_dispatcher", node_router_dispatcher))

    g.set_entry_point("plan")

<<<<<<< HEAD
    # After plan: if planner selected RAG, go directly to router_dispatcher
    # Otherwise, check doc_task_classifier to see if it's doc generation
    g.add_conditional_edges(
        "plan",
        _plan_to_router_or_doc_classifier,
        {
            "router_dispatcher": "router_dispatcher",
            "doc_task_classifier": "doc_task_classifier",
        },
    )
    
    # After doc_task_classifier: route based on workflow/task_type
    g.add_conditional_edges(
        "doc_task_classifier",
        _doc_or_router,
        {
            "desktop_agent": "desktop_agent",
            "router_dispatcher": "router_dispatcher",
            "db_retrieval": "db_retrieval",
        },
    )

    g.add_edge("desktop_agent", END)
=======
    # Plan goes directly to router_dispatcher which handles routing to:
    # - db_retrieval subgraph (if "rag" in selected_routers)
    # - webcalcs subgraph (if "web" in selected_routers)
    # - desktop_agent subgraph (if "desktop" in selected_routers)
    g.add_edge("plan", "router_dispatcher")
>>>>>>> 069be303bd5b6910ab2e1a78bc142bfbafba3541
    g.add_edge("router_dispatcher", END)

    from graph.checkpointer import checkpointer

    return g.compile(checkpointer=checkpointer)
