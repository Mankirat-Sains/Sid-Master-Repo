#!/usr/bin/env python3
"""
Standalone Test Server for CacheSearch
Completely separate from main API server for testing
"""
import sys
from pathlib import Path
import json
import re
from typing import List, Optional
import numpy as np
from langchain_core.documents import Document

# Add Backend directory to Python path
backend_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Import ONLY what we need (no nodes package imports)
from config.llm_instances import emb, llm_synthesis
from config.logging_config import log_query

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# INLINED FUNCTIONS (to avoid circular imports)
# ============================================================================

CACHE_BASE_DIR = Path("/Volumes/J/cache/projects")

def extract_folder_path_from_query(query: str) -> Optional[str]:
    """Extract folder path from query context message"""
    pattern = r'\[Context:.*?project folder:\s*([^\]]+)\]'
    match = re.search(pattern, query)
    if match:
        folder_path = match.group(1).strip()
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
    """Search local cache for a project folder"""
    try:
        project_id = get_project_id_from_folder(folder_path)
        cache_dir = CACHE_BASE_DIR / project_id
        index_file = cache_dir / "index.json"
        
        if not index_file.exists():
            log_query.info(f"⚠️ No cache found for project: {project_id}")
            return []
        
        with open(index_file, 'r', encoding='utf-8') as f:
            index_data = json.load(f)
        
        log_query.info(f"🔍 Searching local cache for project: {project_id} ({len(index_data.get('files', []))} files)")
        
        query_embedding = emb.embed_query(query)
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
                
                for page in cache_data.get('pages', []):
                    page_embedding = page.get('embedding')
                    if not page_embedding:
                        continue
                    
                    similarity = cosine_similarity(query_embedding, page_embedding)
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
        
        all_results.sort(key=lambda x: x['similarity'], reverse=True)
        top_results = all_results[:k]
        
        log_query.info(f"✅ Found {len(top_results)} results from local cache")
        
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

def node_cache_search(state: dict) -> dict:
    """Search local cache and generate answer"""
    import time
    t_start = time.time()
    log_query.info(">>> CACHE SEARCH START")
    
    try:
        user_query = state.get("user_query", "")
        original_question = state.get("original_question") or user_query
        
        folder_path = extract_folder_path_from_query(user_query)
        
        if not folder_path:
            log_query.warning("⚠️ No folder path found in query")
            return {
                "cache_search_result": "I couldn't find a project folder in your query. Please make sure you're asking about a project folder.",
                "cache_search_citations": [],
                "cache_search_completed": True
            }
        
        log_query.info(f"🔍 Searching cache for folder: {folder_path}")
        docs = search_local_cache(user_query, folder_path, k=10)
        
        if not docs:
            log_query.warning("⚠️ No documents found in cache")
            return {
                "cache_search_result": f"I couldn't find any cached information for the folder: {folder_path}. The cache may not have been generated yet, or the folder path might be incorrect.",
                "cache_search_citations": [],
                "cache_search_completed": True
            }
        
        log_query.info(f"✅ Found {len(docs)} documents from cache")
        
        context_parts = []
        citations = []
        
        for i, doc in enumerate(docs):
            context_parts.append(f"[Document {i+1}]\n{doc.page_content}")
            citations.append({
                "source": doc.metadata.get("file_name", "Unknown"),
                "file_path": doc.metadata.get("file_path", ""),
                "page_number": doc.metadata.get("page_number"),
                "file_type": doc.metadata.get("file_type", ""),
            })
        
        context = "\n\n".join(context_parts)
        
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
        
        # Handle different response formats (LangChain AIMessage, Gemini, etc.)
        from langchain_core.messages import AIMessage
        
        answer = ""
        
        if isinstance(response, AIMessage):
            # Standard LangChain AIMessage
            content = response.content
            if isinstance(content, list):
                # Gemini returns list of dicts like [{'type': 'text', 'text': '...'}]
                text_parts = []
                for item in content:
                    if isinstance(item, dict):
                        text = item.get('text', '') or item.get('content', '')
                        if text:
                            text_parts.append(text)
                    elif isinstance(item, str):
                        text_parts.append(item)
                answer = ' '.join(text_parts) if text_parts else str(content)
            else:
                answer = str(content)
        elif hasattr(response, 'content'):
            # Other LangChain response types
            content = response.content
            if isinstance(content, list):
                # Handle list content
                text_parts = []
                for item in content:
                    if isinstance(item, dict):
                        text = item.get('text', '') or item.get('content', '')
                        if text:
                            text_parts.append(text)
                    elif isinstance(item, str):
                        text_parts.append(item)
                answer = ' '.join(text_parts) if text_parts else str(content)
            else:
                answer = str(content)
        elif isinstance(response, list):
            # Handle direct list response
            text_parts = []
            for item in response:
                if isinstance(item, dict):
                    text = item.get('text', '') or item.get('content', '')
                    if text:
                        text_parts.append(text)
                elif isinstance(item, str):
                    text_parts.append(item)
            answer = ' '.join(text_parts) if text_parts else str(response)
        elif isinstance(response, dict):
            # Handle dict format
            answer = response.get('text', '') or response.get('content', '') or str(response)
        else:
            answer = str(response)
        
        # Ensure answer is a string and not empty
        if not isinstance(answer, str):
            answer = str(answer)
        if not answer or answer.strip() == "":
            answer = "I couldn't generate a response. Please try again."
        
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

# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(title="CacheSearch Test Server")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    session_id: str = "test"


class ChatResponse(BaseModel):
    reply: str
    citations: List[dict] = []
    session_id: str


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "ok", "service": "CacheSearch Test Server"}


@app.post("/chat", response_model=ChatResponse)
async def chat_handler(request: ChatRequest):
    """Simple chat endpoint for testing CacheSearch"""
    try:
        logger.info(f"📤 Chat request: {request.message[:100]}...")
        
        state = {
            "user_query": request.message,
            "original_question": request.message,
            "session_id": request.session_id,
        }
        
        result = node_cache_search(state)
        
        reply = result.get("cache_search_result", "No response generated")
        citations = result.get("cache_search_citations", [])
        
        logger.info(f"✅ Response generated: {len(reply)} chars, {len(citations)} citations")
        
        return ChatResponse(
            reply=reply,
            citations=citations,
            session_id=request.session_id
        )
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return ChatResponse(
            reply=f"Error: {str(e)}",
            citations=[],
            session_id=request.session_id
        )


@app.get("/test/folder")
async def test_folder_detection(query: str):
    """Test endpoint to check if folder path extraction works"""
    folder_path = extract_folder_path_from_query(query)
    return {
        "query": query,
        "folder_path": folder_path,
        "has_folder_context": folder_path is not None
    }


@app.get("/test/cache/{project_id}")
async def test_cache_search(project_id: str, query: str):
    """Test endpoint to search cache directly"""
    try:
        from pathlib import Path
        cache_dir = Path(f"/Volumes/J/cache/projects/{project_id}")
        
        if not cache_dir.exists():
            return {
                "error": f"Cache not found for project: {project_id}",
                "cache_dir": str(cache_dir)
            }
        
        index_file = cache_dir / "index.json"
        if index_file.exists():
            with open(index_file, 'r') as f:
                index_data = json.load(f)
            folder_path = index_data.get("folder_path")
            
            if folder_path:
                docs = search_local_cache(query, folder_path, k=5)
                return {
                    "project_id": project_id,
                    "folder_path": folder_path,
                    "query": query,
                    "results_count": len(docs),
                    "results": [
                        {
                            "file_name": doc.metadata.get("file_name"),
                            "page_number": doc.metadata.get("page_number"),
                            "content_preview": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
                        }
                        for doc in docs
                    ]
                }
        
        return {
            "error": "Could not find folder path in cache index",
            "cache_dir": str(cache_dir)
        }
        
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }


if __name__ == "__main__":
    print("🚀 Starting CacheSearch Test Server on http://localhost:8002")
    print("📝 Test endpoint: POST http://localhost:8002/chat")
    print("🔍 Health check: GET http://localhost:8002/health")
    uvicorn.run(app, host="0.0.0.0", port=8002)
