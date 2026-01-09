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
from nodes.DBRetrieval.image_nodes import node_generate_image_description, node_image_similarity_search

# Alias for backward compatibility with graph node names
node_generate_image_embeddings = node_generate_image_description


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
    """Route to retrieve (clarification logic removed - router always selects databases)"""
    return "retrieve"


def _router_dispatcher_to_image_or_retrieve(state) -> str:
    """Route from router_dispatcher to image processing or retrieve"""
    if isinstance(state, dict):
        images_base64 = state.get("images_base64")
        use_image_similarity = state.get("use_image_similarity", False)
    else:
        images_base64 = getattr(state, "images_base64", None)
        use_image_similarity = getattr(state, "use_image_similarity", False)
    
    if images_base64 and use_image_similarity:
        return "generate_image_embeddings"
    return "retrieve"


def _rag_to_image_or_retrieve(state) -> str:
    """Route from rag to image processing or retrieve"""
    if isinstance(state, dict):
        images_base64 = state.get("images_base64")
        use_image_similarity = state.get("use_image_similarity", False)
    else:
        images_base64 = getattr(state, "images_base64", None)
        use_image_similarity = getattr(state, "use_image_similarity", False)
    
    if images_base64 and use_image_similarity:
        return "generate_image_embeddings"
    return "retrieve"


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

    # Image processing nodes
    g.add_node("generate_image_embeddings", node_generate_image_embeddings)
    g.add_node("image_similarity_search", node_image_similarity_search)
    
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

    # Router dispatcher routes to image processing or retrieve (if images and similarity enabled)
    g.add_conditional_edges(
        "router_dispatcher",
        _router_dispatcher_to_image_or_retrieve,
        {
            "generate_image_embeddings": "generate_image_embeddings",
            "retrieve": "retrieve",
        },
    )

    # RAG routes to image processing or retrieve
    g.add_conditional_edges(
        "rag",
        _rag_to_image_or_retrieve,
        {
            "generate_image_embeddings": "generate_image_embeddings",
            "retrieve": "retrieve",
        },
    )
    
    # Image processing pipeline: description → similarity search → retrieve
    # (node generates VLM description, then text semantic search on image_descriptions table)
    g.add_edge("generate_image_embeddings", "image_similarity_search")
    g.add_edge("image_similarity_search", "retrieve")

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
