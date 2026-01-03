#!/usr/bin/env python3
"""
FastAPI server for Mantle RAG Chat Interface
Connect the chatbutton Electron app to the rag.py backend
"""

from datetime import datetime
import logging
import re
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv
import os
import json
from html import escape

# Load environment variables from .env file
load_dotenv()

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
    """
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
@app.post("/chat", response_model=ChatResponse)
async def chat_handler(request: ChatRequest):
    """
    Handle chat requests from the Electron chatbutton app.

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

        # Generate unique message ID for feedback tracking
        message_id = f"msg_{int(time.time())}_{uuid.uuid4().hex[:8]}"

        # Consolidate images: use images_base64 array if provided, else fallback to single image_base64
        images_to_process = request.images_base64 or []
        if not images_to_process and request.image_base64:
            images_to_process = [request.image_base64]  # Backwards compatibility
        
        # Run the agentic RAG system (with optional images for VLM processing)
        rag_result = run_agentic_rag(
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
                image_similarity_results=image_similarity_results if image_similarity_results else None
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

            # Prepare response
            response = ChatResponse(
                reply=combined_answer,
                session_id=request.session_id,
                timestamp=datetime.now().isoformat(),
                latency_ms=round(latency_ms, 2),
                citations=total_citations,
                route=rag_result.get("route"),
                message_id=message_id,
                image_similarity_results=image_similarity_results if image_similarity_results else None
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
            message_id=f"err_{int(time.time())}"
        )

        # Don't raise HTTPException here - return error message instead
        # The Electron app expects a ChatResponse object
        return error_response

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


# Root endpoint
@app.get("/")
@app.head("/")
async def root():
    return {
        "message": "Mantle RAG API Server",
        "version": "1.0.0",
        "endpoints": {
            "chat": "/chat",
            "health": "/health",
            "db_health": "/db/health",
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

