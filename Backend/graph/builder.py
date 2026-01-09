"""
LangGraph Builder
Constructs the parent graph that orchestrates subgraphs (DBRetrieval, DesktopAgent/DocGeneration, WebCalcs, etc.)
"""
from langgraph.graph import StateGraph, END
from models.parent_state import ParentState
from config.logging_config import log_query
from nodes.plan import node_plan
from graph.subgraphs.db_retrieval_subgraph import call_db_retrieval_subgraph
from graph.subgraphs.desktop_agent_subgraph import call_desktop_agent_subgraph
from nodes.router_dispatcher import node_router_dispatcher
from nodes.DocGeneration.node_doc_task_classifier import node_doc_task_classifier


def _router_route(state: ParentState) -> str:
    """
    Planner routing:
    - If the plan selected any routers, run router_dispatcher first.
    - Otherwise go straight to db_retrieval subgraph.
    """
    selected_routers = getattr(state, "selected_routers", None) or []
    if selected_routers:
        return "router_dispatcher"
    return "db_retrieval"


def _doc_or_router(state: ParentState) -> str:
    """
    Route to desktop/doc generation when requested; otherwise follow router/db_retrieval flow.
    """
    if getattr(state, "workflow", None) == "docgen" or getattr(state, "task_type", None) in {"doc_section", "doc_report"}:
        return "desktop_agent"
    return _router_route(state)


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
    def _wrapped(state: ParentState, *args, **kwargs):
        _log_node_state(node_name, state)
        def get(field, default=None):
            if isinstance(state, dict):
                return state.get(field, default)
            return getattr(state, field, default)

        trace = list(get("execution_trace", []) or [])
        trace.append(node_name)
        verbose = list(get("execution_trace_verbose", []) or [])
        verbose.append(
            {
                "node": node_name,
                "task_type": get("task_type"),
                "workflow": get("workflow"),
                "desktop_policy": get("desktop_policy"),
                "requires_desktop_action": get("requires_desktop_action"),
                "doc_type": get("doc_type"),
                "section_type": get("section_type"),
                "has_desktop_plan": bool(get("desktop_action_plan")),
            }
        )

        result = fn(state, *args, **kwargs)
        if isinstance(result, dict):
            result = {
                **result,
                "execution_trace": trace,
                "execution_trace_verbose": verbose,
            }
        return result

    return _wrapped


def build_graph():
    """Build the parent LangGraph workflow."""
    g = StateGraph(ParentState)

    # Add nodes
    g.add_node("plan", _wrap_node("plan", node_plan))
    g.add_node("doc_task_classifier", _wrap_node("doc_task_classifier", node_doc_task_classifier))
    g.add_node("desktop_agent", _wrap_node("desktop_agent", call_desktop_agent_subgraph))
    g.add_node("db_retrieval", call_db_retrieval_subgraph)
    g.add_node("router_dispatcher", node_router_dispatcher)

    # Entry point
    g.set_entry_point("plan")

    # Plan -> doc classifier (decides doc branch vs existing)
    g.add_edge("plan", "doc_task_classifier")

    # Doc classifier routes to desktop/docgen or router/db_retrieval
    g.add_conditional_edges(
        "doc_task_classifier",
        _doc_or_router,
        {
            "desktop_agent": "desktop_agent",
            "router_dispatcher": "router_dispatcher",
            "db_retrieval": "db_retrieval",
        },
    )

    # Terminal edges for subgraphs
    g.add_edge("desktop_agent", END)
    g.add_edge("router_dispatcher", END)
    g.add_edge("db_retrieval", END)

    # Import checkpointer dynamically
    from graph.checkpointer import checkpointer
    return g.compile(checkpointer=checkpointer)
