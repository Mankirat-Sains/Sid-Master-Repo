"""
DBRetrieval Subgraph
Complete RAG pipeline for database retrieval as a subgraph.
"""
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from langgraph.graph import StateGraph, END
from models.db_retrieval_state import DBRetrievalState
from models.parent_state import ParentState
from config.logging_config import log_query, log_route
from graph.tracing import wrap_subgraph_node

# Import all DBRetrieval nodes
from nodes.DBRetrieval.SQLdb.rag_plan import node_rag_plan
from nodes.DBRetrieval.SQLdb.rag_router import node_rag_router
from nodes.DBRetrieval.SQLdb.retrieve import node_retrieve
from nodes.DBRetrieval.SQLdb.grade import node_grade
from nodes.DBRetrieval.SQLdb.answer import node_answer
from nodes.DBRetrieval.SQLdb.verify import node_verify, _verify_route
from nodes.DBRetrieval.SQLdb.correct import node_correct
from nodes.DBRetrieval.SQLdb.image_nodes import node_generate_image_description, node_image_similarity_search


def node_rag_plan_router(state: DBRetrievalState) -> dict:
    """Run rag_plan and rag_router in parallel and merge results."""
    t_start = time.time()
    log_query.info(">>> RAG PLAN & ROUTER START (running in parallel)")

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_plan = executor.submit(node_rag_plan, state)
            future_router = executor.submit(node_rag_router, state)
            plan_result = future_plan.result()
            router_result = future_router.result()

        merged_result = {
            "query_plan": plan_result.get("query_plan"),
            "expanded_queries": plan_result.get("expanded_queries", []),
            "data_route": router_result.get("data_route"),
            "data_sources": router_result.get("data_sources"),
            "project_filter": router_result.get("project_filter"),
            "needs_clarification": False,
        }

        t_elapsed = time.time() - t_start
        log_query.info(f"<<< RAG PLAN & ROUTER DONE in {t_elapsed:.2f}s")
        log_query.info(f"   Merged results: plan steps={len(plan_result.get('query_plan', {}).get('steps', []))}, databases={router_result.get('data_sources', {})}")
        return merged_result

    except Exception as e:
        log_query.error(f"RAG plan & router node failed: {e}")
        import traceback
        traceback.print_exc()
        log_query.warning("⚠️ Parallel execution failed, falling back to sequential")
        try:
            plan_result = node_rag_plan(state)
            router_result = node_rag_router(state)
            return {
                "query_plan": plan_result.get("query_plan"),
                "expanded_queries": plan_result.get("expanded_queries", []),
                "data_route": router_result.get("data_route"),
                "data_sources": router_result.get("data_sources"),
                "project_filter": router_result.get("project_filter"),
                "needs_clarification": False,
            }
        except Exception as e2:
            log_query.error(f"Sequential fallback also failed: {e2}")
            return {
                "query_plan": None,
                "expanded_queries": [state.user_query],
                "data_route": "smart",
                "data_sources": {"project_db": True, "code_db": False, "coop_manual": False, "speckle_db": False},
                "project_filter": None,
                "needs_clarification": False,
            }


def _rag_plan_router_to_image_or_retrieve(state: DBRetrievalState) -> str:
    """Route from rag_plan_router to image processing or retrieve."""
    images_base64 = state.get("images_base64") if isinstance(state, dict) else getattr(state, "images_base64", None)
    use_image_similarity = state.get("use_image_similarity", False) if isinstance(state, dict) else getattr(state, "use_image_similarity", False)
    needs_retrieval = state.get("needs_retrieval", True) if isinstance(state, dict) else getattr(state, "needs_retrieval", True)
    retrieval_completed = state.get("retrieval_completed", False) if isinstance(state, dict) else getattr(state, "retrieval_completed", False)

    # Skip retrieval entirely when not needed or already done
    if not needs_retrieval or retrieval_completed:
        return "grade"

    if images_base64 and use_image_similarity:
        return "generate_image_embeddings"
    return "retrieve"


