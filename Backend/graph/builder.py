"""
LangGraph Builder
Constructs the RAG workflow graph
"""
from langgraph.graph import StateGraph, END
from models.rag_state import RAGState
from database import memory
from config.logging_config import log_query

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
from nodes.DBRetrieval.image_nodes import node_generate_image_embeddings, node_image_similarity_search
# Doc generation nodes
from nodes.DocGeneration.node_doc_task_classifier import node_doc_task_classifier
from nodes.DocGeneration.node_doc_plan import node_doc_plan
from nodes.DocGeneration.node_desktop_execute import node_desktop_execute
from nodes.DocGeneration.node_doc_generate_section import node_doc_generate_section
from nodes.DocGeneration.node_doc_generate_report import node_doc_generate_report
from nodes.DocGeneration.node_doc_answer_adapter import node_doc_answer_adapter
from nodes.DocGeneration.node_doc_think import node_doc_think
from nodes.DocGeneration.node_doc_act import node_doc_act


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


def _doc_or_router(state: RAGState) -> str:
    """
    Route to doc generation when requested; otherwise follow existing router/rag flow.
    """
    if getattr(state, "workflow", None) == "docgen" or getattr(state, "task_type", None) in {"doc_section", "doc_report"}:
        return "doc_plan"
    return _router_route(state)


def _doc_generate_route(state: RAGState) -> str:
    """Route to section vs report generation."""
    if getattr(state, "task_type", None) == "doc_report":
        return "doc_generate_report"
    return "doc_generate_section"


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
    def _wrapped(state: RAGState, *args, **kwargs):
        _log_node_state(node_name, state)
        return fn(state, *args, **kwargs)

    return _wrapped


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
    g.add_node("plan", _wrap_node("plan", node_plan))
    g.add_node("doc_task_classifier", _wrap_node("doc_task_classifier", node_doc_task_classifier))
    g.add_node("doc_plan", _wrap_node("doc_plan", node_doc_plan))
    g.add_node("desktop_execute", _wrap_node("desktop_execute", node_desktop_execute))
    g.add_node("doc_generate_section", _wrap_node("doc_generate_section", node_doc_generate_section))
    g.add_node("doc_generate_report", _wrap_node("doc_generate_report", node_doc_generate_report))
    g.add_node("doc_answer_adapter", _wrap_node("doc_answer_adapter", node_doc_answer_adapter))
    g.add_node("doc_think", _wrap_node("doc_think", node_doc_think))
    g.add_node("doc_act", _wrap_node("doc_act", node_doc_act))

    # RAG wrapper node
    g.add_node("rag", _wrap_node("rag", node_rag))

    # Non-RAG routers + dispatcher
    g.add_node("web_router", _wrap_node("web_router", node_web_router))
    g.add_node("desktop_router", _wrap_node("desktop_router", node_desktop_router))
    g.add_node("router_dispatcher", _wrap_node("router_dispatcher", node_router_dispatcher))

    # Image processing nodes
    g.add_node("generate_image_embeddings", _wrap_node("generate_image_embeddings", node_generate_image_embeddings))
    g.add_node("image_similarity_search", _wrap_node("image_similarity_search", node_image_similarity_search))
    
    g.add_node("retrieve", _wrap_node("retrieve", node_retrieve))
    g.add_node("grade", _wrap_node("grade", node_grade))
    g.add_node("answer", _wrap_node("answer", node_answer))
    g.add_node("verify", _wrap_node("verify", node_verify))
    g.add_node("correct", _wrap_node("correct", node_correct))

    # Entry point
    g.set_entry_point("plan")

    # Plan -> doc classifier (decides doc branch vs existing)
    g.add_edge("plan", "doc_task_classifier")

    # Doc classifier routes to doc_plan (doc generation) or router/rag (existing)
    g.add_conditional_edges(
        "doc_task_classifier",
        _doc_or_router,
        {
            "doc_plan": "doc_plan",
            "router_dispatcher": "router_dispatcher",
            "rag": "rag",
        },
    )

    # Doc generation branch
    g.add_edge("doc_plan", "desktop_router")
    g.add_edge("desktop_router", "doc_think")
    g.add_edge("doc_think", "doc_act")
    g.add_conditional_edges(
        "doc_act",
        _doc_generate_route,
        {
            "doc_generate_section": "doc_generate_section",
            "doc_generate_report": "doc_generate_report",
        },
    )
    g.add_edge("doc_generate_section", "doc_answer_adapter")
    g.add_edge("doc_generate_report", "doc_answer_adapter")
    g.add_edge("doc_answer_adapter", "verify")

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
    
    # Image processing pipeline: embeddings → similarity search → retrieve
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
