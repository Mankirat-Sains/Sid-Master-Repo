"""
LangGraph Builder
Constructs the RAG workflow graph
"""
from langgraph.graph import StateGraph, END
from models.rag_state import RAGState
from database import memory

from nodes.plan import node_plan

# RAG node - wrapper that runs rag_plan and rag_router in parallel
from nodes.DBRetrieval.rag import node_rag

# Optional: sub-nodes used internally by node_rag (imports harmless if unused here)
from nodes.DBRetrieval.rag_plan import node_rag_plan  # noqa: F401
from nodes.DBRetrieval.rag_router import node_rag_router  # noqa: F401

from nodes.WebCalcs.web_router import node_web_router
from nodes.DesktopAgent.desktop_router import node_desktop_router
from nodes.router_dispatcher import node_router_dispatcher

from nodes.DBRetrieval.retrieve import node_retrieve
from nodes.DBRetrieval.grade import node_grade
from nodes.DBRetrieval.answer import node_answer
from nodes.DBRetrieval.verify import node_verify, _verify_route
from nodes.DBRetrieval.correct import node_correct


def _router_route(state: RAGState) -> str:
    """
    Planner routing:
    - If the plan selected any routers, run router_dispatcher first.
    - Otherwise go straight to rag.
    """
    selected_routers = getattr(state, "selected_routers", None) or []
    if selected_routers:
        return "router_dispatcher"
    return "rag"


def _rag_condition(state) -> str:
    """Check if router needs clarification"""
    if isinstance(state, dict):
        needs_clarification = state.get("needs_clarification", False)
    else:
        needs_clarification = getattr(state, "needs_clarification", False)

    return "clarification" if needs_clarification else "retrieve"


def build_graph():
    """Build the LangGraph workflow"""
    g = StateGraph(RAGState)

    # Add nodes
    g.add_node("plan", node_plan)

    # RAG wrapper node
    g.add_node("rag", node_rag)

    # Non-RAG routers + dispatcher
    g.add_node("web_router", node_web_router)
    g.add_node("desktop_router", node_desktop_router)
    g.add_node("router_dispatcher", node_router_dispatcher)

    g.add_node("retrieve", node_retrieve)
    g.add_node("grade", node_grade)
    g.add_node("answer", node_answer)
    g.add_node("verify", node_verify)
    g.add_node("correct", node_correct)

    # Entry point
    g.set_entry_point("plan")

    # Plan routes to either router_dispatcher or rag (NO legacy route)
    g.add_conditional_edges(
        "plan",
        _router_route,
        {
            "router_dispatcher": "router_dispatcher",
            "rag": "rag",
        },
    )

    # Router dispatcher routes to retrieve (after running selected routers)
    g.add_edge("router_dispatcher", "retrieve")

    # RAG routes to retrieve or END (clarification)
    g.add_conditional_edges(
        "rag",
        _rag_condition,
        {
            "clarification": END,
            "retrieve": "retrieve",
        },
    )

    # Continue with existing flow
    g.add_edge("retrieve", "grade")
    g.add_edge("grade", "answer")
    g.add_edge("answer", "verify")

    # Conditional branch from verify
    g.add_conditional_edges(
        "verify",
        _verify_route,
        {"fix": "retrieve", "ok": "correct"},
    )

    g.add_edge("correct", END)

    return g.compile(checkpointer=memory)
