"""
CacheSearch Node
Searches local cache and generates answer
"""
import time
from typing import Dict, Any, List
from langchain_core.documents import Document
from config.logging_config import log_query
from config.llm_instances import llm_synthesis
from .retriever import extract_folder_path_from_query, search_local_cache

MAX_CACHE_DOCS = 10


def node_cache_search(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Search local cache and generate answer.
    
    Args:
        state: State dict with user_query and other fields
    
    Returns:
        Dict with cache_search_result, citations, etc.
    """
    t_start = time.time()
    log_query.info(">>> CACHE SEARCH START")
    
    try:
        user_query = state.get("user_query", "")
        original_question = state.get("original_question") or user_query
        
        # Extract folder path from query
        folder_path = extract_folder_path_from_query(user_query)
        
        if not folder_path:
            log_query.warning("⚠️ No folder path found in query")
            return {
                "cache_search_result": "I couldn't find a project folder in your query. Please make sure you're asking about a project folder.",
                "cache_search_citations": [],
                "cache_search_completed": True
            }
        
        log_query.info(f"🔍 Searching cache for folder: {folder_path}")
        
        # Search local cache
        docs = search_local_cache(user_query, folder_path, k=MAX_CACHE_DOCS)
        
        if not docs:
            log_query.warning("⚠️ No documents found in cache")
            return {
                "cache_search_result": f"I couldn't find any cached information for the folder: {folder_path}. The cache may not have been generated yet, or the folder path might be incorrect.",
                "cache_search_citations": [],
                "cache_search_completed": True
            }
        
        log_query.info(f"✅ Found {len(docs)} documents from cache")
        
        # Build context from documents
        context_parts = []
        citations = []
        
        for i, doc in enumerate(docs):
            content = doc.page_content
            metadata = doc.metadata
            
            context_parts.append(f"[Document {i+1}]\n{content}")
            
            citations.append({
                "source": metadata.get("file_name", "Unknown"),
                "file_path": metadata.get("file_path", ""),
                "page_number": metadata.get("page_number"),
                "file_type": metadata.get("file_type", ""),
                "similarity": getattr(doc, 'similarity', None)
            })
        
        context = "\n\n".join(context_parts)
        
        # Generate answer using LLM
        prompt = f"""You are a helpful assistant answering questions based on cached project documents.

User Question: {original_question}

Relevant Context from Project Files:
{context}

Instructions:
1. Answer the user's question using ONLY the information provided in the context above
2. If the context doesn't contain enough information to answer, say so clearly
3. Cite specific files or pages when referencing information
4. Be concise but thorough
5. If you reference specific details, mention which file they came from

Answer:"""
        
        log_query.info("🤖 Generating answer from cache results...")
        response = llm_synthesis.invoke(prompt)
        answer = response.content if hasattr(response, 'content') else str(response)
        
        t_elapsed = time.time() - t_start
        log_query.info(f"<<< CACHE SEARCH DONE in {t_elapsed:.2f}s")
        
        return {
            "cache_search_result": answer,
            "cache_search_citations": citations,
            "cache_search_docs": docs,
            "cache_search_completed": True,
            "cache_search_folder": folder_path
        }
        
    except Exception as e:
        log_query.error(f"❌ Cache search failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            "cache_search_result": f"I encountered an error while searching the cache: {str(e)}",
            "cache_search_citations": [],
            "cache_search_completed": True
        }
