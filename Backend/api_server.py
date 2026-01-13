#!/usr/bin/env python3
"""
FastAPI server for Mantle RAG Chat Interface
Connect the chatbutton Electron app to the rag.py backend
"""

# Windows async event loop configuration
# Python 3.11+ defaults to ProactorEventLoopPolicy which works well for async I/O
# WindowsSelectorEventLoopPolicy still works but is slower for Windows file I/O
import sys
if sys.platform == 'win32':
    import asyncio
    # Python 3.11+ has better async support - ProactorEventLoopPolicy is default and recommended
    # WindowsSelectorEventLoopPolicy still works but is less efficient
    # Only set policy if we need to override (not necessary in Python 3.11+)
    # asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())  # Commented: use default in 3.11+

from datetime import datetime
import logging
import re
import time
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv
import os
import json
from html import escape
import httpx
from pathlib import Path

# Load environment variables from the root .env (single source of truth)
root_env_path = Path(__file__).resolve().parent.parent / ".env"
if root_env_path.exists():
    load_dotenv(dotenv_path=str(root_env_path), override=True)
    print(f"✅ Loaded environment from {root_env_path}")
else:
    load_dotenv(override=True)
    print(f"⚠️ Root .env not found at {root_env_path}, using current environment")

# Import the RAG system from new modular structure
from main import run_agentic_rag, rag_healthcheck
from nodes.DBRetrieval.KGdb import test_database_connection
from config.settings import PROJECT_CATEGORIES, CATEGORIES_PATH, PLANNER_PLAYBOOK, PLAYBOOK_PATH, DEBUG_MODE

# Import LangGraph types for interrupt handling
try:
    from langgraph.errors import GraphInterrupt
    from langgraph.types import Command
except ImportError:
    GraphInterrupt = Exception  # Fallback
    Command = None

# Import Kuzu manager
try:
    from nodes.DBRetrieval.KGdb.kuzu_client import get_kuzu_manager
except ImportError:
    get_kuzu_manager = None

# Import feedback logger from helpers folder
try:
    from helpers.feedback_logger import get_feedback_logger
except ImportError:
    # Fallback if feedback_logger is not available
    def get_feedback_logger():
        class DummyLogger:
            def log_feedback(self, data):
                return True
            def get_feedback_stats(self):
                return {}
        return DummyLogger()

# Import Supabase logger from helpers folder
try:
    from helpers.supabase_logger import get_supabase_logger
except ImportError:
    # Fallback if supabase_logger is not available
    def get_supabase_logger():
        class DummyLogger:
            enabled = False
            def upload_image(self, *args, **kwargs):
                return None
            def log_user_query(self, *args, **kwargs):
                return True
            def log_feedback(self, *args, **kwargs):
                return True
            def get_interaction_stats(self, *args, **kwargs):
                return {}
            def get_user_summary(self, *args, **kwargs):
                return {}
            def get_recent_interactions(self, *args, **kwargs):
                return []
        return DummyLogger()

# Import enhanced logging system from helpers folder
try:
    from helpers.enhanced_logger import (
        enhanced_log_capture, 
        setup_enhanced_logging, 
        render_enhanced_log_html, 
        get_enhanced_log_stats
    )
except ImportError:
    # Fallback if enhanced_logger is not available
    class DummyLogCapture:
        def get_logs(self, *args, **kwargs):
            return []
        def get_function_calls(self, *args, **kwargs):
            return []
        def get_chunk_flow(self, *args, **kwargs):
            return []
        def clear_all(self):
            pass
    
    enhanced_log_capture = DummyLogCapture()
    
    def setup_enhanced_logging():
        pass
    
    async def render_enhanced_log_html(*args, **kwargs):
        return {"error": "Enhanced logging not available"}
    
    def get_enhanced_log_stats():
        return {}

# Import instructions content from helpers folder
try:
    from helpers.instructions import INSTRUCTIONS_CONTENT
except ImportError:
    INSTRUCTIONS_CONTENT = "# Instructions\n\nInstructions content not available."

# Helper function to wrap project numbers with fully-formed HTML links
def extract_text_from_content(content) -> str:
    """
    Extract text content from AIMessageChunk.content.
    Handles both string format (OpenAI, Anthropic) and list format (Gemini 3.0).
    
    Gemini 3.0 returns: [{'type': 'text', 'text': "..."}]
    Other models return: "text content"
    """
    if not content:
        return ""
    
    # Handle list format (Gemini 3.0)
    if isinstance(content, list):
        text_parts = []
        for item in content:
            if isinstance(item, dict):
                # Extract text from dict items (e.g., {'type': 'text', 'text': "..."})
                if item.get('type') == 'text' and 'text' in item:
                    text_parts.append(str(item['text']))
                elif 'text' in item:
                    # Fallback: just try 'text' key
                    text_parts.append(str(item['text']))
            elif isinstance(item, str):
                # If list contains strings directly
                text_parts.append(item)
        return ''.join(text_parts)
    
    # Handle string format (OpenAI, Anthropic, etc.)
    if isinstance(content, str):
        return content
    
    # Fallback: try to convert to string
    return str(content)


def strip_asterisks_from_projects(text: str) -> str:
    """
    Remove markdown asterisks (**) that wrap project numbers or project names.
    The LLM sometimes adds **Project 25-01-002** - we want to strip these asterisks.
    """
    if not text:
        return text
    
    # Ensure text is a string (in case content was passed directly)
    if not isinstance(text, str):
        text = extract_text_from_content(text)
    
    # Pattern 1: **Project NUMBER** (exact match)
    text = re.sub(r'\*\*Project\s+(\d{2}-\d{2}-\d{3})\*\*', r'Project \1', text)
    
    # Pattern 2: **Project NUMBER - ... (with dash after, asterisks before dash)
    text = re.sub(r'\*\*Project\s+(\d{2}-\d{2}-\d{3})\s*-\s*', r'Project \1 - ', text)
    
    # Pattern 3: Just project number wrapped: **25-01-002**
    text = re.sub(r'\*\*(\d{2}-\d{2}-\d{3})\*\*', r'\1', text)
    
    # Pattern 4: **Project NUMBER** with text after (space before closing **)
    text = re.sub(r'\*\*Project\s+(\d{2}-\d{2}-\d{3})\s+\*\*', r'Project \1 ', text)
    
    # Pattern 5: Handle "**Details:**" or "**Project Name:**" type labels
    text = re.sub(r'\*\*Details:\s*\*\*', 'Details:', text)
    text = re.sub(r'\*\*Project Name:\s*\*\*', 'Project Name:', text)
    text = re.sub(r'\*\*Details:\*\*', 'Details:', text)
    text = re.sub(r'\*\*Project Name:\*\*', 'Project Name:', text)
    
    # Pattern 6: Handle any remaining **Project NUMBER** patterns with various spacing
    text = re.sub(r'\*\*\s*Project\s+(\d{2}-\d{2}-\d{3})\s*\*\*', r'Project \1', text)
    
    return text


def sanitize_file_path(file_path: str) -> str:
    r"""
    Sanitize file path from Supabase:
    1. Stop at \md (remove \md and everything after)
    2. Change .md extension to .pdf
    3. Prepend network path: \\\\WADDELLNAS\\Resources\\References & Codes\\
    
    Example:
    Input:  "NBCC\\nbc2020_p1\\md\\nbc2020_p1_page-379.md"
    Output: "\\\\WADDELLNAS\\Resources\\References & Codes\\NBCC\\nbc2020_p1.pdf"
    
    Input:  "base\\ASCE7-10WindLoadingProvisionsStaticProcedure\\md\\ASCE7-10WindLoadingProvisionsStaticProcedure_page-014.md"
    Output: "\\\\WADDELLNAS\\Resources\\References & Codes\\base\\ASCE7-10WindLoadingProvisionsStaticProcedure.pdf"
    """
    if not file_path:
        return ""
    
    # Stop at \md (remove \md and everything after)
    if "\\md" in file_path:
        file_path = file_path.split("\\md")[0]
    
    # Change .md extension to .pdf
    if file_path.endswith(".md"):
        file_path = file_path[:-3] + ".pdf"
    
    # Prepend network path
    network_path = "\\\\WADDELLNAS\\Resources\\References & Codes\\"
    sanitized_path = network_path + file_path
    
    return sanitized_path


def wrap_code_file_links(text: str, code_citations: List[Dict]) -> str:
    """
    Wrap code file citations with fully-formed HTML links.
    Replaces citation patterns like [Document: filename, Page: X] with clickable filename links.
    Each link uses the specific page number from the citation.
    File paths from Supabase are already in the correct format and used directly.
    Shows filename for code DB (different files).
    This is done in the backend so frontend doesn't need to rebuild executable for link changes.
    """
    if not code_citations:
        return text
    
    # Create a mapping of filename to file path
    # File paths from Supabase are already in correct format: \\\\WADDELLNAS\\Resources\\References & Codes\\...
    file_link_map = {}  # filename -> file_path
    for cite in code_citations:
        filename = cite.get("filename", "")
        file_path = cite.get("file_path", "")
        
        if filename and file_path:
            # Use file_path directly from Supabase (already in correct format)
            if filename not in file_link_map:
                file_link_map[filename] = file_path
    
    # First, replace full citation patterns: [Document: filename, Page: X]
    # This extracts the specific page number from each citation and replaces with clean link
    # Process in reverse order by filename length to handle longer filenames first
    for filename, file_path in sorted(file_link_map.items(), key=lambda x: len(x[0]), reverse=True):
        escaped_filename = re.escape(filename)
        escaped_file_path = escape(file_path, quote=True)
        escaped_display_name = escape(filename, quote=False)  # Don't quote for text content
        
        # Pattern to match: [Document: filename, Page: X] (case-insensitive, flexible spacing)
        # Capture the page number from the citation
        citation_pattern = rf'\[Document:\s*{escaped_filename}\s*,\s*Page:\s*(\d+)\]'
        
        def make_citation_replacer(fpath, fname, display_name):
            def citation_replacer(match):
                page_number = match.group(1)  # Extract page number from citation
                # Generate fully-formed HTML link with filename as display text (code DB shows filename)
                title_text = f"Click to open file at page {page_number}"
                escaped_title = escape(title_text, quote=True)  # Escape title attribute
                return f'<a href="#" class="file-link" data-path="{fpath}" data-page="{page_number}" title="{escaped_title}">{display_name}</a>'
            return citation_replacer
        
        text = re.sub(citation_pattern, make_citation_replacer(escaped_file_path, filename, escaped_display_name), text, flags=re.IGNORECASE)
    
    return text


def wrap_coop_file_links(text: str, coop_citations: List[Dict]) -> str:
    """
    Wrap coop manual file citations with fully-formed HTML links.
    Replaces citation patterns like [Document: filename, Page: X] with clickable page number links.
    Each link uses the specific page number from the citation.
    Shows only page number for coop manual (same file always).
    File paths from Supabase are already in the correct format and used directly.
    This is done in the backend so frontend doesn't need to rebuild executable for link changes.
    """
    if not coop_citations:
        return text
    
    # Create a mapping of filename to file path (coop manual is always the same file)
    # File paths from Supabase are already in correct format: \\\\WADDELLNAS\\Coop\\...
    file_link_map = {}  # filename -> file_path
    for cite in coop_citations:
        filename = cite.get("filename", "")
        file_path = cite.get("file_path", "")
        
        if filename and file_path:
            # Use file_path directly from Supabase (already in correct format)
            if filename not in file_link_map:
                file_link_map[filename] = file_path
    
    # First, replace full citation patterns: [Document: filename, Page: X]
    # This extracts the specific page number from each citation and replaces with page number link
    # Process in reverse order by filename length to handle longer filenames first
    for filename, file_path in sorted(file_link_map.items(), key=lambda x: len(x[0]), reverse=True):
        escaped_filename = re.escape(filename)
        escaped_file_path = escape(file_path, quote=True)
        
        # Pattern to match: [Document: filename, Page: X] (case-insensitive, flexible spacing)
        # Capture the page number from the citation
        citation_pattern = rf'\[Document:\s*{escaped_filename}\s*,\s*Page:\s*(\d+)\]'
        
        def make_citation_replacer(fpath):
            def citation_replacer(match):
                page_number = match.group(1)  # Extract page number from citation
                # Generate fully-formed HTML link with page number as display text (coop manual shows page only)
                title_text = f"Click to open file at page {page_number}"
                escaped_title = escape(title_text, quote=True)  # Escape title attribute
                display_text = escape(f"Page {page_number}", quote=False)
                return f'<a href="#" class="file-link" data-path="{fpath}" data-page="{page_number}" title="{escaped_title}">{display_text}</a>'
            return citation_replacer
        
        text = re.sub(citation_pattern, make_citation_replacer(escaped_file_path), text, flags=re.IGNORECASE)
    
    return text


