"""
LangGraph Builder
Constructs the RAG workflow graph
"""
from langgraph.graph import StateGraph, END
from models.rag_state import RAGState
from database import memory
from nodes.plan import node_plan
from nodes.route import node_route
from nodes.web_router import node_web_router
from nodes.desktop_router import node_desktop_router
from nodes.router_dispatcher import node_router_dispatcher
from nodes.retrieve import node_retrieve
from nodes.grade import node_grade
from nodes.answer import node_answer
from nodes.verify import node_verify, _verify_route
from nodes.correct import node_correct


def _router_route(state: RAGState) -> str:
    """Route to router dispatcher based on selected routers"""
    selected_routers = state.selected_routers or []
    if selected_routers:
        return "router_dispatcher"
    # Fallback to rag router if no routers selected
    return "route"


def build_graph():
    """Build the LangGraph workflow"""
    g = StateGraph(RAGState)

    # Add nodes
    g.add_node("plan", node_plan)
    g.add_node("route", node_route)  # Existing RAG router (unchanged)
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

    # Conditional routing from plan to router dispatcher
    g.add_conditional_edges(
        "plan",
        _router_route,
        {
            "router_dispatcher": "router_dispatcher",
            "route": "route"  # Fallback to existing route node
        }
    )
    
    # Router dispatcher routes to retrieve (after running all selected routers in parallel)
    g.add_edge("router_dispatcher", "retrieve")
    
    # Keep existing route path for backward compatibility
    g.add_edge("route", "retrieve")
    
    # Continue with existing flow
    g.add_edge("retrieve", "grade")
    g.add_edge("grade", "answer")
    g.add_edge("answer", "verify")

    # Conditional branch from verify
    g.add_conditional_edges(
        "verify",
        _verify_route,
        {"fix": "retrieve", "ok": "correct"}
    )

    g.add_edge("correct", END)

    return g.compile(checkpointer=memory)

