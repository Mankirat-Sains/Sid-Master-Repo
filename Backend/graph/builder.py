"""
LangGraph Builder
Constructs the RAG workflow graph
"""
from langgraph.graph import StateGraph, END
from models.rag_state import RAGState
from database import memory
from nodes.plan import node_plan
from nodes.route import node_route
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
    g.add_node("retrieve", node_retrieve)
    g.add_node("grade", node_grade)
    g.add_node("answer", node_answer)
    g.add_node("verify", node_verify)
    g.add_node("correct", node_correct)

    # Entry point
    g.set_entry_point("plan")

    # Linear part
    g.add_edge("plan", "route")
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