def wrap_external_links(text: str) -> str:
    """
    Convert external HTML anchor tags to file-link format so frontend can handle them.
    Replaces external links like <a href="https://..." target="_blank">Sidcode</a>
    with <a href="#" class="file-link" data-path="https://..." title="Sidcode">Sidcode</a>
    This matches the pattern used for file citations - frontend already handles file-link clicks.
    """
    if not text:
        return text
    
    # Pattern to match external anchor tags (with http/https URLs)
    def convert_to_file_link(match):
        full_tag = match.group(0)
        # Extract URL from href attribute
        url_match = re.search(r'href=["\'](https?://[^"\']+)["\']', full_tag)
        # Extract display text (content between > and <)
        text_match = re.search(r'>([^<]+)<', full_tag)
        
        if url_match and text_match:
            url = url_match.group(1)
            display_text = text_match.group(1).strip()
            escaped_url = escape(url, quote=True)
            escaped_text = escape(display_text, quote=False)
            escaped_title = escape(f"Click to open {display_text}", quote=True)
            # Convert to file-link format (same as file citations) - frontend will handle clicks
            return f'<a href="#" class="file-link" data-path="{escaped_url}" title="{escaped_title}">{escaped_text}</a>'
        
        return full_tag  # Return unchanged if we can't parse it
    
    # Match external anchor tags with http/https URLs
    text = re.sub(r'<a\s+[^>]*href=["\']https?://[^"\']+["\'][^>]*>.*?</a>', convert_to_file_link, text, flags=re.IGNORECASE | re.DOTALL)
    
    return text


# Configure logging - use DEBUG_MODE from config
from config.logging_config import LOG_LEVEL
# Only configure if not already configured (logging_config.py already called basicConfig)
# But ensure root logger respects DEBUG_MODE
root_logger = logging.getLogger()
root_logger.setLevel(LOG_LEVEL)
# Also ensure all handlers use DEBUG_MODE level
for handler in root_logger.handlers:
    handler.setLevel(LOG_LEVEL)

logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)  # Ensure this logger respects DEBUG_MODE

# Set up enhanced logging
setup_enhanced_logging()

# FastAPI app
app = FastAPI(
    title="Mantle RAG API",
    description="API for Mantle RAG Chat System",
    version="1.0.0"
)

# Enable CORS for the Electron desktop app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for desktop app
    allow_credentials=False,  # Must be False when using wildcard origins
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize async checkpointer on FastAPI startup
@app.on_event("startup")
async def startup_event():
    """Initialize async checkpointer when FastAPI starts"""
    from graph.checkpointer import init_checkpointer_async, checkpointer, CHECKPOINTER_TYPE
    import logging
    logger = logging.getLogger(__name__)
    try:
        # Initialize the async checkpointer
        initialized_checkpointer = await init_checkpointer_async()
        logger.info(f"✅ Checkpointer initialized: {type(initialized_checkpointer).__name__}")
        
        # Rebuild graph with proper checkpointer
        # This is critical - build_graph() will now import the updated checkpointer
        from graph.builder import build_graph
        import main
        main.graph = build_graph()
        logger.info("✅ Graph rebuilt with async checkpointer")
        
        # Verify checkpointer is being used
        if CHECKPOINTER_TYPE in ["postgres", "supabase"]:
            logger.info(f"✅ Using {CHECKPOINTER_TYPE} checkpointer (persistent)")
            logger.info("💾 State will be automatically saved to Supabase after each node execution")
            # Verify the graph is actually using the async checkpointer
            if hasattr(main.graph, 'checkpointer'):
                logger.info(f"✅ Graph checkpointer verified: {type(main.graph.checkpointer).__name__}")
        else:
            logger.info(f"✅ Using {CHECKPOINTER_TYPE} checkpointer")
    except Exception as e:
        logger.error(f"❌ Failed to initialize checkpointer on startup: {e}")
        import traceback
        logger.error(traceback.format_exc())

# Request/Response Models
class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    user_identifier: Optional[str] = None
    data_sources: Optional[Dict[str, bool]] = None
    image_base64: Optional[str] = None  # Single screenshot/image as base64 (backwards compatible)
    images_base64: Optional[List[str]] = None  # Multiple images as base64 array

class CypherRequest(BaseModel):
    query: str
    params: Optional[Dict[str, Any]] = None

class CypherResponse(BaseModel):
    success: bool
    columns: Optional[List[str]] = None
    rows: Optional[List[Any]] = None
    row_count: Optional[int] = None
    error: Optional[str] = None
    query: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str
    session_id: str
    timestamp: str
    latency_ms: float
    citations: int
    route: Optional[str] = None
    message_id: Optional[str] = None
    project_answer: Optional[str] = None  # Separate project answer when multiple databases enabled
    code_answer: Optional[str] = None  # Separate code answer when code database enabled
    coop_answer: Optional[str] = None  # Separate coop answer when coop database enabled
    project_citations: Optional[int] = None
    code_citations: Optional[int] = None
    coop_citations: Optional[int] = None
    image_similarity_results: Optional[List[Dict[str, Any]]] = None  # Similar images found via image embedding search
    thinking_log: Optional[List[str]] = None  # Agent thinking logs for frontend display
    follow_up_questions: Optional[List[str]] = None  # Follow-up questions generated by verifier
    follow_up_suggestions: Optional[List[str]] = None  # Follow-up suggestions generated by verifier

class FeedbackRequest(BaseModel):
    message_id: str
    rating: str  # 'positive' or 'negative'
    comment: Optional[str] = ""
    user_question: str
    response: str
    timestamp: str

class HealthResponse(BaseModel):
    status: str
    system_info: Dict[str, Any]
    timestamp: str

# Health Check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """System health check"""
    try:
        # Get system info from rag healthcheck
        health_info = rag_healthcheck()
        
        return HealthResponse(
            status="healthy",
            system_info=health_info,
            timestamp=datetime.now().isoformat()
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            system_info={"error": str(e)},
            timestamp=datetime.now().isoformat()
        )

# Debug endpoint to check if project categories and playbook are loaded
@app.get("/debug/categories")
async def debug_categories():
    """Debug endpoint to check if project categories and playbook are loaded"""
    try:
        # Check categories
        categories_loaded = PROJECT_CATEGORIES != "No project categories provided."
        categories_file_exists = CATEGORIES_PATH.exists() if hasattr(CATEGORIES_PATH, 'exists') else False
        
        # Check playbook
        playbook_loaded = PLANNER_PLAYBOOK != "No playbook provided."
        playbook_file_exists = PLAYBOOK_PATH.exists() if hasattr(PLAYBOOK_PATH, 'exists') else False
        
        return {
            "categories": {
                "loaded": categories_loaded,
                "file_path": str(CATEGORIES_PATH),
                "file_exists": categories_file_exists,
                "content_length": len(PROJECT_CATEGORIES) if categories_loaded else 0,
                "preview": PROJECT_CATEGORIES[:500] if categories_loaded else "Not loaded"
            },
            "playbook": {
                "loaded": playbook_loaded,
                "file_path": str(PLAYBOOK_PATH),
                "file_exists": playbook_file_exists,
                "content_length": len(PLANNER_PLAYBOOK) if playbook_loaded else 0,
                "preview": PLANNER_PLAYBOOK[:500] if playbook_loaded else "Not loaded"
            },
            "error": None
        }
    except Exception as e:
        return {
            "categories": {
                "loaded": False,
                "file_path": "Unknown",
                "file_exists": False,
                "error": str(e)
            },
            "playbook": {
                "loaded": False,
                "file_path": "Unknown",
                "file_exists": False,
                "error": str(e)
            },
            "error": str(e)
        }

# Main chat endpoint
# NOTE: This endpoint should ideally not be called if /chat/stream is being used.
# If both are called, it causes duplication. Frontend should use /chat/stream for real-time logs.
@app.post("/chat", response_model=ChatResponse)
async def chat_handler(request: ChatRequest):
    """
    Handle chat requests from the Electron chatbutton app.
    
    WARNING: This endpoint runs the full pipeline synchronously. For real-time thinking logs,
    use /chat/stream instead. If both endpoints are called, it causes duplication.

    Expected request format:
    {
        "message": "What are the roof truss bracing notes for 25-07-003?",
        "session_id": "desktop"
    }

    Returns:
    {
        "reply": "The answer from the RAG system...",
        "session_id": "desktop",
        "timestamp": "2024-01-01T12:00:00",
        "latency_ms": 1250.5,
        "citations": 5,
        "route": "drawings",
        "message_id": "msg_12345_abcdef"
    }
    """
    import time
    import uuid
    start_time = time.time()

    try:
        logger.info(f"Processing chat request from session '{request.session_id}': {request.message[:100]}...")
        logger.warning("⚠️ /chat endpoint called - consider using /chat/stream for real-time logs to avoid duplication")

        # Generate unique message ID for feedback tracking
        message_id = f"msg_{int(time.time())}_{uuid.uuid4().hex[:8]}"

        # Consolidate images: use images_base64 array if provided, else fallback to single image_base64
        images_to_process = request.images_base64 or []
        if not images_to_process and request.image_base64:
            images_to_process = [request.image_base64]  # Backwards compatibility
        
        # Log image receipt status
        logger.info(f"📸 IMAGE RECEIPT: images_base64={request.images_base64 is not None}, image_base64={request.image_base64 is not None}")
        logger.info(f"📸 IMAGES TO PROCESS: count={len(images_to_process)}, has_images={len(images_to_process) > 0}")
        if images_to_process:
            logger.info(f"📸 Image data lengths: {[len(img) for img in images_to_process[:3]]} chars (showing first 3)")
        
        # Run the agentic RAG system (with optional images for VLM processing)
        # Use wrapper that adds thinking logs
        from thinking.rag_wrapper import run_agentic_rag_with_thinking_logs
        
        logger.info(f"🔄 Calling run_agentic_rag_with_thinking_logs with images_base64={images_to_process if images_to_process else None}")
        rag_result = run_agentic_rag_with_thinking_logs(
            question=request.message,
            session_id=request.session_id,
            data_sources=request.data_sources,
            images_base64=images_to_process if images_to_process else None
        )

        # Extract the answer(s)
        answer = rag_result.get("answer", "No answer generated.")
        code_answer = rag_result.get("code_answer")  # May be None if code_db not enabled
        coop_answer = rag_result.get("coop_answer")  # May be None if coop_manual not enabled
        code_citations = rag_result.get("code_citations", [])
        coop_citations = rag_result.get("coop_citations", [])
        project_citations = rag_result.get("citations", [])
        image_similarity_results = rag_result.get("image_similarity_results", [])  # Similar images from embedding search
        follow_up_questions = rag_result.get("follow_up_questions", [])  # Follow-up questions from verifier
        follow_up_suggestions = rag_result.get("follow_up_suggestions", [])  # Follow-up suggestions from verifier
        
        # Check which databases were used
        has_project = bool(answer and answer.strip())
        has_code = bool(code_answer and code_answer.strip())
        has_coop = bool(coop_answer and coop_answer.strip())
        enabled_count = sum([has_project, has_code, has_coop])
        multiple_enabled = enabled_count > 1
        
        # Note: References sections are no longer added automatically
        # Only inline citations in brackets are used (as specified in the prompts)
        
        # Handle empty or None answers
        if not answer or answer.strip() == "":
            # Only set error message if there's no code_answer or coop_answer (pure project_db mode)
            if not code_answer or not code_answer.strip():
                if not coop_answer or not coop_answer.strip():
                    answer = "I couldn't generate a response. Please try rephrasing your question or check that the system is properly configured."
        
        # Process answers separately for multi-bubble display
        if multiple_enabled:
            # Multiple databases enabled - return separate answers
            # Strip asterisks from project names/numbers
            processed_project_answer = strip_asterisks_from_projects(answer) if has_project else None
            
            # Wrap code file citations with file-link tags (shows filename)
            processed_code_answer = wrap_code_file_links(code_answer, code_citations) if (has_code and code_citations) else code_answer
            
            # Convert external links to file-link format (for sidian-bot links) - works with existing frontend handlers
            if has_code:
                processed_code_answer = wrap_external_links(processed_code_answer)
            
            # Wrap coop file citations with file-link tags (shows page number only)
            processed_coop_answer = wrap_coop_file_links(coop_answer, coop_citations) if (has_coop and coop_citations) else coop_answer
            
            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000

            # Log to Supabase (combine for logging purposes)
            supabase_logger = get_supabase_logger()
            if supabase_logger.enabled:
                user_identifier = request.user_identifier or f"{os.getenv('USERNAME', 'unknown')}@{os.getenv('COMPUTERNAME', 'unknown')}"
                # Build combined logging text
                parts = []
                if has_project:
                    parts.append(answer)
                if has_code:
                    parts.append(f"--- Code References ---\n\n{code_answer}")
                if has_coop:
                    parts.append(f"--- Training Manual References ---\n\n{coop_answer}")
                combined_for_logging = "\n\n".join(parts)
                
                # Upload first image if provided (for logging)
                image_url = None
                if images_to_process and len(images_to_process) > 0:
                    image_url = supabase_logger.upload_image(
                        images_to_process[0],
                        message_id,
                        "image/png"
                    )

                query_data = {
                    "message_id": message_id,
                    "session_id": request.session_id,
                    "user_query": request.message,
                    "rag_response": combined_for_logging,
                    "route": rag_result.get("route"),
                    "citations_count": len(project_citations) + len(code_citations) + len(coop_citations),
                    "latency_ms": round(latency_ms, 2),
                    "user_identifier": user_identifier,
                    "image_url": image_url
                }
                supabase_logger.log_user_query(query_data)

            # Extract thinking log from result
            thinking_log = rag_result.get("thinking_log", [])
            
            # Return separate answers
            response = ChatResponse(
                reply=processed_project_answer or processed_code_answer or processed_coop_answer or "No answer generated.",  # Primary answer (for backward compatibility)
                session_id=request.session_id,
                timestamp=datetime.now().isoformat(),
                latency_ms=round(latency_ms, 2),
                citations=len(project_citations) + len(code_citations) + len(coop_citations),  # Total citations
                route=rag_result.get("route"),
                message_id=message_id,
                project_answer=processed_project_answer,
                code_answer=processed_code_answer,
                coop_answer=processed_coop_answer,
                project_citations=len(project_citations) if has_project else None,
                code_citations=len(code_citations) if has_code else None,
                coop_citations=len(coop_citations) if has_coop else None,
                image_similarity_results=image_similarity_results if image_similarity_results else None,
                thinking_log=thinking_log if thinking_log else None,
                follow_up_questions=follow_up_questions if follow_up_questions else None,
                follow_up_suggestions=follow_up_suggestions if follow_up_suggestions else None
            )
        else:
            # Single answer mode (backward compatible)
            if code_answer and code_answer.strip():
                combined_answer = code_answer
                total_citations = len(code_citations)
            elif coop_answer and coop_answer.strip():
                combined_answer = coop_answer
                total_citations = len(coop_citations)
            else:
                combined_answer = answer
                total_citations = len(project_citations)
            
            # Strip asterisks from project names/numbers
            combined_answer = strip_asterisks_from_projects(combined_answer)
            
            # Wrap code file citations with file-link tags for clickable links
            if code_citations:
                combined_answer = wrap_code_file_links(combined_answer, code_citations)
            
            # Wrap coop file citations with file-link tags for clickable links
            if coop_citations:
                combined_answer = wrap_code_file_links(combined_answer, coop_citations)
            
            # Convert external links to file-link format (for sidian-bot links) - works with existing frontend handlers
            if code_answer and code_answer.strip():
                combined_answer = wrap_external_links(combined_answer)

            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000

            # Log to Supabase
            supabase_logger = get_supabase_logger()
            if supabase_logger.enabled:
                user_identifier = request.user_identifier or f"{os.getenv('USERNAME', 'unknown')}@{os.getenv('COMPUTERNAME', 'unknown')}"
                
                # Upload first image if provided (for logging)
                image_url = None
                if images_to_process and len(images_to_process) > 0:
                    image_url = supabase_logger.upload_image(
                        images_to_process[0],
                        message_id,
                        "image/png"
                    )

                query_data = {
                    "message_id": message_id,
                    "session_id": request.session_id,
                    "user_query": request.message,
                    "rag_response": combined_answer,
                    "route": rag_result.get("route"),
                    "citations_count": total_citations,
                    "latency_ms": round(latency_ms, 2),
                    "user_identifier": user_identifier,
                    "image_url": image_url
                }
                supabase_logger.log_user_query(query_data)

            # Extract thinking log from result
            thinking_log = rag_result.get("thinking_log", [])
            
            # Prepare response
            response = ChatResponse(
                reply=combined_answer,
                session_id=request.session_id,
                timestamp=datetime.now().isoformat(),
                latency_ms=round(latency_ms, 2),
                citations=total_citations,
                route=rag_result.get("route"),
                message_id=message_id,
                image_similarity_results=image_similarity_results if image_similarity_results else None,
                thinking_log=thinking_log if thinking_log else None,
                follow_up_questions=follow_up_questions if follow_up_questions else None,
                follow_up_suggestions=follow_up_suggestions if follow_up_suggestions else None
            )

        logger.info(f"Successfully processed request in {latency_ms:.2f}ms [ID: {message_id}]")
        return response

    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        latency_ms = (time.time() - start_time) * 1000

        # Return error response
        error_response = ChatResponse(
            reply=f"I encountered an error while processing your request: {str(e)}",
            session_id=request.session_id,
            timestamp=datetime.now().isoformat(),
            latency_ms=round(latency_ms, 2),
            citations=0,
            message_id=f"err_{int(time.time())}",
            thinking_log=None
        )

        # Don't raise HTTPException here - return error message instead
        # The Electron app expects a ChatResponse object
        return error_response


