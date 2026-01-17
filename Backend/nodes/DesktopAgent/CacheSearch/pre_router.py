"""
CacheSearch Pre-Router
Intercepts queries with folder context and routes to CacheSearch
This runs BEFORE router_dispatcher to sandbox CacheSearch
"""
from typing import Dict, Any
from config.logging_config import log_query, log_route
from .router import has_folder_context
from graph.subgraphs.cache_search_subgraph import call_cache_search_subgraph


def node_cache_search_pre_router(state) -> Dict[str, Any]:
    """
    Pre-router that intercepts ProjectChat queries and routes to CacheSearch.
    
    If folder context is detected, calls CacheSearch and returns results.
    Otherwise, returns empty dict to let normal flow continue.
    """
    # Extract query from state
    if hasattr(state, 'user_query'):
        user_query = state.user_query
        original_question = getattr(state, 'original_question', None) or user_query
    elif isinstance(state, dict):
        user_query = state.get('user_query', '')
        original_question = state.get('original_question') or user_query
    else:
        return {}
    
    # Check if this is a ProjectChat query (has folder context)
    if has_folder_context(user_query) or has_folder_context(original_question):
        log_route.info("🎯 PROJECTCHAT QUERY DETECTED - Routing to CacheSearch")
        
        try:
            # Call CacheSearch subgraph
            cache_result = call_cache_search_subgraph(state)
            
            # If CacheSearch found results, use them and skip normal routing
            if cache_result.get("cache_search_result"):
                log_route.info("✅ CacheSearch completed - using cache results")
                
                # Return results in format that will be used as final answer
                return {
                    "cache_search_result": cache_result.get("cache_search_result"),
                    "cache_search_citations": cache_result.get("cache_search_citations", []),
                    "cache_search_completed": True,
                    # Set final_answer to cache result so it's used
                    "final_answer": cache_result.get("cache_search_result"),
                    "answer_citations": cache_result.get("cache_search_citations", []),
                    # Flag to skip normal routing
                    "_skip_normal_routing": True,
                }
            else:
                log_route.info("⚠️ CacheSearch found no results - falling through to normal routing")
                return {}
        except Exception as e:
            log_query.error(f"❌ CacheSearch pre-router failed: {e}")
            import traceback
            traceback.print_exc()
            # Fall through to normal routing on error
            return {}
    
    # No folder context - let normal flow continue
    return {}
