"""
Project Folder Cache Generator

Creates embeddings cache for project files using OpenAI text-embedding-3-small.
"""

from .cache_generator import build_project_cache, get_project_id, ensure_cache_dir

__all__ = ['build_project_cache', 'get_project_id', 'ensure_cache_dir']
