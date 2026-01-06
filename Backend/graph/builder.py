"""
LangGraph Builder
Constructs the RAG workflow graph
"""
from langgraph.graph import StateGraph, END
from models.rag_state import RAGState
from database import memory
# Legacy imports (kept for backwards compatibility)
from nodes.plan import node_plan
from nodes.route import node_route
# RAG node - wrapper that runs rag_plan and rag_router in parallel (triggered when top-level plan outputs "rag")
from nodes.rag import node_rag
# RAG sub-nodes (used internally by node_rag)
from nodes.rag_plan import node_rag_plan
from nodes.rag_router import node_rag_router
from nodes.retrieve import node_retrieve
from nodes.grade import node_grade
from nodes.answer import node_answer
from nodes.verify import node_verify, _verify_route
from nodes.correct import node_correct


def build_graph():
    """Build the LangGraph workflow"""
    g = StateGraph(RAGState)

    # Add nodes
    g.add_node("plan", node_plan)
    g.add_node("route", node_route)
    g.add_node("rag", node_rag)  # RAG node - triggered when plan node routes to "rag" (runs rag_plan and rag_router in parallel)
    g.add_node("retrieve", node_retrieve)
    g.add_node("grade", node_grade)
    g.add_node("answer", node_answer)
    g.add_node("verify", node_verify)
    g.add_node("correct", node_correct)

    # Entry point
    g.set_entry_point("plan")

    # NOTE: The plan node will conditionally route to either "route" (legacy) or "rag" (new parallel execution)
    # The conditional routing logic is handled within the plan node implementation
    # For now, we maintain the legacy flow: plan -> route
    # When plan node outputs "rag", it should route to "rag" node instead
    g.add_edge("plan", "route")
    
    # Conditional edge from rag - check if clarification is needed (when plan routes to rag)
    def _rag_condition(state):
        """Check if router needs clarification"""
        if isinstance(state, dict):
            needs_clarification = state.get("needs_clarification", False)
        else:
            needs_clarification = getattr(state, "needs_clarification", False)
        
        if needs_clarification:
            return "clarification"
        return "retrieve"
    
    g.add_conditional_edges(
        "rag",
        _rag_condition,
        {
            "clarification": END,
            "retrieve": "retrieve"
        }
    )
    
    # Conditional edge from route - check if clarification is needed
    def _route_condition(state):
        """Check if router needs clarification"""
        if isinstance(state, dict):
            needs_clarification = state.get("needs_clarification", False)
        else:
            needs_clarification = getattr(state, "needs_clarification", False)
        
        if needs_clarification:
            return "clarification"
        return "retrieve"
    
    g.add_conditional_edges(
        "route",
        _route_condition,
        {
            "clarification": END,
            "retrieve": "retrieve"
        }
    )
    
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

