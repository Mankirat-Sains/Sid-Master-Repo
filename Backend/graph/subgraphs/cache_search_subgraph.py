"""
CacheSearch Subgraph
Sandboxed subgraph for testing local cache retrieval
"""
from langgraph.graph import StateGraph, END
from nodes.DesktopAgent.CacheSearch.node import node_cache_search
from nodes.DesktopAgent.CacheSearch.router import node_cache_search_router
from config.logging_config import log_query


def build_cache_search_subgraph():
    """Build the CacheSearch subgraph."""
    g = StateGraph(dict)  # Use simple dict state for sandboxing
    
    g.add_node("router", node_cache_search_router)
    g.add_node("search", node_cache_search)
    
    g.set_entry_point("router")
    
    # Route based on should_use_cache_search flag
    def route_decision(state):
        if state.get("should_use_cache_search", False):
            return "search"
        return END
    
    g.add_conditional_edges("router", route_decision, {
        "search": "search",
        END: END
    })
    
    g.add_edge("search", END)
    
    return g.compile()


_cache_search_subgraph = None


def call_cache_search_subgraph(state) -> dict:
    """
    Wrapper that invokes the CacheSearch subgraph.
    
    Args:
        state: OrchestrationState or dict with user_query, original_question, etc.
    
    Returns:
        Dict with cache_search_result, cache_search_citations, etc.
    """
    global _cache_search_subgraph
    
    if _cache_search_subgraph is None:
        log_query.info("🔧 Initializing CacheSearch subgraph...")
        _cache_search_subgraph = build_cache_search_subgraph()
        log_query.info("✅ CacheSearch subgraph initialized")
    
    # Convert state to dict if needed
    if hasattr(state, '__dict__'):
        state_dict = {
            "user_query": getattr(state, "user_query", ""),
            "original_question": getattr(state, "original_question", None),
            "session_id": getattr(state, "session_id", ""),
        }
    else:
        state_dict = dict(state)
    
    try:
        result = _cache_search_subgraph.invoke(state_dict)
        
        # Extract results
        return {
            "cache_search_result": result.get("cache_search_result"),
            "cache_search_citations": result.get("cache_search_citations", []),
            "cache_search_completed": result.get("cache_search_completed", False),
            "cache_search_folder": result.get("cache_search_folder"),
        }
    except Exception as e:
        log_query.error(f"❌ CacheSearch subgraph failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            "cache_search_result": None,
            "cache_search_citations": [],
            "cache_search_completed": False,
        }
