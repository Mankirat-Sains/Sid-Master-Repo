"""
Router Dispatcher Wrapper
Wraps router_dispatcher to intercept ProjectChat queries and route to CacheSearch
This is a sandboxed wrapper that doesn't modify existing router_dispatcher code
"""
from nodes.router_dispatcher import node_router_dispatcher
from nodes.DesktopAgent.CacheSearch.pre_router import node_cache_search_pre_router
from config.logging_config import log_route


def node_router_dispatcher_with_cache_search(state):
    """
    Wrapper around router_dispatcher that checks for CacheSearch first.
    
    If folder context is detected, routes to CacheSearch.
    Otherwise, falls through to normal router_dispatcher.
    """
    # First, check if this should use CacheSearch
    cache_result = node_cache_search_pre_router(state)
    
    # If CacheSearch was used and found results, return those
    if cache_result.get("_skip_normal_routing") or cache_result.get("cache_search_result"):
        log_route.info("✅ Using CacheSearch results - skipping normal routing")
        return cache_result
    
    # Otherwise, proceed with normal routing
    log_route.info("⏭️ No CacheSearch match - proceeding with normal routing")
    return node_router_dispatcher(state)
