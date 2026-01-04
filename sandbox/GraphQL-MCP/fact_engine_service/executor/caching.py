"""In-memory caching for fact extraction (per-request)"""
from typing import Dict, Any, Optional
import hashlib
import json


class RequestCache:
    """
    In-memory cache for a single request.
    
    Caches extracted facts to avoid re-extracting the same facts
    from the same elements multiple times.
    """
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
    
    def _make_key(self, element_id: str, fact_name: str) -> str:
        """Create cache key"""
        return f"{element_id}:{fact_name}"
    
    def get(self, element_id: str, fact_name: str) -> Optional[Any]:
        """Get cached fact value"""
        key = self._make_key(element_id, fact_name)
        return self._cache.get(key)
    
    def set(self, element_id: str, fact_name: str, value: Any):
        """Cache a fact value"""
        key = self._make_key(element_id, fact_name)
        self._cache[key] = value
    
    def clear(self):
        """Clear the cache"""
        self._cache.clear()
    
    def has(self, element_id: str, fact_name: str) -> bool:
        """Check if a fact is cached"""
        key = self._make_key(element_id, fact_name)
        return key in self._cache