def build_db_retrieval_subgraph():
    """Build the DBRetrieval subgraph."""
    g = StateGraph(DBRetrievalState)

    g.add_node("rag_plan_router", wrap_subgraph_node("rag_plan_router")(node_rag_plan_router))
    g.add_node("generate_image_embeddings", wrap_subgraph_node("generate_image_embeddings")(node_generate_image_description))
    g.add_node("image_similarity_search", wrap_subgraph_node("image_similarity_search")(node_image_similarity_search))
    g.add_node("retrieve", wrap_subgraph_node("retrieve")(node_retrieve))
    g.add_node("grade", wrap_subgraph_node("grade")(node_grade))
    g.add_node("answer", wrap_subgraph_node("answer")(node_answer))
    g.add_node("verify", wrap_subgraph_node("verify")(node_verify))
    g.add_node("correct", wrap_subgraph_node("correct")(node_correct))

    g.set_entry_point("rag_plan_router")

    g.add_conditional_edges(
        "rag_plan_router",
        _rag_plan_router_to_image_or_retrieve,
        {
            "generate_image_embeddings": "generate_image_embeddings",
            "retrieve": "retrieve",
            "grade": "grade",
        },
    )
    g.add_edge("generate_image_embeddings", "image_similarity_search")
    g.add_edge("image_similarity_search", "retrieve")
    g.add_edge("retrieve", "grade")
    g.add_edge("grade", "answer")
    g.add_edge("answer", "verify")
    g.add_conditional_edges("verify", _verify_route, {"fix": "retrieve", "ok": "correct"})
    g.add_edge("correct", END)

    return g.compile()


_db_retrieval_subgraph = None


def call_db_retrieval_subgraph(state: ParentState) -> dict:
    """
    Wrapper node that invokes the DBRetrieval subgraph from the parent graph.
    Transforms ParentState → DBRetrievalState → invokes subgraph → transforms result back.
    """
    global _db_retrieval_subgraph

    if _db_retrieval_subgraph is None:
        log_query.info("🔧 Initializing DBRetrieval subgraph...")
        _db_retrieval_subgraph = build_db_retrieval_subgraph()
        log_query.info("✅ DBRetrieval subgraph initialized")

    db_input = DBRetrievalState(
        session_id=state.session_id,
        user_query=state.user_query,
        original_question=state.original_question,
        user_role=state.user_role,
        messages=state.messages,
        data_sources=getattr(state, "data_sources", None),
        project_filter=getattr(state, "project_filter", None),
        images_base64=state.images_base64,
        conversation_history=getattr(state, "conversation_history", []),
    )

    parent_trace = getattr(state, "execution_trace", []) or []
    parent_verbose = getattr(state, "execution_trace_verbose", []) or []

    try:
        db_result = _db_retrieval_subgraph.invoke(asdict(db_input))
        return {
            "db_retrieval_result": db_result.get("final_answer"),
            "db_retrieval_citations": db_result.get("answer_citations", []),
            "db_retrieval_code_answer": db_result.get("code_answer"),
            "db_retrieval_code_citations": db_result.get("code_citations", []),
            "db_retrieval_coop_answer": db_result.get("coop_answer"),
            "db_retrieval_coop_citations": db_result.get("coop_citations", []),
            "db_retrieval_follow_up_questions": db_result.get("follow_up_questions", []),
            "db_retrieval_follow_up_suggestions": db_result.get("follow_up_suggestions", []),
            "db_retrieval_selected_projects": db_result.get("selected_projects", []),
            "db_retrieval_route": db_result.get("data_route"),
            "db_retrieval_image_similarity_results": db_result.get("image_similarity_results", []),
            "db_retrieval_expanded_queries": db_result.get("expanded_queries", []),
            "db_retrieval_support_score": db_result.get("answer_support_score", 0.0),
            "conversation_history": db_result.get("conversation_history", []),
            "messages": db_result.get("messages", []),
            "project_filter": db_result.get("project_filter"),
            "execution_trace": parent_trace + (db_result.get("execution_trace", []) or []),
            "execution_trace_verbose": parent_verbose + (db_result.get("execution_trace_verbose", []) or []),
        }
    except Exception as e:
        log_query.error(f"❌ DBRetrieval subgraph failed: {e}")
        import traceback
        traceback.print_exc()
        return {"db_retrieval_result": None}