# Streaming chat endpoint with real-time thinking logs
@app.post("/chat/stream")
async def chat_stream_handler(request: ChatRequest):
    """
    Streaming chat endpoint that emits thinking logs in real-time via Server-Sent Events (SSE).
    
    Returns:
        StreamingResponse with SSE format:
        - data: {"type": "connected"} - Initial connection
        - data: {"type": "thinking", "message": "...", "node": "...", "timestamp": ...} - Thinking logs
        - data: {"type": "complete", "result": {...}} - Final result
        - data: {"type": "error", "message": "..."} - Error messages
    """
    import time
    import uuid
    import asyncio
    
    def _extract_projects(docs):
        """Extract project keys from documents"""
        projects = set()
        for doc in docs:
            if hasattr(doc, 'metadata') and isinstance(doc.metadata, dict):
                proj = doc.metadata.get("drawing_number") or doc.metadata.get("project_key")
                if proj:
                    projects.add(proj)
        return list(projects)[:20]
    
    def _extract_projects_from_citations(citations):
        """Extract project keys from citations"""
        projects = set()
        for citation in citations:
            if isinstance(citation, dict):
                proj = citation.get("project_key") or citation.get("drawing_number")
                if proj:
                    projects.add(proj)
        return list(projects)[:20]
    
    async def generate_stream():
        """Generate SSE stream of thinking logs and final result"""
        start_time = time.time()
        message_id = f"msg_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        try:
            # Send initial connection event
            logger.info(f"📡 Starting streaming response for message: {request.message[:100]}...")
            yield f"data: {json.dumps({'type': 'connected', 'message_id': message_id})}\n\n"
            
            # Consolidate images
            images_to_process = request.images_base64 or []
            if not images_to_process and request.image_base64:
                images_to_process = [request.image_base64]
            
            # Log image receipt status (matching chat endpoint)
            logger.info(f"📸 IMAGE RECEIPT: images_base64={request.images_base64 is not None}, image_base64={request.image_base64 is not None}")
            logger.info(f"📸 IMAGES TO PROCESS: count={len(images_to_process)}, has_images={len(images_to_process) > 0}")
            if images_to_process:
                logger.info(f"📸 Image data lengths: {[len(img) for img in images_to_process[:3]]} chars (showing first 3)")
            
            # Process images if provided - Convert to searchable text via VLM (matching chat endpoint)
            # This is the key difference - chat endpoint does this before graph execution
            image_context = ""
            enhanced_question = request.message
            if images_to_process and len(images_to_process) > 0:
                from nodes.DBRetrieval.SQLdb.image_nodes import describe_image_for_search
                from config.logging_config import log_vlm
                
                log_vlm.info("")
                log_vlm.info("🔷" * 30)
                log_vlm.info(f"🖼️ PROCESSING {len(images_to_process)} IMAGE(S) WITH VLM")
                log_vlm.info(f"📝 User question: {request.message[:150] if request.message else 'General image description'}")
                log_vlm.info("🔷" * 30)
                
                # Emit thinking log for VLM processing
                # Log VLM processing to terminal and send to stream for Agent Thinking panel
                logger.info(f"🖼️ Processing {len(images_to_process)} image(s) with vision model...")
                # Send to stream for Agent Thinking panel - frontend will route to correct panel
                yield f"data: {json.dumps({'type': 'thinking', 'message': f'Processing {len(images_to_process)} image(s) with vision model...', 'node': 'vlm_processing', 'timestamp': time.time()})}\n\n"
                await asyncio.sleep(0.001)
                
                image_descriptions = []
                for i, image_base64 in enumerate(images_to_process):
                    log_vlm.info("")
                    log_vlm.info(f"📸 Processing image {i+1}/{len(images_to_process)}")
                    try:
                        image_description = describe_image_for_search(image_base64, request.message)
                        image_descriptions.append(f"Image {i+1}: {image_description}")
                        log_vlm.info(f"✅ Image {i+1} description completed successfully")
                    except Exception as e:
                        log_vlm.error(f"❌ VLM processing failed for image {i+1}, skipping: {e}")
                
                if image_descriptions:
                    image_context = "\n\n[Image Context: " + " | ".join(image_descriptions) + "]"
                    enhanced_question = request.message + image_context
                    log_vlm.info("")
                    log_vlm.info(f"📊 ALL IMAGES PROCESSED - Combined context length: {len(image_context)} chars")
                    log_vlm.info("🔷" * 30)
                    log_vlm.info("")
            
            # Import graph and state
            from main import graph
            from models.parent_state import ParentState
            from dataclasses import asdict
            from thinking.intelligent_log_generator import IntelligentLogGenerator
            from models.memory import intelligent_query_rewriter
            
            log_generator = IntelligentLogGenerator()
            
            # CRITICAL: Load previous state from checkpointer to get messages
            # This follows LangGraph best practices for short-term memory
            # Messages are persisted by checkpointer and loaded here for conversation context
            previous_state = None
            try:
                # Get the latest checkpoint state for this thread
                # For async checkpointers, use aget_state() instead of get_state()
                from graph.checkpointer import CHECKPOINTER_TYPE
                if CHECKPOINTER_TYPE in ["postgres", "supabase"]:
                    # Async checkpointer - use async method
                    state_snapshot = await graph.aget_state({"configurable": {"thread_id": request.session_id}})
                else:
                    # Sync checkpointer - use sync method
                    state_snapshot = graph.get_state({"configurable": {"thread_id": request.session_id}})
                
                if state_snapshot and state_snapshot.values:
                    previous_state = state_snapshot.values
                    logger.info(f"📖 Loaded previous state from checkpointer for thread_id={request.session_id}")
                    if previous_state.get("messages"):
                        logger.info(f"📖 Found {len(previous_state['messages'])} previous messages")
            except Exception as e:
                # No previous state exists (first invocation) - this is fine
                logger.info(f"📖 No previous state found (first invocation): {e}")
                previous_state = None
            
            # Get messages from previous state for query rewriting and context
            previous_messages = previous_state.get("messages", []) if previous_state else []
            
            # Intelligent query rewriting with conversation context
            # This helps with follow-up detection and pronoun resolution
            rewritten_query, query_filters = intelligent_query_rewriter(
                enhanced_question,
                request.session_id,
                messages=previous_messages
            )
            logger.info(f"🎯 QUERY REWRITING: '{enhanced_question[:100]}...' → '{rewritten_query[:100]}...'" if len(enhanced_question) > 100 or len(rewritten_query) > 100 else f"🎯 QUERY REWRITING: '{enhanced_question}' → '{rewritten_query}'")
            
            # Extract project filter from query_filters if present
            project_filter = None
            if query_filters.get("project_keys"):
                project_filter = query_filters["project_keys"][0]
                logger.info(f"🎯 PROJECT FILTER FROM REWRITER: {project_filter}")
            
            # Determine if image similarity should be enabled
            use_image_similarity = False
            query_intent = None
            if images_to_process:
                from nodes.DBRetrieval.SQLdb.image_nodes import classify_image_query_intent
                intent_result = classify_image_query_intent(request.message, images_to_process[0])
                use_image_similarity = intent_result.get("use_image_similarity", False)
                query_intent = intent_result.get("intent")
            
            # CRITICAL: Initialize messages from previous state and add new user message
            # This follows LangGraph's pattern: messages flow through the graph state
            # The checkpointer automatically persists messages after each node execution
            init_messages = list(previous_messages) if previous_messages else []
            
            # Add the current user message to the conversation history
            # This ensures nodes like rag_plan can see the full conversation context
            init_messages.append({
                "role": "user",
                "content": request.message  # Use original question, not rewritten query
            })
            
            logger.info(f"📖 Initialized messages: {len(previous_messages) if previous_messages else 0} previous + 1 new = {len(init_messages)} total")
            
            # Create initial state with messages and original question
            # This follows LangGraph best practices for short-term memory
            init_state = ParentState(
                session_id=request.session_id,
                user_query=rewritten_query,  # Rewritten query for retrieval (with context)
                original_question=request.message,  # Original question (for storing in messages)
                images_base64=images_to_process if images_to_process else None,
                messages=init_messages,  # CRITICAL: Includes previous messages + new user message
                selected_routers=[],  # Will be set by plan node
                # Results will be populated by subgraphs
                db_retrieval_result=None,
                db_retrieval_citations=[],
                db_retrieval_follow_up_questions=[],
                db_retrieval_follow_up_suggestions=[],
                db_retrieval_selected_projects=[],
                webcalcs_result=None,
                desktop_result=None,
                build_model_result=None,
            )
            
            # Track state as we go to detect which node ran
            previous_state = asdict(init_state)
            final_result = None
            
            config = {
                "configurable": {"thread_id": request.session_id}
            }
            
            # Use LangGraph's native streaming with stream_mode="updates"
            # "updates" mode gives us {node_name: state_updates} so we can identify which node ran
            # "custom" mode gives us custom events emitted from nodes
            accumulated_state = asdict(init_state)
            final_state = None
            
            logger.info(f"🔄 Starting graph.astream with stream_mode=['updates', 'custom', 'messages']")
            
            # Use "exit" durability mode to only save final state (not after each node)
            # This dramatically reduces storage costs - only 1 checkpoint per query instead of 7+
            # Trade-off: Can't resume from intermediate nodes, but you only need final state for memory
            durability_mode = os.getenv("CHECKPOINTER_DURABILITY", "exit").lower()  # "exit", "async", or "sync"
            if durability_mode == "exit":
                logger.info(f"💾 Checkpointer: Will save ONLY final state (exit mode) - reduces storage by ~85%")
            else:
                logger.info(f"💾 Checkpointer: Will save state after each node ({durability_mode} mode)")
            
            node_count = 0
            # Use multiple stream modes per LangGraph best practices:
            # - "updates": State updates per node with node names {node_name: state_updates}
            # - "custom": Custom events emitted from nodes (for real-time progress)
            # - "messages": LLM tokens as they're generated (for real-time answer streaming)
            # NOTE: LangGraph automatically saves state to checkpointer after each node when:
            #       1. Graph is compiled with checkpointer
            #       2. Config includes thread_id
            #       3. Using graph.astream() or graph.ainvoke()
            #       4. Durability mode controls WHEN it saves (exit = only at end, async/sync = after each node)
            # CRITICAL: durability is a DIRECT parameter, not in config dict!
            messages_received = 0
            interrupt_detected = False
            interrupt_payload = None
            completion_executed = False  # Flag to ensure completion code runs only once
            
            try:
                async for stream_item in graph.astream(
                    asdict(init_state),
                    config=config,
                    stream_mode=["updates", "custom", "messages"],  # Add "messages" for token streaming
                    durability=durability_mode,  # Pass durability as direct parameter, not in config
                    subgraphs=True  # CRITICAL: Include outputs from subgraphs (e.g., db_retrieval subgraph) in stream
                ):
                    # Handle different stream formats (with/without subgraphs)
                    # When subgraphs=True with multiple stream modes, format is: (namespace, stream_mode, chunk)
                    # When subgraphs=False or single mode, format is: (stream_mode, chunk)
                    # namespace is a tuple like ('node_name:task_id',) for subgraph nodes, or () for parent nodes
                    if isinstance(stream_item, tuple) and len(stream_item) == 3:
                        # Format: (namespace, stream_mode, chunk) when subgraphs=True with multiple modes
                        namespace, stream_mode, chunk = stream_item
                        # Log subgraph namespace for debugging (first few only)
                        if node_count < 5 and namespace:
                            logger.debug(f"📦 Subgraph namespace: {namespace}")
                    elif isinstance(stream_item, tuple) and len(stream_item) == 2:
                        # Format: (stream_mode, chunk) when subgraphs=False or single mode
                        stream_mode, chunk = stream_item
                        namespace = ()  # No namespace for parent graph nodes
                    else:
                        # Unexpected format - log and skip
                        logger.warning(f"⚠️ Unexpected stream format: {type(stream_item)}, length: {len(stream_item) if isinstance(stream_item, tuple) else 'N/A'}")
                        logger.warning(f"⚠️ Stream item: {str(stream_item)[:200]}")
                        continue
                    # Handle LLM token streaming (messages mode)
                    # This captures tokens directly from LLM calls made within nodes
                    if stream_mode == "messages":
                        messages_received += 1
                        # Log first few messages to debug
                        if messages_received <= 5:
                            logger.info(f"📨 Messages mode event #{messages_received}: type={type(chunk)}, chunk={str(chunk)[:200]}")
                        
                        # chunk is a tuple: (AIMessageChunk, metadata)
                        if isinstance(chunk, tuple) and len(chunk) >= 2:
                            message_chunk = chunk[0]
                            metadata = chunk[1] if len(chunk) > 1 else {}
                            
                            # Get the content from the message chunk
                            if hasattr(message_chunk, 'content') and message_chunk.content:
                                # Extract text content - handles both string (OpenAI/Anthropic) and list (Gemini 3.0) formats
                                raw_content = message_chunk.content
                                token_content = extract_text_from_content(raw_content)
                                
                                # Skip if no text content extracted
                                if not token_content:
                                    continue
                                
                                # Check metadata for node info to filter tokens
                                node_name = metadata.get('langgraph_node', 'unknown') if isinstance(metadata, dict) else 'unknown'
                                
                                # IMPORTANT: Stream tokens from answer node (including subgraph paths like "db_retrieval.answer")
                                # Filter out tokens ONLY from known planning/routing nodes that don't generate user-facing content
                                # These are internal processing and should only show as thinking logs
                                skip_nodes = ['plan', 'rag_plan_router', 'rag_plan', 'rag_router', 'retrieve', 'grade', 'verify', 'correct', 'router_dispatcher']
                                
                                # Check if node_name contains any skip pattern (handles subgraph paths like "db_retrieval.retrieve")
                                # BUT: Allow "answer" nodes even if they're in subgraphs (e.g., "db_retrieval.answer")
                                should_skip = False
                                if node_name != 'unknown':
                                    # Check if it's a skip node
                                    node_lower = node_name.lower()
                                    should_skip = any(skip_node in node_lower for skip_node in skip_nodes)
                                    # BUT: If it contains "answer", always stream it (even if it also contains a skip node name)
                                    if 'answer' in node_lower:
                                        should_skip = False
                                
                                # Stream tokens from answer nodes or unknown nodes (unknown = likely from subgraphs)
                                if should_skip:
                                    # Log to terminal but don't stream to main chat - these are internal processing tokens
                                    if messages_received <= 10:  # Log first 10 skips for debugging
                                        logger.info(f"⏭️  Skipping token from node '{node_name}' (internal processing node)")
                                    continue
                                
                                # Strip asterisks from project patterns
                                token_content = strip_asterisks_from_projects(token_content)
                                
                                # Stream token to frontend (answer node tokens and unknown nodes)
                                if messages_received <= 10:  # Log first 10 tokens for debugging
                                    logger.info(f"💬 Streaming token #{messages_received}: {len(token_content)} chars from node '{node_name}'")
                                yield f"data: {json.dumps({'type': 'token', 'content': token_content, 'node': node_name, 'timestamp': time.time()})}\n\n"
                                # REMOVED: await asyncio.sleep(0.001) - unnecessary delay for real-time streaming
                        continue
                
                    # Handle custom events (emitted directly from nodes)
                    if stream_mode == "custom":
                        logger.debug(f"📨 Custom event received: {chunk}")
                        # Handle custom events - send thinking logs to Agent Thinking panel, tokens to main chat
                        if isinstance(chunk, dict):
                            if chunk.get("type") == "thinking":
                                # Send thinking log to stream for Agent Thinking panel
                                logger.info(f"💭 {chunk.get('message', '')}")
                                yield f"data: {json.dumps({'type': 'thinking', 'message': chunk.get('message', ''), 'node': chunk.get('node', 'unknown'), 'timestamp': time.time()})}\n\n"
                                # REMOVED: await asyncio.sleep(0.001) - unnecessary delay
                            elif chunk.get("type") == "token":
                                # Forward token to frontend for real-time streaming (from stream writer)
                                token_content = chunk.get('content', '')
                                token_node = chunk.get('node', 'answer')
                                # Strip asterisks from project patterns in token
                                token_content = strip_asterisks_from_projects(token_content)
                                
                                # Stream immediately - no delay for real-time token-by-token
                                logger.debug(f"💬 Streaming token from stream writer (node '{token_node}'): {len(token_content)} chars")
                                yield f"data: {json.dumps({'type': 'token', 'content': token_content, 'node': token_node, 'timestamp': time.time()})}\n\n"
                                # REMOVED: await asyncio.sleep(0.001) - unnecessary delay
                        continue
                
                    # Handle state updates (updates mode)
                    if stream_mode != "updates":
                        continue
                    
                    # chunk is now {node_name: state_updates_dict}
                    # This gives us the node name directly as the key
                    node_outputs = chunk
                    logger.info(f"📦 Received node_outputs: {list(node_outputs.keys())}")
                    
                    for node_key, state_updates in node_outputs.items():
                        node_count += 1
                        
                        # Handle subgraph nodes: node_key can be a tuple like ('db_retrieval:thread_id', 'retrieve')
                        # or a string like 'plan'
                        if isinstance(node_key, tuple):
                            # Subgraph node: extract the actual node name
                            subgraph_name = node_key[0] if len(node_key) > 0 else 'unknown'
                            node_name = node_key[-1] if len(node_key) > 1 else subgraph_name
                            logger.info(f"🔍 Processing subgraph node #{node_count}: '{node_name}' (from subgraph '{subgraph_name}')")
                        else:
                            # Regular parent graph node
                            node_name = node_key
                            logger.info(f"🔍 Processing node #{node_count}: '{node_name}'")
                        
                        # CRITICAL: Handle __interrupt__ node FIRST - this is how LangGraph signals interrupts in astream mode
                        # When using .astream(), interrupts appear as __interrupt__ node output, not as exceptions
                        # Must check BEFORE the dict check because state_updates might not be a dict for interrupts
                        if node_name == "__interrupt__":
                            interrupt_detected = True  # Set flag to prevent completion code from running
                            logger.info("⏸️  INTERRUPT NODE DETECTED in stream - extracting interrupt information")
                            logger.info(f"📋 Interrupt node_key={node_key}, state_updates type={type(state_updates)}")
                            
                            # Extract interrupt information directly from state_updates
                            # In astream mode, state_updates for __interrupt__ is a tuple containing an Interrupt object
                            try:
                                interrupt_value = None
                                interrupt_id = None
                                
                                # state_updates is a tuple: (Interrupt(value={...}, id=...), ...)
                                if isinstance(state_updates, tuple) and len(state_updates) > 0:
                                    interrupt_obj = state_updates[0]  # Get first Interrupt object
                                    if hasattr(interrupt_obj, 'value'):
                                        interrupt_value = interrupt_obj.value
                                    if hasattr(interrupt_obj, 'id'):
                                        interrupt_id = interrupt_obj.id
                                    
                                    logger.info(f"⏸️  INTERRUPT EXTRACTED: type={interrupt_value.get('type') if isinstance(interrupt_value, dict) else 'unknown'}, id={interrupt_id}")
                                
                                # Fallback: check if it's a dict (shouldn't happen, but be safe)
                                elif isinstance(state_updates, dict):
                                    if "__interrupt__" in state_updates:
                                        interrupt_list = state_updates.get("__interrupt__", [])
                                        if interrupt_list and len(interrupt_list) > 0:
                                            interrupt_obj = interrupt_list[0]
                                            if isinstance(interrupt_obj, dict):
                                                interrupt_value = interrupt_obj.get("value")
                                                interrupt_id = interrupt_obj.get("id")
                                            elif hasattr(interrupt_obj, 'value'):
                                                interrupt_value = interrupt_obj.value
                                                interrupt_id = getattr(interrupt_obj, 'id', None)
                                
                                if interrupt_value is None:
                                    logger.error("❌ Could not extract interrupt information from state_updates")
                                    # Still send a basic interrupt event so frontend knows something happened
                                    interrupt_data = {
                                        "type": "interrupt",
                                        "interrupt_id": None,
                                        "interrupt_type": "unknown",
                                        "question": "Code verification required",
                                        "codes": [],
                                        "code_count": 0,
                                        "chunk_count": 0,
                                        "available_codes": [],
                                        "previously_retrieved": [],
                                        "session_id": request.session_id,
                                        "thread_id": request.session_id
                                    }
                                else:
                                    # Send interrupt event to frontend with extracted data
                                    interrupt_data = {
                                        "type": "interrupt",
                                        "interrupt_id": interrupt_id,
                                        "interrupt_type": interrupt_value.get("type") if isinstance(interrupt_value, dict) else "unknown",
                                        "question": interrupt_value.get("question") if isinstance(interrupt_value, dict) else "",
                                        "codes": interrupt_value.get("codes") if isinstance(interrupt_value, dict) else [],
                                        "code_count": interrupt_value.get("code_count") if isinstance(interrupt_value, dict) else 0,
                                        "chunk_count": interrupt_value.get("chunk_count") if isinstance(interrupt_value, dict) else 0,
                                        "available_codes": interrupt_value.get("available_codes") if isinstance(interrupt_value, dict) else [],
                                        "previously_retrieved": interrupt_value.get("previously_retrieved") if isinstance(interrupt_value, dict) else [],
                                        "session_id": request.session_id,
                                        "thread_id": request.session_id
                                    }
                                
                                yield f"data: {json.dumps(interrupt_data)}\n\n"
                                logger.info(f"📤 Sent interrupt event to frontend: {interrupt_data.get('interrupt_type')}")
                                codes_list = interrupt_data.get('codes') or []
                                available_codes_list = interrupt_data.get('available_codes') or []
                                logger.info(f"📋 Interrupt payload: codes={len(codes_list)}, available_codes={len(available_codes_list)}")
                                return  # Stop streaming - wait for resume
                            except Exception as e:
                                logger.error(f"❌ Failed to extract interrupt information: {e}")
                                import traceback
                                traceback.print_exc()
                                # Send a basic interrupt event anyway
                                interrupt_data = {
                                    "type": "interrupt",
                                    "interrupt_id": None,
                                    "interrupt_type": "code_verification",
                                    "question": "Code verification required",
                                    "codes": [],
                                    "code_count": 0,
                                    "chunk_count": 0,
                                    "available_codes": [],
                                    "previously_retrieved": [],
                                    "session_id": request.session_id,
                                    "thread_id": request.session_id
                                }
                                yield f"data: {json.dumps(interrupt_data)}\n\n"
                                logger.info("📤 Sent fallback interrupt event to frontend")
                                return  # Stop streaming - wait for resume
                        
                        # Skip non-dict state_updates for regular nodes (but interrupts are handled above)
                        if not isinstance(state_updates, dict):
                            continue
                        
                        # Merge state updates into accumulated state
                        # (updates mode gives us only the changes, not full state)
                        accumulated_state.update(state_updates)
                        state_dict = accumulated_state.copy()
                        
                        # Generate thinking log based on node using intelligent_log_generator and RAG state data
                        thinking_log = None
                        
                        if node_name == "plan":
                            plan = state_dict.get("query_plan") or {}
                            thinking_log = log_generator.generate_planning_log(
                                query=request.message,
                                plan=plan,
                                route=state_dict.get("data_route") or "smart",
                                project_filter=state_dict.get("project_filter")
                            )
                        elif node_name == "router_dispatcher":
                            thinking_log = log_generator.generate_router_dispatcher_log(
                                query=request.message,
                                selected_routers=state_dict.get("selected_routers", [])
                            )
                        elif node_name == "rag":
                            thinking_log = log_generator.generate_rag_log(
                                query=request.message,
                                query_plan=state_dict.get("query_plan"),
                                data_route=state_dict.get("data_route"),
                                data_sources=state_dict.get("data_sources")
                            )
                        elif node_name == "generate_image_embeddings":
                            image_count = len(state_dict.get("images_base64") or [])
                            thinking_log = log_generator.generate_image_embeddings_log(
                                query=request.message,
                                image_count=image_count
                            )
                        elif node_name == "image_similarity_search":
                            similarity_results = state_dict.get("image_similarity_results", [])
                            project_keys = set()
                            for img in similarity_results:
                                proj = img.get("project_key")
                                if proj:
                                    project_keys.add(proj)
                            thinking_log = log_generator.generate_image_similarity_log(
                                query=request.message,
                                result_count=len(similarity_results),
                                project_count=len(project_keys)
                            )
                        elif node_name == "retrieve":
                            # Handle both old field names and new db_retrieval_* field names
                            retrieved_docs = state_dict.get("retrieved_docs") or []
                            retrieved_code_docs = state_dict.get("retrieved_code_docs") or state_dict.get("retrieved_code_docs") or []
                            retrieved_coop_docs = state_dict.get("retrieved_coop_docs") or state_dict.get("retrieved_coop_docs") or []
                            thinking_log = log_generator.generate_retrieval_log(
                                query=request.message,
                                project_count=len(retrieved_docs),
                                code_count=len(retrieved_code_docs),
                                coop_count=len(retrieved_coop_docs),
                                projects=_extract_projects(retrieved_docs),
                                route=state_dict.get("data_route") or state_dict.get("db_retrieval_route") or "smart",
                                project_filter=state_dict.get("project_filter"),
                                query_plan=state_dict.get("query_plan")
                            )
                        elif node_name == "grade":
                            thinking_log = log_generator.generate_grading_log(
                                query=request.message,
                                retrieved_count=len(state_dict.get("retrieved_docs") or []),
                                graded_count=len(state_dict.get("graded_docs") or []),
                                filtered_out=len(state_dict.get("retrieved_docs") or []) - len(state_dict.get("graded_docs") or [])
                            )
                        elif node_name == "answer":
                            # Handle both old field names and new db_retrieval_* field names
                            citations = state_dict.get("db_retrieval_citations") or state_dict.get("answer_citations") or []
                            thinking_log = log_generator.generate_synthesis_log(
                                query=request.message,
                                graded_count=len(citations),
                                projects=_extract_projects_from_citations(citations),
                                has_code=bool(state_dict.get("db_retrieval_code_answer") or state_dict.get("code_answer")),
                                has_coop=bool(state_dict.get("db_retrieval_coop_answer") or state_dict.get("coop_answer"))
                            )
                        elif node_name == "verify":
                            # Handle both old field names and new db_retrieval_* field names
                            follow_up_q = state_dict.get("db_retrieval_follow_up_questions") or state_dict.get("follow_up_questions", [])
                            follow_up_s = state_dict.get("db_retrieval_follow_up_suggestions") or state_dict.get("follow_up_suggestions", [])
                            thinking_log = log_generator.generate_verify_log(
                                query=request.message,
                                needs_fix=state_dict.get("needs_fix", False),
                                follow_up_count=len(follow_up_q),
                                suggestion_count=len(follow_up_s)
                            )
                        elif node_name == "correct":
                            thinking_log = log_generator.generate_correct_log(
                                query=request.message,
                                support_score=state_dict.get("answer_support_score", 1.0),
                                corrective_attempted=state_dict.get("corrective_attempted", False)
                            )
                        else:
                            # For any unexpected nodes, log them but don't show to user
                            logger.info(f"Skipping thinking log for node: {node_name}")
                            thinking_log = None
                        
                        # Emit thinking log to stream for Agent Thinking panel (NOT displayed in main chat)
                        if thinking_log:
                            log_data = {'type': 'thinking', 'message': thinking_log, 'node': node_name, 'timestamp': time.time()}
                            logger.info(f"📤 Streaming thinking log for node '{node_name}': {thinking_log[:100]}...")
                            # Send to stream for Agent Thinking panel - frontend will route to correct panel
                            yield f"data: {json.dumps(log_data)}\n\n"
                            await asyncio.sleep(0.001)  # Minimal delay for proper streaming
                        else:
                            logger.info(f"⏭️  No thinking log generated for node '{node_name}'")
                        
                        # STREAM ANSWER IMMEDIATELY when answer node completes
                        # Don't wait for verify/correct - stream now for instant feedback!
                        if node_name == "answer" and messages_received == 0:
                            # Check all answer types: final_answer, code_answer, coop_answer
                            answer_text = (state_dict.get("final_answer") or 
                                          state_dict.get("code_answer") or 
                                          state_dict.get("coop_answer") or 
                                          state_dict.get("answer", ""))
                            if answer_text:
                                logger.info(f"📤 Streaming answer immediately ({len(answer_text)} chars)...")
                                # Split into words and stream in small groups
                                words = answer_text.split(' ')
                                chunk_size = 3  # Send 3 words at a time
                                for i in range(0, len(words), chunk_size):
                                    word_chunk = ' '.join(words[i:i+chunk_size])
                                    if i + chunk_size < len(words):
                                        word_chunk += ' '  # Add space if not last chunk
                                    # Strip asterisks from project patterns
                                    word_chunk = strip_asterisks_from_projects(word_chunk)
                                    yield f"data: {json.dumps({'type': 'token', 'content': word_chunk, 'node': 'answer', 'timestamp': time.time()})}\n\n"
                                    await asyncio.sleep(0.008)  # Small delay for visual effect
                                logger.info(f"✅ Finished streaming answer")
                        # DO NOT manually stream answer - tokens come via "messages" mode
                        # The manual word-by-word streaming causes duplication
                        # Tokens are already being streamed in real-time via messages mode (line 930)
                        # This manual streaming was causing word duplication ("Project Project", etc.)
                        if node_name == "answer":
                            logger.info(f"📤 Answer node completed - tokens streaming via messages mode (received: {messages_received})")
                        
                        # Store final state - correct node is the last one in DBRetrieval subgraph
                        # Also check for router_dispatcher completion (which calls subgraph)
                        final_state = state_dict.copy()
                        
                        # Break after correct node (last node in DBRetrieval pipeline)
                        # OR after router_dispatcher (which completes after subgraph finishes)
                        if node_name == "correct" or (node_name == "router_dispatcher" and "db_retrieval_result" in state_dict):
                            logger.info(f"✅ Breaking after node '{node_name}' - subgraph execution complete")
                            logger.info(f"📊 Final state keys: {list(state_dict.keys())[:20]}...")  # Log first 20 keys
                            logger.info(f"📊 db_retrieval_result present: {'db_retrieval_result' in state_dict}")
                            logger.info(f"📊 db_retrieval_result value: {str(state_dict.get('db_retrieval_result', 'None'))[:100] if state_dict.get('db_retrieval_result') else 'None'}")
                            break
                    
                    # Execute completion code once (after for loop, inside async for body, uses flag to run only once)
                    # CRITICAL: Skip completion code if interrupt was detected OR if we just processed an interrupt node
                    # Check if any node in this chunk was an interrupt before running completion
                    chunk_has_interrupt = any(key == "__interrupt__" or (isinstance(key, tuple) and key[-1] == "__interrupt__") for key in node_outputs.keys())
                    if chunk_has_interrupt:
                        logger.info("⏸️  Skipping completion code - interrupt detected in current chunk")
                    elif interrupt_detected:
                        logger.info("⏸️  Skipping completion code - interrupt was previously detected")
                    elif not completion_executed and final_state and not interrupt_detected and not chunk_has_interrupt:
                        # CRITICAL: Only run completion code if we have an actual answer, not just any state
                        # This prevents "No answer generated" from appearing prematurely
                        has_answer = bool(
                            final_state.get("db_retrieval_result") or 
                            final_state.get("final_answer") or 
                            final_state.get("answer") or
                            final_state.get("db_retrieval_code_answer") or 
                            final_state.get("code_answer") or
                            final_state.get("db_retrieval_coop_answer") or 
                            final_state.get("coop_answer")
                        )
                        if has_answer:
                            completion_executed = True
                            logger.info("✅ Running completion code - answer found in state")
                            
                            # Log streaming stats
                            logger.info(f"📊 Streaming stats: {messages_received} LLM token events received via messages mode")
                            
                            # Extract final answer
                            answer = final_state.get("db_retrieval_result") or final_state.get("final_answer") or final_state.get("answer")
                            code_answer = final_state.get("db_retrieval_code_answer") or final_state.get("code_answer")
                            coop_answer = final_state.get("db_retrieval_coop_answer") or final_state.get("coop_answer")
                            
                            if not answer or answer.strip() == "":
                                answer = code_answer or coop_answer or "No answer generated."
                            
                            code_citations = final_state.get("db_retrieval_code_citations") or final_state.get("code_citations", [])
                            coop_citations = final_state.get("db_retrieval_coop_citations") or final_state.get("coop_citations", [])
                            project_citations = final_state.get("db_retrieval_citations") or final_state.get("answer_citations", [])
                            image_similarity_results = final_state.get("db_retrieval_image_similarity_results") or final_state.get("image_similarity_results", [])
                            follow_up_questions = final_state.get("db_retrieval_follow_up_questions") or final_state.get("follow_up_questions", [])
                            follow_up_suggestions = final_state.get("db_retrieval_follow_up_suggestions") or final_state.get("follow_up_suggestions", [])
                            
                            has_project = bool(answer and answer.strip())
                            has_code = bool(code_answer and code_answer.strip())
                            has_coop = bool(coop_answer and coop_answer.strip())
                            enabled_count = sum([has_project, has_code, has_coop])
                            multiple_enabled = enabled_count > 1
                            
                            if not answer or answer.strip() == "":
                                if not code_answer or not code_answer.strip():
                                    if not coop_answer or not coop_answer.strip():
                                        answer = "I couldn't generate a response. Please try rephrasing your question or check that the system is properly configured."
                            
                            latency_ms = (time.time() - start_time) * 1000
                            
                            if multiple_enabled:
                                processed_project_answer = strip_asterisks_from_projects(answer) if has_project else None
                                processed_code_answer = wrap_code_file_links(code_answer, code_citations) if (has_code and code_citations) else code_answer
                                
                                if has_code:
                                    processed_code_answer = wrap_external_links(processed_code_answer)
                                
                                processed_coop_answer = wrap_coop_file_links(coop_answer, coop_citations) if (has_coop and coop_citations) else coop_answer
                                
                                supabase_logger = get_supabase_logger()
                                if supabase_logger.enabled:
                                    user_identifier = request.user_identifier or f"{os.getenv('USERNAME', 'unknown')}@{os.getenv('COMPUTERNAME', 'unknown')}"
                                    parts = []
                                    if has_project:
                                        parts.append(answer)
                                    if has_code:
                                        parts.append(f"--- Code References ---\n\n{code_answer}")
                                    if has_coop:
                                        parts.append(f"--- Training Manual References ---\n\n{coop_answer}")
                                    combined_for_logging = "\n\n".join(parts)
                                    
                                    image_url = None
                                    if images_to_process and len(images_to_process) > 0:
                                        image_url = supabase_logger.upload_image(images_to_process[0], message_id, "image/png")
                                    
                                    query_data = {
                                        "message_id": message_id,
                                        "session_id": request.session_id,
                                        "user_query": request.message,
                                        "rag_response": combined_for_logging,
                                        "route": final_state.get("data_route"),
                                        "citations_count": len(project_citations) + len(code_citations) + len(coop_citations),
                                        "latency_ms": round(latency_ms, 2),
                                        "user_identifier": user_identifier,
                                        "image_url": image_url
                                    }
                                    supabase_logger.log_user_query(query_data)
                                
                                response_data = {
                                    'reply': processed_project_answer or processed_code_answer or processed_coop_answer or "No answer generated.",
                                    'session_id': request.session_id,
                                    'timestamp': datetime.now().isoformat(),
                                    'latency_ms': round(latency_ms, 2),
                                    'citations': len(project_citations) + len(code_citations) + len(coop_citations),
                                    'route': final_state.get("data_route"),
                                    'message_id': message_id,
                                    'project_answer': processed_project_answer,
                                    'code_answer': processed_code_answer,
                                    'coop_answer': processed_coop_answer,
                                    'project_citations': len(project_citations) if has_project else None,
                                    'code_citations': len(code_citations) if has_code else None,
                                    'coop_citations': len(coop_citations) if has_coop else None,
                                    'image_similarity_results': image_similarity_results if image_similarity_results else [],
                                    'follow_up_questions': follow_up_questions if follow_up_questions else None,
                                    'follow_up_suggestions': follow_up_suggestions if follow_up_suggestions else None
                                }
                            else:
                                if code_answer and code_answer.strip():
                                    combined_answer = code_answer
                                    total_citations = len(code_citations)
                                elif coop_answer and coop_answer.strip():
                                    combined_answer = coop_answer
                                    total_citations = len(coop_citations)
                                else:
                                    combined_answer = answer
                                    total_citations = len(project_citations)
                                
                                combined_answer = strip_asterisks_from_projects(combined_answer)
                                if code_citations:
                                    combined_answer = wrap_code_file_links(combined_answer, code_citations)
                                if coop_citations:
                                    combined_answer = wrap_code_file_links(combined_answer, coop_citations)
                                if code_answer and code_answer.strip():
                                    combined_answer = wrap_external_links(combined_answer)
                                
                                supabase_logger = get_supabase_logger()
                                if supabase_logger.enabled:
                                    user_identifier = request.user_identifier or f"{os.getenv('USERNAME', 'unknown')}@{os.getenv('COMPUTERNAME', 'unknown')}"
                                    image_url = None
                                    if images_to_process and len(images_to_process) > 0:
                                        image_url = supabase_logger.upload_image(images_to_process[0], message_id, "image/png")
                                    query_data = {
                                        "message_id": message_id,
                                        "session_id": request.session_id,
                                        "user_query": request.message,
                                        "rag_response": combined_answer,
                                        "route": final_state.get("data_route"),
                                        "citations_count": total_citations,
                                        "latency_ms": round(latency_ms, 2),
                                        "user_identifier": user_identifier,
                                        "image_url": image_url
                                    }
                                    supabase_logger.log_user_query(query_data)
                                
                                response_data = {
                                    'reply': combined_answer,
                                    'session_id': request.session_id,
                                    'timestamp': datetime.now().isoformat(),
                                    'latency_ms': round(latency_ms, 2),
                                    'citations': total_citations,
                                    'route': final_state.get("data_route"),
                                    'message_id': message_id,
                                    'image_similarity_results': image_similarity_results if image_similarity_results else [],
                                    'follow_up_questions': follow_up_questions if follow_up_questions else None,
                                    'follow_up_suggestions': follow_up_suggestions if follow_up_suggestions else None
                                }
                        
                            if image_similarity_results:
                                logger.info(f"🖼️ Sending {len(image_similarity_results)} image similarity results to frontend")
                                for i, img in enumerate(image_similarity_results[:3]):
                                    logger.info(f"🖼️   Image {i+1}: project={img.get('project_key')}, page={img.get('page_number')}, url={img.get('image_url', 'MISSING')[:50]}...")
                            else:
                                logger.info(f"🖼️ No image similarity results to send (image_similarity_results is empty or None)")
                            
                            yield f"data: {json.dumps({'type': 'complete', 'result': response_data})}\n\n"
                            logger.info(f"✅ Streaming completed in {latency_ms:.2f}ms [ID: {message_id}]")
                        else:
                            logger.debug("⏭️  Skipping completion code - no answer in state yet (waiting for answer node)")
            except GraphInterrupt as interrupt:
                # CRITICAL: Interrupt detected - pause execution and wait for human input
                # Extract interrupt payload from the exception
                interrupt_value = interrupt.value if hasattr(interrupt, 'value') else None
                interrupt_id = interrupt.id if hasattr(interrupt, 'id') else None
                
                logger.info(f"⏸️  INTERRUPT DETECTED: type={interrupt_value.get('type') if isinstance(interrupt_value, dict) else 'unknown'}, id={interrupt_id}")
                
                # Send interrupt event to frontend
                interrupt_data = {
                    "type": "interrupt",
                    "interrupt_id": interrupt_id,
                    "interrupt_type": interrupt_value.get("type") if isinstance(interrupt_value, dict) else "unknown",
                    "question": interrupt_value.get("question") if isinstance(interrupt_value, dict) else "",
                    "codes": interrupt_value.get("codes") if isinstance(interrupt_value, dict) else [],
                    "code_count": interrupt_value.get("code_count") if isinstance(interrupt_value, dict) else 0,
                    "chunk_count": interrupt_value.get("chunk_count") if isinstance(interrupt_value, dict) else 0,
                    "available_codes": interrupt_value.get("available_codes") if isinstance(interrupt_value, dict) else [],
                    "previously_retrieved": interrupt_value.get("previously_retrieved") if isinstance(interrupt_value, dict) else [],
                    "session_id": request.session_id,
                    "thread_id": request.session_id  # Same as session_id for resume
                }
                
                yield f"data: {json.dumps(interrupt_data)}\n\n"
                logger.info(f"📤 Sent interrupt event to frontend: {interrupt_data.get('interrupt_type')}")
                return  # Stop streaming - wait for resume
            
        except Exception as e:
            logger.error(f"❌ Streaming error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            return
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "Access-Control-Allow-Origin": "*",  # CORS for streaming
            "X-Content-Type-Options": "nosniff",  # Prevent MIME sniffing
        }
    )


