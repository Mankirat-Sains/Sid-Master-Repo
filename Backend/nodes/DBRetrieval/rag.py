"""
RAG Node - Wrapper that runs rag_plan and rag_router in parallel
This node is triggered when the top-level plan node outputs "rag"
"""
import time
from concurrent.futures import ThreadPoolExecutor
from models.rag_state import RAGState
from config.logging_config import log_query, log_route
from .rag_plan import node_rag_plan
from .rag_router import node_rag_router


def node_rag(state: RAGState) -> dict:
    """
    RAG Node - Runs rag_plan and rag_router in parallel.
    This is triggered when the top-level plan node outputs "rag".
    
    Both sub-nodes run simultaneously using ThreadPoolExecutor, then results are merged.
    """
    t_start = time.time()
    log_query.info(">>> RAG NODE START (running rag_plan and rag_router in parallel)")
    
    try:
        # Run rag_plan and rag_router in parallel
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_plan = executor.submit(node_rag_plan, state)
            future_router = executor.submit(node_rag_router, state)
            
            # Get results from both
            plan_result = future_plan.result()
            router_result = future_router.result()
        
        # Check if router requested clarification
        if router_result.get("needs_clarification") == True:
            log_query.info("❓ Router requested clarification - returning early")
            t_elapsed = time.time() - t_start
            log_query.info(f"<<< RAG NODE DONE in {t_elapsed:.2f}s (clarification needed)")
            
            # Merge results, prioritizing clarification
            return {
                "needs_clarification": True,
                "clarification_question": router_result.get("clarification_question"),
                "query_plan": plan_result.get("query_plan"),
                "expanded_queries": plan_result.get("expanded_queries", []),
                "data_route": router_result.get("data_route"),
                "data_sources": router_result.get("data_sources"),
                "project_filter": router_result.get("project_filter")
            }
        
        # Merge results from both nodes
        merged_result = {
            # From rag_plan
            "query_plan": plan_result.get("query_plan"),
            "expanded_queries": plan_result.get("expanded_queries", []),
            # From rag_router
            "data_route": router_result.get("data_route"),
            "data_sources": router_result.get("data_sources"),
            "project_filter": router_result.get("project_filter"),
            "needs_clarification": False
        }
        
        t_elapsed = time.time() - t_start
        log_query.info(f"<<< RAG NODE DONE in {t_elapsed:.2f}s")
        log_query.info(f"   Merged results: plan steps={len(plan_result.get('query_plan', {}).get('steps', []))}, databases={router_result.get('data_sources', {})}")
        
        return merged_result
        
    except Exception as e:
        log_query.error(f"RAG node failed: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback: try to run them sequentially if parallel execution fails
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
                "needs_clarification": router_result.get("needs_clarification", False),
                "clarification_question": router_result.get("clarification_question")
            }
        except Exception as e2:
            log_query.error(f"Sequential fallback also failed: {e2}")
            # Ultimate fallback
            return {
                "query_plan": None,
                "expanded_queries": [state.user_query],
                "data_route": "smart",
                "data_sources": {"project_db": True, "code_db": False, "coop_manual": False, "speckle_db": False},
                "project_filter": None,
                "needs_clarification": False
            }

