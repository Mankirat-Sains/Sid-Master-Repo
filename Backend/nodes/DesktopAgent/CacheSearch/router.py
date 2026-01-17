"""
CacheSearch Router
Detects if query should use CacheSearch (has folder context from ProjectChat)
"""
import re
from typing import Dict, Any
from config.logging_config import log_query


def has_folder_context(query: str) -> bool:
    """
    Check if query contains folder context from ProjectChat.
    
    Pattern: [Context: User is working in project folder: /path/to/folder]
    """
    pattern = r'\[Context:.*?project folder:\s*[^\]]+\]'
    return bool(re.search(pattern, query))


def node_cache_search_router(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Router that determines if CacheSearch should be used.
    
    Returns:
        Dict with should_use_cache_search flag
    """
    user_query = state.get("user_query", "")
    original_question = state.get("original_question") or user_query
    
    # Check if query has folder context
    use_cache_search = has_folder_context(user_query) or has_folder_context(original_question)
    
    if use_cache_search:
        log_query.info("✅ Routing to CacheSearch (folder context detected)")
    else:
        log_query.info("⏭️ Skipping CacheSearch (no folder context)")
    
    return {
        "should_use_cache_search": use_cache_search
    }
