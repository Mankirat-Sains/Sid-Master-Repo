"""
LangGraph Builder
Constructs the RAG workflow graph
"""
from langgraph.graph import StateGraph, END
from models.parent_state import ParentState
# Import checkpointer dynamically in build_graph() to get the latest initialized version

from nodes.plan import node_plan

# Subgraph wrappers
from graph.subgraphs.db_retrieval_subgraph import call_db_retrieval_subgraph

from nodes.router_dispatcher import node_router_dispatcher


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


def build_graph():
    """Build the LangGraph workflow"""
    g = StateGraph(ParentState)

    # Add nodes
    g.add_node("plan", node_plan)

    # Subgraphs (all capability branches are now subgraphs)
    g.add_node("db_retrieval", call_db_retrieval_subgraph)

    # Router dispatcher (handles routing to WebCalcs, DesktopAgent, and DBRetrieval subgraphs)
    g.add_node("router_dispatcher", node_router_dispatcher)

    # Entry point
    g.set_entry_point("plan")

    # Plan routes to either router_dispatcher or db_retrieval subgraph
    g.add_conditional_edges(
        "plan",
        _router_route,
        {
            "router_dispatcher": "router_dispatcher",
            "db_retrieval": "db_retrieval",
        },
    )

    # Router dispatcher completes (it handles its own routing internally)
    # The subgraph handles all DBRetrieval pipeline internally
    g.add_edge("router_dispatcher", END)
    g.add_edge("db_retrieval", END)

    # Import checkpointer here to get the latest initialized version
    # (not at module level, since it may be initialized during FastAPI startup)
    from graph.checkpointer import checkpointer
    return g.compile(checkpointer=checkpointer)
