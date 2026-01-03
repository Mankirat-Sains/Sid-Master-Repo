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
from nodes.image_nodes import node_generate_image_embeddings, node_image_similarity_search


def build_graph():
    """Build the LangGraph workflow"""
    g = StateGraph(RAGState)

    # Add nodes
    g.add_node("plan", node_plan)
    g.add_node("route", node_route)
    g.add_node("generate_image_embeddings", node_generate_image_embeddings)
    g.add_node("image_similarity", node_image_similarity_search)
    g.add_node("retrieve", node_retrieve)
    g.add_node("grade", node_grade)
    g.add_node("answer", node_answer)
    g.add_node("verify", node_verify)
    g.add_node("correct", node_correct)

    # Entry point
    g.set_entry_point("plan")

    # Linear part
    g.add_edge("plan", "route")
    
    # Conditional: After route, check if we need image similarity search
    def should_use_image_search(state: RAGState) -> str:
        """Determine if we should run image similarity search"""
        if state.use_image_similarity and state.images_base64:
            return "generate_image_embeddings"
        return "retrieve"
    
    g.add_conditional_edges(
        "route",
        should_use_image_search,
        {
            "generate_image_embeddings": "generate_image_embeddings",
            "retrieve": "retrieve"
        }
    )
    
    # Image embedding generation always goes to image similarity search
    g.add_edge("generate_image_embeddings", "image_similarity")
    
    # Image similarity search feeds into retrieve (to merge results)
    g.add_edge("image_similarity", "retrieve")
    
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

