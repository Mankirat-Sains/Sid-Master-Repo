#!/usr/bin/env python3
"""
FastAPI server for Mantle RAG Chat Interface
Connect the chatbutton Electron app to the rag.py backend
"""

from datetime import datetime
import logging
import re
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
from database import test_database_connection
from config.settings import PROJECT_CATEGORIES, CATEGORIES_PATH, PLANNER_PLAYBOOK, PLAYBOOK_PATH

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
def wrap_project_links(text: str) -> str:
    """
    Detect project numbers in format XX-XX-XXX (e.g., 25-08-001)
    and convert them to fully-formed HTML links.
    This is done in the backend so frontend doesn't need to rebuild executable for link changes.
    """
    # Regex pattern to match project numbers like 25-08-001
    project_number_pattern = r'\b(\d{2}-\d{2}-\d{3})\b'

    def make_folder_link(match):
        project_number = match.group(1)
        # Build the network path for the project folder
        network_path = f"\\\\WADDELLNAS\\Projects\\{project_number}"
        # HTML-escape the path for the attribute
        escaped_path = escape(network_path, quote=True)
        # HTML-escape the title attribute
        title_text = "Left-click: Open in Explorer | Right-click: Open in Harmani"
        escaped_title = escape(title_text, quote=True)
        # Generate fully-formed HTML link
        return f'<a href="#" class="folder-link" data-path="{escaped_path}" data-project="{escape(project_number, quote=True)}" title="{escaped_title}">{project_number}</a>'

    # Replace each match with fully-formed HTML link
    wrapped_text = re.sub(
        project_number_pattern,
        make_folder_link,
        text
    )

    return wrapped_text


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


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# Request/Response Models
class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    user_identifier: Optional[str] = None
    data_sources: Optional[Dict[str, bool]] = None
    image_base64: Optional[str] = None  # Single screenshot/image as base64 (backwards compatible)
    images_base64: Optional[List[str]] = None  # Multiple images as base64 array

    
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
            # Wrap project numbers with folder-link tags
            processed_project_answer = wrap_project_links(answer) if has_project else None
            
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
            
            # Wrap project numbers with folder-link tags for clickable links
            combined_answer = wrap_project_links(combined_answer)
            
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
            
            # Import graph and state
            from main import graph
            from models.rag_state import RAGState
            from dataclasses import asdict
            from thinking.intelligent_log_generator import IntelligentLogGenerator
            
            log_generator = IntelligentLogGenerator()
            
            # Determine if image similarity should be enabled
            use_image_similarity = False
            query_intent = None
            if images_to_process:
                from nodes.DBRetrieval.image_nodes import classify_image_query_intent
                intent_result = classify_image_query_intent(request.message, images_to_process[0])
                use_image_similarity = intent_result.get("use_image_similarity", False)
                query_intent = intent_result.get("intent")
            
            # Create initial state
            init_state = RAGState(
                session_id=request.session_id,
                user_query=request.message,
                query_plan=None,
                data_route=None,
                project_filter=None,
                expanded_queries=[],
                retrieved_docs=[],
                graded_docs=[],
                db_result=None,
                final_answer=None,
                answer_citations=[],
                code_answer=None,
                code_citations=[],
                coop_answer=None,
                coop_citations=[],
                answer_support_score=0.0,
                corrective_attempted=False,
                data_sources=request.data_sources,
                images_base64=images_to_process if images_to_process else None,
                use_image_similarity=use_image_similarity,
                query_intent=query_intent
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
            node_count = 0
            # Use multiple stream modes per LangGraph best practices:
            # - "updates": State updates per node with node names {node_name: state_updates}
            # - "custom": Custom events emitted from nodes (for real-time progress)
            # - "messages": LLM tokens as they're generated (for real-time answer streaming)
            async for stream_mode, chunk in graph.astream(
                asdict(init_state),
                config=config,
                stream_mode=["updates", "custom", "messages"]  # Add "messages" for token streaming
            ):
                # Handle LLM token streaming (messages mode)
                if stream_mode == "messages":
                    # chunk is a tuple: (message_chunk, metadata)
                    # message_chunk is the token or message segment from the LLM
                    # metadata contains node info with 'langgraph_node' field (per LangGraph docs)
                    try:
                        message, metadata = chunk
                        if hasattr(message, 'content') and message.content:
                            # Filter tokens by node name using 'langgraph_node' field (per LangGraph docs)
                            # https://docs.langchain.com/oss/python/langgraph/streaming#filter-by-node
                            node_name = metadata.get('langgraph_node', metadata.get('node', 'unknown')) if isinstance(metadata, dict) else 'unknown'
                            
                            # Only forward tokens from the answer node (final synthesis)
                            # Other nodes' LLM outputs should only appear in Agent Thinking
                            if node_name == "answer":
                                token_content = message.content
                                logger.debug(f"💬 Streaming token from messages mode (node '{node_name}'): {len(token_content)} chars")
                                token_data = {
                                    'type': 'token',
                                    'content': token_content,
                                    'node': node_name,
                                    'timestamp': time.time()
                                }
                                yield f"data: {json.dumps(token_data)}\n\n"
                                await asyncio.sleep(0.001)  # Minimal delay for proper streaming
                            else:
                                # Log but don't forward - these are internal reasoning, not user-facing
                                logger.debug(f"Filtered out token from node '{node_name}' (not answer node)")
                    except (ValueError, TypeError) as e:
                        # If chunk format is different, log and continue
                        logger.debug(f"Messages mode chunk format: {type(chunk)}, error: {e}")
                    continue
                
                # Handle custom events (emitted directly from nodes)
                if stream_mode == "custom":
                    logger.debug(f"📨 Custom event received: {chunk}")
                    # Emit custom event immediately to frontend
                    if isinstance(chunk, dict):
                        if chunk.get("type") == "thinking":
                            yield f"data: {json.dumps({'type': 'thinking', 'message': chunk.get('message', ''), 'node': chunk.get('node', 'unknown'), 'timestamp': time.time()})}\n\n"
                            await asyncio.sleep(0.001)
                        elif chunk.get("type") == "token":
                            # Forward token to frontend for real-time streaming
                            token_content = chunk.get('content', '')
                            token_node = chunk.get('node', 'answer')
                            logger.debug(f"💬 Streaming token from node '{token_node}': {len(token_content)} chars")
                            yield f"data: {json.dumps({'type': 'token', 'content': token_content, 'node': token_node, 'timestamp': time.time()})}\n\n"
                            await asyncio.sleep(0.001)  # Minimal delay for proper streaming
                    continue
                
                # Handle state updates (updates mode)
                if stream_mode != "updates":
                    continue
                    
                # chunk is now {node_name: state_updates_dict}
                # This gives us the node name directly as the key
                node_outputs = chunk
                logger.info(f"📦 Received node_outputs: {list(node_outputs.keys())}")
                
                for node_name, state_updates in node_outputs.items():
                    node_count += 1
                    logger.info(f"🔍 Processing node #{node_count}: '{node_name}'")
                    
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
                        thinking_log = log_generator.generate_retrieval_log(
                            query=request.message,
                            project_count=len(state_dict.get("retrieved_docs") or []),
                            code_count=len(state_dict.get("retrieved_code_docs") or []),
                            coop_count=len(state_dict.get("retrieved_coop_docs") or []),
                            projects=_extract_projects(state_dict.get("retrieved_docs") or []),
                            route=state_dict.get("data_route") or "smart",
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
                        thinking_log = log_generator.generate_synthesis_log(
                            query=request.message,
                            graded_count=len(state_dict.get("answer_citations") or []),
                            projects=_extract_projects_from_citations(state_dict.get("answer_citations") or []),
                            has_code=bool(state_dict.get("code_answer")),
                            has_coop=bool(state_dict.get("coop_answer"))
                        )
                    elif node_name == "verify":
                        thinking_log = log_generator.generate_verify_log(
                            query=request.message,
                            needs_fix=state_dict.get("needs_fix", False),
                            follow_up_count=len(state_dict.get("follow_up_questions", [])),
                            suggestion_count=len(state_dict.get("follow_up_suggestions", []))
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
                    
                    # Emit thinking log immediately (same speed as terminal logs)
                    if thinking_log:
                        log_data = {'type': 'thinking', 'message': thinking_log, 'node': node_name, 'timestamp': time.time()}
                        logger.info(f"📤 Streaming thinking log for node '{node_name}': {thinking_log[:100]}...")
                        yield f"data: {json.dumps(log_data)}\n\n"
                        await asyncio.sleep(0.001)  # Minimal delay for proper streaming
                    else:
                        logger.info(f"⏭️  No thinking log generated for node '{node_name}'")
                    
                    # Store final state - correct node is the last one
                    final_state = state_dict.copy()
                    
                    # Break after correct node (last node in pipeline)
                    if node_name == "correct":
                        break
            
            # Check if we got a result
            if not final_state:
                yield f"data: {json.dumps({'type': 'error', 'message': 'No result returned from RAG'})}\n\n"
                return
            
            # Extract final answer
            answer = final_state.get("final_answer") or final_state.get("answer", "No answer generated.")
            code_answer = final_state.get("code_answer")
            coop_answer = final_state.get("coop_answer")
            
            # Combine answers
            combined_answer = answer
            if code_answer:
                combined_answer = f"{combined_answer}\n\n--- Code References ---\n\n{code_answer}"
            if coop_answer:
                combined_answer = f"{combined_answer}\n\n--- Training Manual References ---\n\n{coop_answer}"
            
            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            
            # Extract follow-up questions and suggestions
            follow_up_questions = final_state.get("follow_up_questions", [])
            follow_up_suggestions = final_state.get("follow_up_suggestions", [])
            
            # Build response
            response_data = {
                'reply': combined_answer,
                'message': combined_answer,  # For compatibility
                'session_id': request.session_id,
                'timestamp': datetime.now().isoformat(),
                'latency_ms': round(latency_ms, 2),
                'citations': len(final_state.get("answer_citations", [])),
                'route': final_state.get("data_route"),
                'message_id': message_id,
                'follow_up_questions': follow_up_questions if follow_up_questions else None,
                'follow_up_suggestions': follow_up_suggestions if follow_up_suggestions else None,
                'image_similarity_results': final_state.get("image_similarity_results") if final_state.get("image_similarity_results") else None
            }
            
            # Send completion event with final result
            yield f"data: {json.dumps({'type': 'complete', 'result': response_data})}\n\n"
            
            logger.info(f"✅ Streaming completed in {latency_ms:.2f}ms [ID: {message_id}]")
            
        except Exception as e:
            logger.error(f"❌ Streaming error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "Access-Control-Allow-Origin": "*"  # CORS for streaming
        }
    )


# Additional endpoint for compatibility with different response formats
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
        from database.supabase_client import vs_smart, vs_large
        
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
            "stats_recent": "/stats/recent"
        }
    }

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
