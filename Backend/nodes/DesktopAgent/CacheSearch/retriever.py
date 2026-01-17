"""
Local Cache Retriever
Searches cached embeddings from project folders
"""
import json
import os
import re
from pathlib import Path
from typing import List, Optional
import numpy as np
from langchain_core.documents import Document
from config.llm_instances import emb
from config.logging_config import log_query

CACHE_BASE_DIR = Path("/Volumes/J/cache/projects")


def extract_folder_path_from_query(query: str) -> Optional[str]:
    """Extract folder path from query context message"""
    # Look for pattern: [Context: User is working in project folder: /path/to/folder]
    pattern = r'\[Context:.*?project folder:\s*([^\]]+)\]'
    match = re.search(pattern, query)
    if match:
        folder_path = match.group(1).strip()
        # Clean up - remove any trailing context
        folder_path = folder_path.split('.')[0].strip()
        return folder_path
    return None


def get_project_id_from_folder(folder_path: str) -> str:
    """Get project ID from folder path - matches cache_generator logic exactly"""
    folder_name = Path(folder_path).name
    if folder_name:
        # Match cache_generator.py logic: replace spaces and slashes with underscores
        project_id = folder_name.replace(" ", "_").replace("/", "_")
        return project_id
    # Fallback to hash
    import hashlib
    return hashlib.md5(folder_path.encode()).hexdigest()[:12]


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors"""
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(dot_product / (norm1 * norm2))


def search_local_cache(query: str, folder_path: str, k: int = 10) -> List[Document]:
    """
    Search local cache for a project folder.
    
    Args:
        query: User query
        folder_path: Path to project folder
        k: Number of results to return
    
    Returns:
        List of Document objects with content and metadata
    """
    try:
        # Get project ID
        project_id = get_project_id_from_folder(folder_path)
        cache_dir = CACHE_BASE_DIR / project_id
        
        # Check if cache exists
        index_file = cache_dir / "index.json"
        if not index_file.exists():
            log_query.info(f"⚠️ No cache found for project: {project_id}")
            return []
        
        # Load index
        with open(index_file, 'r', encoding='utf-8') as f:
            index_data = json.load(f)
        
        log_query.info(f"🔍 Searching local cache for project: {project_id} ({len(index_data.get('files', []))} files)")
        
        # Generate query embedding
        query_embedding = emb.embed_query(query)
        
        # Search all cached files
        all_results = []
        files_dir = cache_dir / "files"
        
        for file_entry in index_data.get('files', []):
            file_hash = file_entry.get('file_hash')
            cache_file = files_dir / f"{file_hash}.json"
            
            if not cache_file.exists():
                continue
            
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                # Search through pages/chunks
                for page in cache_data.get('pages', []):
                    page_embedding = page.get('embedding')
                    if not page_embedding:
                        continue
                    
                    # Calculate cosine similarity
                    similarity = cosine_similarity(query_embedding, page_embedding)
                    
                    # Get metadata
                    file_metadata = cache_data.get('metadata', {})
                    
                    all_results.append({
                        'content': page.get('text', ''),
                        'similarity': similarity,
                        'metadata': {
                            'file_path': file_metadata.get('file_path'),
                            'file_name': file_metadata.get('file_name'),
                            'file_type': file_metadata.get('file_type'),
                            'page_number': page.get('page_number'),
                            'description': page.get('description', ''),
                            'source': 'local_cache',
                            'project_id': project_id
                        }
                    })
            except Exception as e:
                log_query.warning(f"Error reading cache file {cache_file}: {e}")
                continue
        
        # Sort by similarity and take top k
        all_results.sort(key=lambda x: x['similarity'], reverse=True)
        top_results = all_results[:k]
        
        log_query.info(f"✅ Found {len(top_results)} results from local cache")
        
        # Convert to Documents
        documents = []
        for result in top_results:
            doc = Document(
                page_content=result['content'],
                metadata=result['metadata']
            )
            documents.append(doc)
        
        return documents
        
    except Exception as e:
        log_query.error(f"❌ Error searching local cache: {e}")
        import traceback
        traceback.print_exc()
        return []


def make_local_cache_retriever(folder_path: Optional[str] = None):
    """
    Create a retriever function for local cache.
    
    Args:
        folder_path: Optional folder path. If None, will extract from query.
    
    Returns:
        Retriever function that takes (query: str, k: int) -> List[Document]
    """
    def retriever(query: str, k: int = 10) -> List[Document]:
        # Extract folder path from query if not provided
        target_folder = folder_path or extract_folder_path_from_query(query)
        
        if not target_folder:
            log_query.info("⚠️ No folder path found in query for local cache search")
            return []
        
        return search_local_cache(query, target_folder, k)
    
    return retriever