# Additional endpoint for compatibility with different response formats
@app.post("/chat/resume")
async def chat_resume(request: Dict[str, Any]):
    """
    Resume graph execution after an interrupt.
    
    Request body:
    {
        "session_id": "thread_id",
        "response": "approved" | "rejected" | ["code1", "code2", ...]  # List of selected codes if rejected
    }
    """
    try:
        session_id = request.get("session_id")
        user_response = request.get("response")
        
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id is required")
        if user_response is None:
            raise HTTPException(status_code=400, detail="response is required")
        
        logger.info(f"🔄 Resuming graph for session_id={session_id} with response={user_response}")
        
        # Import graph
        from main import graph
        
        # Create config with same thread_id
        config = {
            "configurable": {"thread_id": session_id}
        }
        
        # Resume with Command
        # The response value becomes the return value of interrupt() in the node
        from langgraph.types import Command
        
        # Start streaming the resumed execution
        async def generate_resume_stream():
            import time  # Import time inside function to ensure it's in scope
            final_state = None
            messages_received = 0
            
            try:
                async for stream_item in graph.astream(
                    Command(resume=user_response),
                    config=config,
                    stream_mode=["updates", "custom", "messages"],
                    durability=os.getenv("CHECKPOINTER_DURABILITY", "exit").lower(),
                    subgraphs=True  # CRITICAL: Include outputs from subgraphs (e.g., db_retrieval subgraph) in stream
                ):
                    # Handle different stream formats (with/without subgraphs)
                    # When subgraphs=True with multiple stream modes, format is: (namespace, stream_mode, chunk)
                    # When subgraphs=False or single mode, format is: (stream_mode, chunk)
                    if isinstance(stream_item, tuple) and len(stream_item) == 3:
                        namespace, stream_mode, chunk = stream_item
                    elif isinstance(stream_item, tuple) and len(stream_item) == 2:
                        stream_mode, chunk = stream_item
                    else:
                        logger.warning(f"⚠️ Resume: Unexpected stream format: {type(stream_item)}")
                        continue
                    # Forward all stream events to frontend (same as chat/stream)
                    if stream_mode == "messages":
                        messages_received += 1
                        if isinstance(chunk, tuple) and len(chunk) >= 2:
                            message_chunk = chunk[0]
                            metadata = chunk[1] if len(chunk) > 1 else {}
                            
                            # Get the content from the message chunk
                            if hasattr(message_chunk, 'content') and message_chunk.content:
                                # When resuming, stream all tokens (answer node filtering may not work correctly on resume)
                                # The answer node should be the only one generating tokens after resume anyway
                                node_name = metadata.get('langgraph_node', 'unknown') if isinstance(metadata, dict) else 'unknown'
                                logger.debug(f"💬 Resume: Streaming token from node '{node_name}' ({len(message_chunk.content)} chars)")
                                yield f"data: {json.dumps({'type': 'token', 'content': message_chunk.content, 'timestamp': time.time()})}\n\n"
                    elif stream_mode == "custom":
                        if isinstance(chunk, dict):
                            if chunk.get("type") == "thinking":
                                yield f"data: {json.dumps({'type': 'thinking', 'message': chunk.get('message', ''), 'node': chunk.get('node', 'unknown'), 'timestamp': time.time()})}\n\n"
                    elif stream_mode == "updates":
                        # Track final state and break after router_dispatcher completes
                        for node_key, state_updates in chunk.items():
                            # CRITICAL: Handle __interrupt__ node FIRST - this is how LangGraph signals interrupts in astream mode
                            # When using .astream(), interrupts appear as __interrupt__ node output, not as exceptions
                            # This is especially important for the second interrupt (code selection after rejection)
                            
                            # Handle subgraph nodes: node_key can be a tuple like ('db_retrieval:thread_id', '__interrupt__')
                            if isinstance(node_key, tuple):
                                node_name = node_key[-1] if len(node_key) > 0 else 'unknown'
                            else:
                                node_name = node_key
                            
                            if node_name == "__interrupt__":
                                logger.info("⏸️  Resume: Second interrupt detected (code selection after rejection)")
                                logger.info(f"📋 Interrupt node_key={node_key}, state_updates type={type(state_updates)}")
                                
                                # Extract interrupt information directly from state_updates
                                # In astream mode, state_updates for __interrupt__ is a tuple containing an Interrupt object
                                try:
                                    interrupt_value = None
                                    interrupt_id = None
                                    
                                    # state_updates is a tuple: (Interrupt(value={...}, id=...), ...)
                                    if isinstance(state_updates, tuple) and len(state_updates) > 0:
                                        interrupt_obj = state_updates[0]  # Get first Interrupt object
                                        if hasattr(interrupt_obj, 'value'):
                                            interrupt_value = interrupt_obj.value
                                        if hasattr(interrupt_obj, 'id'):
                                            interrupt_id = interrupt_obj.id
                                        
                                        logger.info(f"⏸️  Resume: INTERRUPT EXTRACTED: type={interrupt_value.get('type') if isinstance(interrupt_value, dict) else 'unknown'}, id={interrupt_id}")
                                    
                                    # Fallback: check if it's a dict (shouldn't happen, but be safe)
                                    elif isinstance(state_updates, dict):
                                        if "__interrupt__" in state_updates:
                                            interrupt_list = state_updates.get("__interrupt__", [])
                                            if interrupt_list and len(interrupt_list) > 0:
                                                interrupt_obj = interrupt_list[0]
                                                if isinstance(interrupt_obj, dict):
                                                    interrupt_value = interrupt_obj.get("value")
                                                    interrupt_id = interrupt_obj.get("id")
                                                elif hasattr(interrupt_obj, 'value'):
                                                    interrupt_value = interrupt_obj.value
                                                    interrupt_id = getattr(interrupt_obj, 'id', None)
                                    
                                    if interrupt_value is None:
                                        logger.error("❌ Resume: Could not extract interrupt information from state_updates")
                                        interrupt_data = {
                                            "type": "interrupt",
                                            "interrupt_id": None,
                                            "interrupt_type": "unknown",
                                            "question": "Code selection required",
                                            "codes": [],
                                            "code_count": 0,
                                            "chunk_count": 0,
                                            "available_codes": [],
                                            "previously_retrieved": [],
                                            "session_id": session_id,
                                            "thread_id": session_id
                                        }
                                    else:
                                        # Send interrupt event to frontend with extracted data
                                        interrupt_data = {
                                            "type": "interrupt",
                                            "interrupt_id": interrupt_id,
                                            "interrupt_type": interrupt_value.get("type") if isinstance(interrupt_value, dict) else "unknown",
                                            "question": interrupt_value.get("question") if isinstance(interrupt_value, dict) else "",
                                            "codes": interrupt_value.get("codes") if isinstance(interrupt_value, dict) else [],
                                            "code_count": interrupt_value.get("code_count") if isinstance(interrupt_value, dict) else 0,
                                            "chunk_count": interrupt_value.get("chunk_count") if isinstance(interrupt_value, dict) else 0,
                                            "available_codes": interrupt_value.get("available_codes") or [] if isinstance(interrupt_value, dict) else [],
                                            "previously_retrieved": interrupt_value.get("previously_retrieved") if isinstance(interrupt_value, dict) else [],
                                            "session_id": session_id,
                                            "thread_id": session_id
                                        }
                                    
                                    yield f"data: {json.dumps(interrupt_data)}\n\n"
                                    logger.info(f"📤 Resume: Sent second interrupt event to frontend: {interrupt_data.get('interrupt_type')}")
                                    codes_list = interrupt_data.get('codes') or []
                                    available_codes_list = interrupt_data.get('available_codes') or []
                                    logger.info(f"📋 Resume: Interrupt payload: codes={len(codes_list)}, available_codes={len(available_codes_list)}")
                                    
                                    # Return early - don't process further until user responds
                                    return
                                    
                                except Exception as e:
                                    logger.error(f"❌ Resume: Error extracting interrupt information: {e}")
                                    # Still send a basic interrupt event
                                    interrupt_data = {
                                        "type": "interrupt",
                                        "interrupt_id": None,
                                        "interrupt_type": "code_selection",
                                        "question": "Please select which building codes you'd like me to reference:",
                                        "codes": [],
                                        "code_count": 0,
                                        "chunk_count": 0,
                                        "available_codes": [],
                                        "previously_retrieved": [],
                                        "session_id": session_id,
                                        "thread_id": session_id
                                    }
                                    yield f"data: {json.dumps(interrupt_data)}\n\n"
                                    return
                            
                            # Skip non-dict state_updates (like interrupt tuples)
                            if not isinstance(state_updates, dict):
                                continue
                            
                            # Update final_state with latest state
                            if final_state is None:
                                final_state = {}
                            final_state.update(state_updates)
                            
                            # Break after router_dispatcher completes (same as main stream)
                            # Check final_state (accumulated) not just state_updates (current chunk)
                            # Also check for answer in various forms
                            has_result = (
                                final_state.get("db_retrieval_result") or
                                final_state.get("db_retrieval_code_answer") or
                                final_state.get("db_retrieval_coop_answer") or
                                final_state.get("final_answer") or
                                final_state.get("code_answer") or
                                final_state.get("coop_answer")
                            )
                            
                            if node_key == "router_dispatcher" and has_result:
                                logger.info(f"✅ Resume: Breaking after router_dispatcher - subgraph execution complete")
                                logger.info(f"📊 Resume: Answer present in final_state")
                                break
                
                # Extract final answer and send completion (same logic as main stream)
                if final_state:
                    has_answer = bool(
                        final_state.get("db_retrieval_result") or 
                        final_state.get("final_answer") or 
                        final_state.get("answer") or
                        final_state.get("db_retrieval_code_answer") or 
                        final_state.get("code_answer") or
                        final_state.get("db_retrieval_coop_answer") or 
                        final_state.get("coop_answer")
                    )
                    
                    logger.info(f"📊 Resume: Final state check - messages_received={messages_received}, has_answer={has_answer}")
                    logger.info(f"📊 Resume: Final state keys: {list(final_state.keys())[:20]}")
                    
                    if has_answer:
                        logger.info(f"✅ Resume: Answer found in final state, sending completion")
                        
                        # Extract final answer
                        answer = final_state.get("db_retrieval_result") or final_state.get("final_answer") or final_state.get("answer")
                        code_answer = final_state.get("db_retrieval_code_answer") or final_state.get("code_answer")
                        coop_answer = final_state.get("db_retrieval_coop_answer") or final_state.get("coop_answer")
                        
                        if not answer or answer.strip() == "":
                            answer = code_answer or coop_answer or "No answer generated."
                        
                        # Store answer_text for fallback streaming if needed
                        answer_text = answer or code_answer or coop_answer or ""
                        
                        code_citations = final_state.get("db_retrieval_code_citations") or final_state.get("code_citations", [])
                        coop_citations = final_state.get("db_retrieval_coop_citations") or final_state.get("coop_citations", [])
                        project_citations = final_state.get("db_retrieval_citations") or final_state.get("answer_citations", [])
                        image_similarity_results = final_state.get("db_retrieval_image_similarity_results") or final_state.get("image_similarity_results", [])
                        follow_up_questions = final_state.get("db_retrieval_follow_up_questions") or final_state.get("follow_up_questions", [])
                        follow_up_suggestions = final_state.get("db_retrieval_follow_up_suggestions") or final_state.get("follow_up_suggestions", [])
                        
                        has_project = bool(answer and answer.strip())
                        has_code = bool(code_answer and code_answer.strip())
                        has_coop = bool(coop_answer and coop_answer.strip())
                        enabled_count = sum([has_project, has_code, has_coop])
                        multiple_enabled = enabled_count > 1
                        
                        # Use helper functions (defined at module level)
                        if multiple_enabled:
                            processed_project_answer = strip_asterisks_from_projects(answer) if has_project else None
                            processed_code_answer = wrap_code_file_links(code_answer, code_citations) if (has_code and code_citations) else code_answer
                            
                            if has_code:
                                processed_code_answer = wrap_external_links(processed_code_answer)
                            
                            processed_coop_answer = wrap_coop_file_links(coop_answer, coop_citations) if (has_coop and coop_citations) else coop_answer
                            
                            response_data = {
                                'reply': processed_project_answer or processed_code_answer or processed_coop_answer or "No answer generated.",
                                'session_id': session_id,
                                'timestamp': datetime.now().isoformat(),
                                'citations': len(project_citations) + len(code_citations) + len(coop_citations),
                                'route': final_state.get("data_route"),
                                'project_answer': processed_project_answer,
                                'code_answer': processed_code_answer,
                                'coop_answer': processed_coop_answer,
                                'project_citations': len(project_citations) if has_project else None,
                                'code_citations': len(code_citations) if has_code else None,
                                'coop_citations': len(coop_citations) if has_coop else None,
                                'image_similarity_results': image_similarity_results if image_similarity_results else [],
                                'follow_up_questions': follow_up_questions if follow_up_questions else None,
                                'follow_up_suggestions': follow_up_suggestions if follow_up_suggestions else None
                            }
                        else:
                            if code_answer and code_answer.strip():
                                combined_answer = code_answer
                                total_citations = len(code_citations)
                            elif coop_answer and coop_answer.strip():
                                combined_answer = coop_answer
                                total_citations = len(coop_citations)
                            else:
                                combined_answer = answer
                                total_citations = len(project_citations)
                            
                            combined_answer = strip_asterisks_from_projects(combined_answer)
                            if code_citations:
                                combined_answer = wrap_code_file_links(combined_answer, code_citations)
                            if coop_citations:
                                combined_answer = wrap_code_file_links(combined_answer, coop_citations)
                            if code_answer and code_answer.strip():
                                combined_answer = wrap_external_links(combined_answer)
                            
                            response_data = {
                                'reply': combined_answer,
                                'session_id': session_id,
                                'timestamp': datetime.now().isoformat(),
                                'citations': total_citations,
                                'route': final_state.get("data_route"),
                                'image_similarity_results': image_similarity_results if image_similarity_results else [],
                                'follow_up_questions': follow_up_questions if follow_up_questions else None,
                                'follow_up_suggestions': follow_up_suggestions if follow_up_suggestions else None
                            }
                        
                        # Only use fallback if we truly got no tokens AND answer exists
                        # This should be rare - normally tokens should stream from answer node
                        # NOTE: This fallback should NOT be needed if tokens are streaming correctly
                        # If this triggers, it means tokens aren't being captured from the answer node
                        if messages_received == 0 and answer_text:
                            logger.warning("⚠️ Resume: No tokens received during streaming, but answer exists in state")
                            logger.info("📤 Resume: Sending answer content as token chunks to frontend")
                            # Send answer in chunks to simulate streaming (no await in generator)
                            chunk_size = 50  # Smaller chunks for better streaming effect
                            for i in range(0, len(answer_text), chunk_size):
                                chunk = answer_text[i:i + chunk_size]
                                yield f"data: {json.dumps({'type': 'token', 'content': chunk, 'timestamp': time.time()})}\n\n"
                                messages_received += 1
                        
                        # Send completion with result
                        yield f"data: {json.dumps({'type': 'complete', 'result': response_data})}\n\n"
                        logger.info(f"✅ Resume streaming completed - {messages_received} token events received")
                    else:
                        logger.warning("⚠️ Resume: No answer found in final state")
                        yield f"data: {json.dumps({'type': 'complete', 'message': 'Resume completed but no answer found'})}\n\n"
                else:
                    logger.warning("⚠️ Resume: No final state captured")
                    yield f"data: {json.dumps({'type': 'complete', 'message': 'Resume completed'})}\n\n"
            except GraphInterrupt as interrupt:
                # Another interrupt occurred (e.g., code selection after rejection)
                # This is expected when user rejects initial codes - second interrupt for code selection
                interrupt_value = interrupt.value if hasattr(interrupt, 'value') else None
                interrupt_id = interrupt.id if hasattr(interrupt, 'id') else None
                
                logger.info(f"⏸️  Resume: Second interrupt detected (code selection after rejection)")
                logger.info(f"📋 Interrupt type: {interrupt_value.get('type') if isinstance(interrupt_value, dict) else 'unknown'}")
                
                interrupt_data = {
                    "type": "interrupt",
                    "interrupt_id": interrupt_id,
                    "interrupt_type": interrupt_value.get("type") if isinstance(interrupt_value, dict) else "unknown",
                    "question": interrupt_value.get("question") if isinstance(interrupt_value, dict) else "",
                    "codes": interrupt_value.get("codes") if isinstance(interrupt_value, dict) else [],
                    "code_count": interrupt_value.get("code_count") if isinstance(interrupt_value, dict) else 0,
                    "chunk_count": interrupt_value.get("chunk_count") if isinstance(interrupt_value, dict) else 0,
                    "available_codes": interrupt_value.get("available_codes") if isinstance(interrupt_value, dict) else [],
                    "previously_retrieved": interrupt_value.get("previously_retrieved") if isinstance(interrupt_value, dict) else [],
                    "session_id": session_id,
                    "thread_id": session_id
                }
                
                yield f"data: {json.dumps(interrupt_data)}\n\n"
                logger.info(f"📤 Resume: Sent second interrupt event to frontend (code selection)")
                return  # Stop streaming - wait for second resume with selected codes
            except Exception as e:
                logger.error(f"❌ Resume error: {e}")
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        
        return StreamingResponse(
            generate_resume_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "Access-Control-Allow-Origin": "*"
            }
        )
        
    except Exception as e:
        logger.error(f"❌ Resume endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/legacy")
