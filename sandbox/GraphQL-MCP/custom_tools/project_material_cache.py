#!/usr/bin/env python3
"""
Project Material Cache

Caches project material metadata to avoid repeated queries.
This significantly speeds up repeated searches.

Cache structure:
{
    "project_id": {
        "last_updated": timestamp,
        "version_id": "latest_version_id",
        "materials": ["timber", "steel", ...],
        "sample_size": 50,
        "element_count": 1000
    }
}
"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional, Set
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ProjectMaterialCache:
    """
    Cache for project material metadata.
    
    Reduces redundant queries by caching material information per project.
    Cache expires when project versions change.
    """
    
    def __init__(self, cache_file: Optional[str] = None, ttl_hours: int = 24):
        """
        Initialize cache.
        
        Args:
            cache_file: Path to cache file (default: .project_material_cache.json)
            ttl_hours: Time-to-live in hours (default: 24)
        """
        self.cache_file = Path(cache_file) if cache_file else Path(__file__).parent / ".project_material_cache.json"
        self.ttl_seconds = ttl_hours * 3600
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._load_cache()
    
    def _load_cache(self):
        """Load cache from file"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    self._cache = json.load(f)
                logger.info(f"Loaded cache with {len(self._cache)} projects")
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")
                self._cache = {}
        else:
            self._cache = {}
    
    def _save_cache(self):
        """Save cache to file"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self._cache, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")
    
    def get_project_materials(
        self,
        project_id: str,
        version_id: Optional[str] = None
    ) -> Optional[Set[str]]:
        """
        Get cached materials for a project.
        
        Args:
            project_id: Project ID
            version_id: Current version ID (for cache invalidation)
            
        Returns:
            Set of materials or None if not cached/invalid
        """
        cached = self._cache.get(project_id)
        if not cached:
            return None
        
        # Check if cache is expired
        last_updated = cached.get("last_updated", 0)
        if time.time() - last_updated > self.ttl_seconds:
            logger.debug(f"Cache expired for project {project_id}")
            return None
        
        # Check if version changed (invalidate cache)
        if version_id and cached.get("version_id") != version_id:
            logger.debug(f"Version changed for project {project_id}, invalidating cache")
            return None
        
        materials = cached.get("materials", [])
        return set(materials) if materials else None
    
    def set_project_materials(
        self,
        project_id: str,
        materials: Set[str],
        version_id: Optional[str] = None,
        sample_size: int = 50,
        element_count: Optional[int] = None
    ):
        """
        Cache materials for a project.
        
        Args:
            project_id: Project ID
            materials: Set of materials found
            version_id: Current version ID
            sample_size: Number of elements sampled
            element_count: Total element count (if known)
        """
        self._cache[project_id] = {
            "last_updated": time.time(),
            "version_id": version_id,
            "materials": sorted(list(materials)),
            "sample_size": sample_size,
            "element_count": element_count
        }
        self._save_cache()
        logger.debug(f"Cached materials for project {project_id}: {materials}")
    
    def invalidate_project(self, project_id: str):
        """Invalidate cache for a specific project"""
        if project_id in self._cache:
            del self._cache[project_id]
            self._save_cache()
            logger.debug(f"Invalidated cache for project {project_id}")
    
    def clear(self):
        """Clear all cache"""
        self._cache = {}
        self._save_cache()
        logger.info("Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "cached_projects": len(self._cache),
            "cache_file": str(self.cache_file),
            "ttl_hours": self.ttl_seconds / 3600
        }