async def chat_legacy(request: ChatRequest):
    """
    Legacy endpoint that returns the exact format the chatbutton originally expected.
    Returns answer field instead of reply for backward compatibility.
    """
    response = await chat_handler(request)
    return {
        "answer": response.reply,
        "session_id": response.session_id,
        "citations": response.citations,
        "route": response.route,
        "data_sources": response.data_sources
    }

# IFC File Upload endpoint
@app.post("/chat/upload-ifc")
async def upload_ifc_to_speckle(
    file: UploadFile = File(...),
    project_id: Optional[str] = Form(None),
    model_name: str = Form("main")
):
    """
    Upload IFC file to Speckle server.
    Creates new project if project_id not provided.
    Saves metadata to database.
    
    Returns:
        {
            "success": bool,
            "speckle_project_id": str,
            "speckle_model_name": str,
            "message": str
        }
    """
    try:
        logger.info(f"📤 IFC upload request: {file.filename}, project_id={project_id}, model={model_name}")
        
        # Get Speckle credentials from environment
        speckle_url = os.getenv("SPECKLE_URL") or os.getenv("SPECKLE_SERVER_URL") or "https://app.speckle.systems"
        speckle_token = os.getenv("SPECKLE_TOKEN")
        
        if not speckle_token:
            raise HTTPException(status_code=500, detail="Speckle token not configured")
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        file_type = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
        
        logger.info(f"📦 File details: {file.filename}, size={file_size} bytes, type={file_type}")
        
        # 1. CREATE PROJECT IN SPECKLE (if not provided)
        speckle_project_id = project_id
        if not speckle_project_id:
            project_name = file.filename.replace('.ifc', '').replace('.IFC', '') or f"IFC Upload {datetime.now().strftime('%Y-%m-%d')}"
            
            logger.info(f"🏗️ Creating Speckle project: {project_name}")
            
            # Call Speckle GraphQL to create project
            async with httpx.AsyncClient(timeout=30.0) as client:
                create_project_response = await client.post(
                    f"{speckle_url}/graphql",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {speckle_token}"
                    },
                    json={
                        "query": """
                            mutation CreateProject($input: ProjectCreateInput!) {
                                projectMutations {
                                    create(input: $input) {
                                        id
                                        name
                                    }
                                }
                            }
                        """,
                        "variables": {
                            "input": {
                                "name": project_name,
                                "description": f"Uploaded from chat: {file.filename}",
                                "visibility": "PRIVATE"
                            }
                        }
                    }
                )
                
                if create_project_response.status_code != 200:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to create Speckle project: {create_project_response.text}"
                    )
                
                result = create_project_response.json()
                if "errors" in result:
                    raise HTTPException(
                        status_code=500,
                        detail=f"GraphQL error: {result['errors']}"
                    )
                
                speckle_project_id = result["data"]["projectMutations"]["create"]["id"]
                project_name_created = result["data"]["projectMutations"]["create"]["name"]
                logger.info(f"✅ Created Speckle project: {speckle_project_id} ({project_name_created})")
        
        # 2. SAVE TO YOUR DATABASE (if you have a database setup)
        # TODO: Add your database save logic here
        # Example:
        # file_record = {
        #     "filename": file.filename,
        #     "file_type": file_type,
        #     "file_size": file_size,
        #     "speckle_project_id": speckle_project_id,
        #     "speckle_model_name": model_name,
        #     "upload_date": datetime.now().isoformat(),
        #     "status": "uploading"
        # }
        # await your_db.file_uploads.insert(file_record)
        
        # 3. UPLOAD TO SPECKLE SERVER using autodetect endpoint
        logger.info(f"⬆️ Uploading file to Speckle: project={speckle_project_id}, model={model_name}")
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            # Create multipart form data
            files = {
                "file": (file.filename, file_content, file.content_type or "application/octet-stream")
            }
            
            upload_response = await client.post(
                f"{speckle_url}/api/file/autodetect/{speckle_project_id}/{model_name}",
                headers={
                    "Authorization": f"Bearer {speckle_token}"
                },
                files=files
            )
            
            if upload_response.status_code != 201:
                error_text = upload_response.text
                logger.error(f"❌ Speckle upload failed: {upload_response.status_code} - {error_text}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Speckle upload failed: {error_text}"
                )
            
            upload_result = upload_response.json()
            logger.info(f"✅ File uploaded to Speckle successfully: {upload_result}")
        
        # 4. UPDATE YOUR DATABASE (if you have one)
        # TODO: Update status to "completed"
        # await your_db.file_uploads.update(
        #     {"status": "completed", "speckle_blob_id": upload_result.get("blobId")}
        # )
        
        return {
            "success": True,
            "speckle_project_id": speckle_project_id,
            "speckle_model_name": model_name,
            "message": f"File '{file.filename}' uploaded successfully. Speckle is processing it and it will appear in your project shortly."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ IFC upload error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


# Feedback endpoint
@app.post("/feedback")
async def feedback_handler(request: FeedbackRequest):
    """
    Handle feedback submissions from the Electron app.
    Saves feedback locally to AppData and syncs to GitHub.

    Expected request format:
    {
        "message_id": "msg_12345_abcdef",
        "rating": "positive",
        "comment": "Great answer!",
        "user_question": "What are...",
        "response": "The answer is...",
        "timestamp": "2025-10-05T12:00:00Z"
    }
    """
    try:
        logger.info(f"Received feedback: {request.rating} for message {request.message_id}")

        # Get feedback logger instance
        feedback_logger = get_feedback_logger()

        # Prepare feedback data
        feedback_data = {
            "message_id": request.message_id,
            "rating": request.rating,
            "comment": request.comment or "",
            "user_question": request.user_question,
            "response": request.response,
            "timestamp": request.timestamp
        }

        # Log feedback (saves locally + pushes to GitHub)
        success = feedback_logger.log_feedback(feedback_data)

        # Also log to Supabase
        supabase_logger = get_supabase_logger()
        if supabase_logger.enabled:
            user_identifier = f"{os.getenv('USERNAME', 'unknown')}@{os.getenv('COMPUTERNAME', 'unknown')}"
            supabase_feedback_data = {
                "message_id": request.message_id,
                "rating": request.rating,
                "comment": request.comment or "",
                "user_identifier": user_identifier
            }
            supabase_success = supabase_logger.log_feedback(supabase_feedback_data)
            
            if supabase_success:
                logger.info(f"✓ Feedback also logged to Supabase: {request.message_id}")
            else:
                logger.warning(f"⚠ Failed to log feedback to Supabase: {request.message_id}")

        if success:
            return {
                "status": "success",
                "message": "Feedback received and saved",
                "message_id": request.message_id
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to save feedback")

    except Exception as e:
        logger.error(f"Error processing feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Feedback stats endpoint (for debugging/admin)
@app.get("/feedback/stats")
async def feedback_stats():
    """Get feedback statistics"""
    try:
        feedback_logger = get_feedback_logger()
        stats = feedback_logger.get_feedback_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting feedback stats: {e}")
        return {"error": str(e)}

# Database health endpoint
@app.get("/db/health")
async def database_health():
    """Check database connection status"""
    try:
        db_status = test_database_connection()
        return db_status
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {"connected": False, "error": str(e)}

# Debug routing endpoint
@app.get("/debug/routing")
async def debug_routing():
    """Debug endpoint to show current routing configuration"""
    try:
        # Import the constants from config
        from config.settings import (
            MAX_SMART_RETRIEVAL_DOCS, MAX_LARGE_RETRIEVAL_DOCS, 
            MAX_HYBRID_RETRIEVAL_DOCS, SUPA_SMART_TABLE, SUPA_LARGE_TABLE
        )
        from nodes.DBRetrieval.KGdb.supabase_client import vs_smart, vs_large
        
        return {
            "supabase_configured": bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_ANON_KEY")),
            "smart_table": SUPA_SMART_TABLE,
            "large_table": SUPA_LARGE_TABLE,
            "vs_smart_exists": vs_smart is not None,
            "vs_large_exists": vs_large is not None,
            "chunk_limits": {
                "smart": MAX_SMART_RETRIEVAL_DOCS,
                "large": MAX_LARGE_RETRIEVAL_DOCS,
                "hybrid": MAX_HYBRID_RETRIEVAL_DOCS
            }
        }
    except Exception as e:
        logger.error(f"Debug routing check failed: {e}")
        return {"error": str(e)}

# Enhanced logging endpoints
@app.get("/logs/enhanced")
async def get_enhanced_logs(
    level: Optional[str] = None,
    logger: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 100,
    format: str = "json"
):
    """Enhanced logs with function tracking and chunk flow"""
    logs = enhanced_log_capture.get_logs(level_filter=level, logger_filter=logger, limit=limit)
    
    if category:
        logs = [log for log in logs if log.get('extra_data', {}).get('category') == category]
    
    if format == "html":
        return await render_enhanced_log_html(logs, level, logger, category, limit)
    
    return {
        "logs": logs,
        "function_calls": enhanced_log_capture.get_function_calls(20),
        "chunk_flow": enhanced_log_capture.get_chunk_flow(50),
        "count": len(logs)
    }

@app.post("/logs/enhanced/clear")
async def clear_enhanced_logs():
    """Clear all enhanced logs and tracking data"""
    enhanced_log_capture.clear_all()
    return {"message": "All logs and tracking data cleared successfully"}

@app.get("/logs/enhanced/stats")
async def enhanced_log_stats():
    """Get comprehensive statistics"""
    return get_enhanced_log_stats()

# Supabase Statistics Endpoints
@app.get("/stats/interactions")
async def get_interaction_stats(user_identifier: str = None, days: int = 30):
    """Get comprehensive interaction statistics from Supabase"""
    supabase_logger = get_supabase_logger()
    if not supabase_logger.enabled:
        return {"error": "Supabase logging not enabled"}
    
    stats = supabase_logger.get_interaction_stats(user_identifier, days)
    return stats

@app.get("/stats/user/{user_identifier}")
async def get_user_summary(user_identifier: str, days: int = 30):
    """Get comprehensive summary for a specific user"""
    supabase_logger = get_supabase_logger()
    if not supabase_logger.enabled:
        return {"error": "Supabase logging not enabled"}
    
    summary = supabase_logger.get_user_summary(user_identifier, days)
    return summary

@app.get("/stats/recent")
async def get_recent_interactions(limit: int = 50, user_identifier: str = None):
    """Get recent interactions"""
    supabase_logger = get_supabase_logger()
    if not supabase_logger.enabled:
        return {"error": "Supabase logging not enabled"}
    
    interactions = supabase_logger.get_recent_interactions(limit, user_identifier)
    return {"interactions": interactions, "count": len(interactions)}

# Instructions endpoint
@app.get("/instructions")
async def get_instructions():
    """
    Return usage instructions for the frontend.
    Content is stored in instructions.py and can be updated without rebuilding the executable.
    """
    return {
        "content": INSTRUCTIONS_CONTENT,
        "format": "markdown"
    }

# ============================================================
# RENDERER AUTO-UPDATE ENDPOINTS
# ============================================================
# These endpoints serve the renderer files for the Electron app auto-update system.
# When you want to push an update, edit the files in Backend/renderer-update/
# and bump the version in version.json.

RENDERER_UPDATE_DIR = os.path.join(os.path.dirname(__file__), "renderer-update")

@app.get("/renderer-update/version.json")
async def get_renderer_version():
    """Return the current version info for auto-update check."""
    version_file = os.path.join(RENDERER_UPDATE_DIR, "version.json")
    if not os.path.exists(version_file):
        raise HTTPException(status_code=404, detail="version.json not found")
    return FileResponse(version_file, media_type="application/json")

@app.get("/renderer-update/{filename}")
async def get_renderer_file(filename: str):
    """
    Serve renderer files for auto-update.
    Allowed files: index.html, renderer.js, style.css, PURPLE LIGHT.png
    """
    # Security: only allow specific files
    allowed_files = ["index.html", "renderer.js", "style.css", "PURPLE LIGHT.png"]
    if filename not in allowed_files:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_path = os.path.join(RENDERER_UPDATE_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"{filename} not found")
    
    # Determine media type
    media_types = {
        "index.html": "text/html",
        "renderer.js": "application/javascript",
        "style.css": "text/css",
        "PURPLE LIGHT.png": "image/png"
    }
    media_type = media_types.get(filename, "application/octet-stream")
    
    return FileResponse(file_path, media_type=media_type)


# Test endpoint to verify which backend is running
@app.get("/test/backend-version")
async def test_backend_version():
    """Test endpoint to verify we're using the new Backend/Backend code"""
    from config.settings import SUPA_SMART_TABLE, SUPA_LARGE_TABLE
    return {
        "backend": "Backend/Backend (NEW)",
        "smart_table": SUPA_SMART_TABLE,
        "large_table": SUPA_LARGE_TABLE,
        "message": "This is the NEW modular backend"
    }

# Root endpoint
@app.get("/")
@app.head("/")
async def root():
    return {
        "message": "Mantle RAG API Server",
        "version": "1.0.0",
        "backend": "Backend/Backend (NEW)",
        "endpoints": {
            "chat": "/chat",
            "health": "/health",
            "db_health": "/db/health",
            "test_backend": "/test/backend-version",
            "instructions": "/instructions",
            "logs_enhanced": "/logs/enhanced",
            "logs_stats": "/logs/enhanced/stats",
            "stats_interactions": "/stats/interactions",
            "stats_user": "/stats/user/{user_identifier}",
            "stats_recent": "/stats/recent",
            "graph_cypher": "/graph/cypher (DEBUG only)",
            "graph_schema": "/graph/schema (DEBUG only)"
        }
    }

# ============================================================
# KUZU GRAPH DATABASE ENDPOINTS (DEBUG ONLY)
# ============================================================
@app.post("/graph/cypher", response_model=CypherResponse)
async def execute_cypher(request: CypherRequest):
    """Execute a Cypher query against the Kuzu graph database (Debug mode only)"""
    if not DEBUG_MODE:
        raise HTTPException(status_code=403, detail="Graph database access is only available in DEBUG_MODE")
    
    if get_kuzu_manager is None:
        raise HTTPException(status_code=500, detail="Kuzu manager not available")
    
    try:
        kuzu_manager = get_kuzu_manager()
        result = kuzu_manager.execute(request.query, request.params)
        return CypherResponse(**result)
    except Exception as e:
        logger.error(f"Cypher endpoint error: {e}")
        return CypherResponse(success=False, error=str(e), query=request.query)

@app.get("/graph/schema")
async def get_graph_schema():
    """Get the Kuzu graph database schema (Debug mode only)"""
    if not DEBUG_MODE:
        raise HTTPException(status_code=403, detail="Graph database access is only available in DEBUG_MODE")
    
    if get_kuzu_manager is None:
        raise HTTPException(status_code=500, detail="Kuzu manager not available")
    
    try:
        kuzu_manager = get_kuzu_manager()
        return kuzu_manager.get_schema()
    except Exception as e:
        logger.error(f"Graph schema endpoint error: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    # Check environment setup
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY environment variable not found!")
        print("\n❌ Please set OPENAI_API_KEY in your .env file before starting the server.")
        print("   Example: OPENAI_API_KEY=your_api_key_here")
        exit(1)

    # Get port from environment (for Render deployment) or default to 8000
    port = int(os.getenv("PORT", 8000))

    print("\n🚀 Starting Mantle RAG API Server...")
    print(f"   Chat endpoint: http://0.0.0.0:{port}/chat")
    print(f"   Health check: http://0.0.0.0:{port}/health")
    print(f"   Database status: http://0.0.0.0:{port}/db/health")
    print(f"   📊 Enhanced Debugger: http://0.0.0.0:{port}/logs/enhanced?format=html")
    print(f"   📈 Log Statistics: http://0.0.0.0:{port}/logs/enhanced/stats")
    if DEBUG_MODE:
        print(f"   🛠️  Kuzu Graph DB Cypher: http://0.0.0.0:{port}/graph/schema")
    print(f"\n📡 Server running on port: {port}")
    print("⚡ Ready for Electron chatbutton app!")

    # Run the server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True
    )
