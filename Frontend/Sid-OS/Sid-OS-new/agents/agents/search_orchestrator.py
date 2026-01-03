# 1) Imports & Typed State ------------------------------------------------------------
import os, re, json, time
import base64
from io import BytesIO
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Literal, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

# Conditional imports for LangGraph and LangChain (may not be available in all environments)
try:
    from langgraph.graph import StateGraph, END
    from langgraph.checkpoint.memory import MemorySaver
    HAS_LANGGRAPH_FULL = True
except ImportError:
    HAS_LANGGRAPH_FULL = False
    StateGraph = None
    END = None
    MemorySaver = None

try:
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
    from langchain_community.vectorstores import SupabaseVectorStore
    from langchain_core.documents import Document
    from langchain_core.caches import BaseCache  # Fix for Pydantic v2 compatibility
    from langchain_core.callbacks import Callbacks  # Fix for Pydantic v2 compatibility
    # PromptTemplate moved to langchain_core.prompts in newer versions
    try:
        from langchain_core.prompts import PromptTemplate
    except ImportError:
        from langchain.prompts import PromptTemplate  # Fallback for older versions
    HAS_LANGCHAIN = True
    # ChatAnthropic is optional (only needed for Claude models)
    try:
        from langchain_anthropic import ChatAnthropic
    except ImportError:
        ChatAnthropic = None
except ImportError:
    HAS_LANGCHAIN = False
    ChatAnthropic = None
    ChatOpenAI = None
    OpenAIEmbeddings = None
    SupabaseVectorStore = None
    Document = None
    BaseCache = None
    Callbacks = None
    PromptTemplate = None
    ChatAnthropic = None

try:
    from supabase import create_client, Client
    HAS_SUPABASE = True
except ImportError:
    HAS_SUPABASE = False
    create_client = None
    Client = None

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    OpenAI = None

try:
    from dotenv import load_dotenv
    from pathlib import Path
    # Load .env from project root - ensure we find it even when imported from different directories
    # search_orchestrator.py is in localagent/agents/, so go up 2 levels to Sid-OS-new
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file, override=True)
    else:
        # Fallback: try current directory and parent directories (like working RAG code)
        load_dotenv()
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False

# Import enhanced logging system (optional)
try:
    from enhanced_logger import track_function, enhanced_log_capture
    HAS_ENHANCED_LOGGER = True
except ImportError:
    HAS_ENHANCED_LOGGER = False
    # Create dummy functions if not available
    def track_function(func):
        return func
    def enhanced_log_capture():
        return lambda x: x

###--------Logging for Clarity------------------------####
import logging

# DEBUG_MODE: OFF - Only VLM logs will be shown
DEBUG_MODE = False

# Set logging level to WARNING (suppress INFO/DEBUG from all loggers)
LOG_LEVEL = logging.WARNING
logging.basicConfig(level=LOG_LEVEL, format="%(message)s")  # Simple format - just the message

log_query = logging.getLogger("QUERY_FLOW")
log_route = logging.getLogger("ROUTING")
log_db    = logging.getLogger("DATABASE")
log_enh   = logging.getLogger("ENHANCEMENT")
log_syn   = logging.getLogger("SYNTHESIS")
log_vlm   = logging.getLogger("VLM")

# VLM logger - ONLY logger that shows INFO level (for image processing)
log_vlm.setLevel(logging.INFO)

# Suppress ALL other loggers - only show WARNING and above
log_query.setLevel(logging.WARNING)
log_route.setLevel(logging.WARNING)
log_db.setLevel(logging.WARNING)
log_enh.setLevel(logging.WARNING)
log_syn.setLevel(logging.WARNING)

# Special logger for CHUNKS - suppress for cleaner VLM-only logs
log_chunks = logging.getLogger("CHUNKS")
log_chunks.setLevel(logging.WARNING)  # Suppress chunk logs too

# Helper function for always-visible chunk logging
def log_chunk_info(message: str):
    """Log chunk-related info that should always be visible"""
    print(f"📦 {message}")  # Using print to bypass log level

# =============================================================================
# VLM IMAGE DESCRIPTION - Convert screenshots/images to searchable text
# =============================================================================

# Module-level caching for image embedding model (load once, reuse many times)
_image_embedding_model = None
_image_embedding_processor = None
_projection_layer = None  # Projection layer to reduce 1280 → 1024 dimensions

def _get_model_local_path():
    """
    Get the local directory path where the model will be stored in the project.
    Model will be downloaded directly to this folder, not in a cache.
    """
    # Store model directly in Backend/models/vit-h14 directory
    project_root = Path(__file__).resolve().parent
    model_path = project_root / "models" / "vit-h14"
    
    # Create directory if it doesn't exist
    model_path.mkdir(parents=True, exist_ok=True)
    return str(model_path)

def _get_image_embedding_model():
    """Get or create the cached image embedding model and processor."""
    global _image_embedding_model, _image_embedding_processor, _projection_layer
    if _image_embedding_model is None:
        import torch
        from transformers import ViTImageProcessor, ViTModel
        
        # Use ViT-Huge (H/14) which produces 1280 dimensions
        # We'll project it down to 1024 to match database schema
        model_name = "google/vit-huge-patch14-224-in21k"
        local_model_path = _get_model_local_path()
        
        log_vlm.info(f"🖼️ Loading image embedding model: {model_name}")
        log_vlm.info(f"🖼️ Model storage: {local_model_path}")
        
        # Check if model already exists locally
        model_exists = Path(local_model_path).exists() and any(Path(local_model_path).iterdir())
        
        if model_exists:
            log_vlm.info(f"🖼️ Loading model from local directory: {local_model_path}")
        else:
            log_vlm.info(f"🖼️ Downloading model to: {local_model_path} (first time only)")
        
        # Load model from local path (downloads if not present, loads from disk if present)
        _image_embedding_processor = ViTImageProcessor.from_pretrained(
            model_name,
            cache_dir=local_model_path
        )
        _image_embedding_model = ViTModel.from_pretrained(
            model_name,
            cache_dir=local_model_path
        )
        
        # Create projection layer to reduce 1280 → 1024 dimensions (matches database schema)
        model_hidden_size = _image_embedding_model.config.hidden_size
        target_size = 1024  # Database expects 1024 dimensions
        
        if model_hidden_size != target_size:
            log_vlm.info(f"🖼️ Model produces {model_hidden_size} dimensions, adding projection to {target_size} for database compatibility")
            _projection_layer = torch.nn.Linear(model_hidden_size, target_size)
            _projection_layer.eval()  # Set to evaluation mode
            log_vlm.info(f"🖼️ Projection layer created: {model_hidden_size} → {target_size}")
        else:
            _projection_layer = None
            log_vlm.info(f"🖼️ No projection needed, model already produces {target_size} dimensions")
        
        log_vlm.info(f"🖼️ Image embedding model ready (stored at: {local_model_path}, output: {target_size} dims)")
    return _image_embedding_model, _image_embedding_processor

def describe_image_for_search(image_base64: str, user_question: str = "") -> str:
    """
    Use VLM to convert an image into a searchable text description.
    Works for any type of image - drawings, code documents, photos, etc.
    
    Args:
        image_base64: Base64 encoded image data
        user_question: Optional user question to focus the description
        
    Returns:
        Detailed text description suitable for embedding search
    """
    client = OpenAI()
    
    # Build context-aware prompt with maximum detail extraction
    if user_question:
        prompt = f"""You are an expert technical document analyzer. Examine this image exhaustively and provide a comprehensive description.

The user is asking: "{user_question}"

Provide an extremely detailed description covering ALL of the following:

**1. DOCUMENT IDENTIFICATION:**
- What type of document is this? (structural drawing, architectural detail, building code section, calculation sheet, specification, photo, sketch, table, diagram, etc.)
- Any title, heading, or document name visible
- Project number, drawing number, revision number, date
- Company name, engineer/architect stamps, or signatures

**2. ALL VISIBLE TEXT - Transcribe everything you can read:**
- Headers, titles, labels
- Notes, annotations, callouts
- Dimensions and measurements (with units)
- Reference numbers, grid lines, section marks
- Table contents, column headers, data values
- Code sections, clause numbers, requirements
- Any fine print or smaller text

**3. TECHNICAL CONTENT:**
- Structural members shown (beams, columns, connections, etc.) with sizes if visible
- Material specifications (steel grades, concrete strength, wood species)
- Connection details, fasteners, welds
- Spacing, pitch, gauges
- Load values, design criteria
- Code references (NBCC, ASCE, CSA, etc.)

**4. GRAPHICAL ELEMENTS:**
- What is being depicted in the drawing/diagram
- Scale if shown
- Section cuts, detail callouts
- Symbols and their meaning
- Hatching patterns, line types

**5. CONTEXT FOR SEARCH:**
- What engineering topic does this relate to?
- What would someone search for to find related information?
- Key technical terms that should be used for retrieval

Be thorough - every piece of text and every detail matters for search accuracy."""
    else:
        prompt = """You are an expert technical document analyzer. Examine this image exhaustively and provide a comprehensive description.

Provide an extremely detailed description covering ALL of the following:

**1. DOCUMENT IDENTIFICATION:**
- What type of document is this? (structural drawing, architectural detail, building code section, calculation sheet, specification, photo, sketch, table, diagram, etc.)
- Any title, heading, or document name visible
- Project number, drawing number, revision number, date
- Company name, engineer/architect stamps, or signatures

**2. ALL VISIBLE TEXT - Transcribe everything you can read:**
- Headers, titles, labels
- Notes, annotations, callouts
- Dimensions and measurements (with units)
- Reference numbers, grid lines, section marks
- Table contents, column headers, data values
- Code sections, clause numbers, requirements
- Any fine print or smaller text

**3. TECHNICAL CONTENT:**
- Structural members shown (beams, columns, connections, etc.) with sizes if visible
- Material specifications (steel grades, concrete strength, wood species)
- Connection details, fasteners, welds
- Spacing, pitch, gauges
- Load values, design criteria
- Code references (NBCC, ASCE, CSA, etc.)

**4. GRAPHICAL ELEMENTS:**
- What is being depicted in the drawing/diagram
- Scale if shown
- Section cuts, detail callouts
- Symbols and their meaning
- Hatching patterns, line types

**5. CONTEXT FOR SEARCH:**
- What engineering topic does this relate to?
- What would someone search for to find related information?
- Key technical terms that should be used for retrieval

Be thorough - every piece of text and every detail matters for search accuracy."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_base64}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_tokens=2000
        )
        
        description = response.choices[0].message.content
        log_vlm.info(f"🖼️ VLM generated description: {len(description)} chars")
        return description
        
    except Exception as e:
        log_vlm.error(f"🖼️ VLM processing failed: {e}")
        raise

# =============================================================================
# IMAGE EMBEDDING GENERATION - Vit-H14 for image similarity search
# =============================================================================

def generate_vit_h14_embedding(image_base64: str) -> List[float]:
    """
    Generate Vision Transformer (ViT-H/14) embedding for an image.
    Uses ViT-Huge model (google/vit-huge-patch14-224-in21k) which produces 1280-dimensional embeddings.
    Projects down to 1024 dimensions to match database schema (vector(1024)).
    
    Args:
        image_base64: Base64 encoded image data
        
    Returns:
        List of floats representing the image embedding vector (1024 dimensions)
        
    Raises:
        ImportError: If required libraries (transformers, torch, pillow) are not installed
        Exception: If image processing or embedding generation fails
    """
    try:
        # Import required libraries (with clear error message if missing)
        try:
            from PIL import Image
            import torch
        except ImportError as import_err:
            log_vlm.error("🖼️ Required libraries not installed for image embeddings")
            log_vlm.error("🖼️ Please install: pip install transformers torch pillow")
            raise ImportError(
                "Image embedding generation requires: transformers, torch, pillow. "
                f"Missing: {import_err}"
            ) from import_err
        
        # Decode base64 image
        image_data = base64.b64decode(image_base64)
        image = Image.open(BytesIO(image_data))
        
        # Convert to RGB if necessary (ViT expects RGB)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Use cached model and processor (loads once, reuses on subsequent calls)
        model, processor = _get_image_embedding_model()
        global _projection_layer
        
        # Process image and generate embedding
        inputs = processor(images=image, return_tensors="pt")
        with torch.no_grad():
            outputs = model(**inputs)
            # Get the CLS token embedding (first token)
            # Shape: [batch, seq_len, hidden_size] -> [0, 0, :] gets CLS token
            embedding = outputs.last_hidden_state[0, 0]  # Shape: [hidden_size]
            
            # Apply projection layer if needed (reduces 1280 → 1024)
            if _projection_layer is not None:
                embedding = _projection_layer(embedding)
                log_vlm.info(f"🖼️ Applied projection: {model.config.hidden_size} → 1024 dimensions")
            
            embedding = embedding.cpu().numpy().tolist()
        
        embedding_dim = len(embedding)
        log_vlm.info(f"🖼️ Generated image embedding: {embedding_dim} dimensions")
        
        # Verify it's exactly 1024 dimensions (required by database schema)
        if embedding_dim != 1024:
            log_vlm.error(f"🖼️ ERROR: Expected 1024 dimensions but got {embedding_dim}")
            log_vlm.error(f"🖼️ Database schema requires vector(1024)")
            raise ValueError(f"Embedding dimension mismatch: expected 1024, got {embedding_dim}")
        
        return embedding
        
    except ImportError:
        # Re-raise ImportError with clear message
        raise
    except Exception as e:
        log_vlm.error(f"🖼️ Image embedding generation failed: {e}")
        import traceback
        log_vlm.error(f"🖼️ Traceback: {traceback.format_exc()}")
        raise

def classify_image_query_intent(user_query: str, image_base64: Optional[str] = None) -> Dict[str, Any]:
    """
    Classify user intent to determine if image similarity search is needed.
    
    TEMPORARY: Always does image similarity search when image is present.
    
    Args:
        user_query: The user's text query
        image_base64: Optional base64 image (for future use)
        
    Returns:
        Dict with 'intent', 'use_image_similarity', and 'confidence'
    """
    query_lower = user_query.lower().strip()
    
    # TEMPORARY: If image is present, ALWAYS do image similarity search
    if image_base64:
        log_vlm.info(f"🖼️ IMAGE INTENT CLASSIFICATION: Image present - FORCING similarity search (temporary mode)")
        return {
            "intent": "image_similarity",
            "use_image_similarity": True,
            "confidence": 1.0
        }
    
    # Keywords that suggest image similarity search (expanded and more aggressive)
    similarity_keywords = [
        "similar", "simillar", "like this", "same type", "look like", "match", 
        "find similar", "show similar", "other images", "other drawings",
        "same drawing", "similar screenshot", "find images like",
        "find me similar", "show me similar", "get similar", "find similar images",
        "similar images", "similar drawings", "similar screenshots",
        "images like", "drawings like", "screenshots like",
        "find other", "show other", "other similar", "more like",
        "comparable", "resemble", "alike", "equivalent"
    ]
    
    # Keywords that suggest content detail query (use existing VLM path)
    detail_keywords = [
        "what is", "explain", "describe", "what does", "tell me about",
        "details", "information", "what shows", "analyze", "what does this show",
        "what is this", "explain this", "describe this"
    ]
    
    # Check for similarity intent - more aggressive matching
    similarity_score = 0
    for keyword in similarity_keywords:
        if keyword in query_lower:
            similarity_score += 1
            # Boost score for explicit requests
            if any(phrase in query_lower for phrase in ["find", "show", "get", "give me"]):
                similarity_score += 0.5
    
    detail_score = sum(1 for keyword in detail_keywords if keyword in query_lower)
    
    # Prioritize similarity if ANY similarity keywords found (unless strong detail request)
    if similarity_score > 0:
        if detail_score > similarity_score * 2:
            # Strong detail request overrides similarity
            intent = "content_detail"
            use_similarity = False
            confidence = min(0.9, 0.5 + (detail_score * 0.1))
        else:
            # Similarity request takes priority
            intent = "image_similarity"
            use_similarity = True
            confidence = min(0.95, 0.6 + (similarity_score * 0.1))
    elif detail_score > 0:
        intent = "content_detail"
        use_similarity = False
        confidence = min(0.9, 0.5 + (detail_score * 0.1))
    else:
        # Default: use content detail (existing behavior)
        intent = "content_detail"
        use_similarity = False
        confidence = 0.5
    
    log_vlm.info(f"🖼️ IMAGE INTENT CLASSIFICATION: query='{user_query[:100]}', intent={intent}, use_similarity={use_similarity}, confidence={confidence:.2f}, similarity_score={similarity_score}, detail_score={detail_score}")
    
    return {
        "intent": intent,
        "use_image_similarity": use_similarity,
        "confidence": confidence
    }

# ---- Typed RAG state passed between graph nodes ----
@dataclass
class RAGState:
    session_id: str = ""
    user_query: str = ""
    # planning / routing
    query_plan: Optional[Dict] = None
    data_sources: Dict[str, bool] = field(default_factory=lambda: {"project_db": True, "code_db": False, "coop_manual": False})
    data_route: Optional[Literal["smart","large"]] = None
    project_filter: Optional[str] = None
    active_filters: Optional[Dict[str, Any]] = None  # Store extracted filters for synthesis
    # retrieval artifacts
    expanded_queries: List[str] = field(default_factory=list)
    retrieved_docs: List[Document] = field(default_factory=list)
    retrieved_code_docs: List[Document] = field(default_factory=list)  # Code docs from retrieval (separate pipeline)
    retrieved_coop_docs: List[Document] = field(default_factory=list)  # Coop docs from retrieval (separate pipeline)
    graded_docs: List[Document] = field(default_factory=list)
    graded_code_docs: List[Document] = field(default_factory=list)  # Graded code docs (separate pipeline)
    graded_coop_docs: List[Document] = field(default_factory=list)  # Graded coop docs (separate pipeline)
    db_result: Optional[str] = None
    # synthesis
    final_answer: Optional[str] = None
    answer_citations: List[Dict] = field(default_factory=list)
    code_answer: Optional[str] = None  # Separate answer for code database
    code_citations: List[Dict] = field(default_factory=list)  # Citations for code answer
    coop_answer: Optional[str] = None  # Separate answer for coop manual database
    coop_citations: List[Dict] = field(default_factory=list)  # Citations for coop answer
    answer_support_score: float = 0.0
    # control
    corrective_attempted: bool = False
    needs_fix: bool = False

    # carry the selected projects across steps ---
    selected_projects: List[str] = field(default_factory=list)
    
    # image similarity search (optional - doesn't affect existing pipeline)
    images_base64: Optional[List[str]] = None  # Base64 encoded images from frontend
    image_embeddings: Optional[List[List[float]]] = None  # Vit-H14 embeddings (one per image)
    image_similarity_results: List[Dict] = field(default_factory=list)  # Similar images found
    use_image_similarity: bool = False  # Flag to enable/disable image search
    query_intent: Optional[Literal["image_similarity", "content_detail", "hybrid"]] = None

###-----Memory
SESSION_MEMORY: Dict[str, Dict] = {}
MAX_CONVERSATION_HISTORY = 5  # Keep last 5 Q&A exchanges
MAX_SEMANTIC_HISTORY = 5  # Keep semantic intelligence for last 5 exchanges

# Focus State for intelligent query rewriting
from typing import TypedDict, Optional as Opt
FocusState = TypedDict("FocusState", {
    "recent_projects": list[str],        # MRU, dedup, max ~10
    "last_answer_projects": list[str],   # extracted from last answer
    "last_results_projects": list[str],  # extracted from last retrieval
    "last_query_text": str,
})

# Global focus state storage
FOCUS_STATES: Dict[str, FocusState] = {}

def update_focus_state(session_id: str, query: str, projects: list[str] = None, results_projects: list[str] = None):
    """Update focus state with new information"""
    if session_id not in FOCUS_STATES:
        FOCUS_STATES[session_id] = {
            "recent_projects": [],
            "last_answer_projects": [],
            "last_results_projects": [],
            "last_query_text": ""
        }
    
    state = FOCUS_STATES[session_id]
    
    # Update recent projects (MRU, dedup, max 10)
    if projects:
        for p in projects:
            if p in state["recent_projects"]:
                state["recent_projects"].remove(p)
            state["recent_projects"].append(p)
        state["recent_projects"] = state["recent_projects"][-10:]  # Keep last 10
    
    if results_projects:
        state["last_results_projects"] = results_projects
    
    state["last_query_text"] = query
    
    log_query.info(f"🎯 FOCUS STATE UPDATED: recent_projects={state['recent_projects'][-3:]}, last_results={state['last_results_projects'][-3:]}")


def _extract_semantic_context_for_rewriter(session_data: dict) -> dict:
    """Extract semantic context for query rewriting."""
    last_semantic = session_data.get("last_semantic", {})
    semantic_history = session_data.get("semantic_history", [])
    
    # Extract recent topics and complexity patterns
    recent_topics = []
    recent_complexity = []
    recent_operations = []
    
    # Get data from last semantic intelligence
    if last_semantic:
        planning = last_semantic.get("planning", {})
        routing = last_semantic.get("routing", {})
        execution = last_semantic.get("execution", {})
        
        recent_topics.extend(planning.get("topics_explored", []))
        recent_complexity.append(planning.get("complexity_assessment", ""))
        recent_operations.extend(execution.get("operations_performed", []))
    
    # Get patterns from semantic history (last 2-3 exchanges)
    for semantic_record in semantic_history[-2:]:
        planning = semantic_record.get("planning", {})
        recent_topics.extend(planning.get("topics_explored", []))
        recent_complexity.append(planning.get("complexity_assessment", ""))
    
    return {
        "recent_topics": list(set([t for t in recent_topics if t]))[:5],  # Unique, limit to 5
        "recent_complexity_patterns": list(set([c for c in recent_complexity if c]))[:3],
        "recent_operation_patterns": list(set([o for o in recent_operations if o]))[:5],
        "last_route": last_semantic.get("routing", {}).get("data_route", ""),
        "last_scope": last_semantic.get("routing", {}).get("scope_assessment", "")
    }

def intelligent_query_rewriter(user_query: str, session_id: str) -> tuple[str, dict]:
    """
    Use LLM to intelligently rewrite queries and detect follow-ups
    Returns: (rewritten_query, filters_dict)
    """
    import re
    import json
    
    # Guardrail 1: Extract explicit project IDs with regex
    explicit_ids = re.findall(r'\b\d{2}-\d{2}-\d{3}\b', user_query)
    if explicit_ids:
        log_query.info(f"🎯 EXPLICIT IDs DETECTED: {explicit_ids}")
        return user_query, {"project_keys": explicit_ids}
    
    # Get focus state
    focus_state = FOCUS_STATES.get(session_id, {
        "recent_projects": [],
        "last_answer_projects": [],
        "last_results_projects": [],
        "last_query_text": ""
    })
    
    # SEMANTIC INTELLIGENCE: Get semantic context from session memory
    session_data = SESSION_MEMORY.get(session_id, {})
    semantic_context = _extract_semantic_context_for_rewriter(session_data)
    
    # ENHANCED: Let LLM determine if it's a follow-up based on full semantic context
    # No more hardcoded indicators - LLM makes intelligent decision
    
    # Enhanced LLM-based rewriting with semantic intelligence
    focus_context = {
        "recent_projects": focus_state["recent_projects"][-5:],  # Last 5 recent
        "last_answer_projects": focus_state["last_answer_projects"],
        "last_results_projects": focus_state["last_results_projects"],
        "last_query": focus_state["last_query_text"],
        # NEW: Semantic intelligence
        "recent_topics": semantic_context["recent_topics"],
        "recent_complexity": semantic_context["recent_complexity_patterns"],
        "last_route_preference": semantic_context["last_route"],
        "last_scope_pattern": semantic_context["last_scope"]
    }
    
    log_query.info(f"🎯 FOCUS CONTEXT FOR REWRITER: {focus_context}")
    
    prompt = f"""You are a classifier for an engineering-drawings RAG system. Your job is to determine if a query is a follow-up to previous conversation.

CURRENT QUERY: "{user_query}"

CONVERSATION CONTEXT:
{json.dumps(focus_context, indent=2)}

SEMANTIC INTELLIGENCE:
- Recent topics explored: {semantic_context["recent_topics"]}
- Recent complexity patterns: {semantic_context["recent_complexity_patterns"]}  
- Last route preference: {semantic_context["last_route"]}
- Last scope pattern: {semantic_context["last_scope"]}

TASK: Analyze if this query is a follow-up to previous conversation context.

FOLLOW-UP INDICATORS (clear signals that indicate follow-up):
- Explicit references to prior context:
  * Pronouns: "it", "that one", "those", "the project", "the one you mentioned"
  * Positional references: "the first one", "the second project", "the last one", "the second one"
  * Explicit references: "the project I asked about", "the same one", "that project"
  * Requests for more info: "tell me more about it", "give me more info on the second one"
- Query is incomplete without prior context (unclear what "it", "that", "the second one" refers to)
- Query continues previous topic: "also", "additionally", "furthermore" (when clearly continuing same topic)
- Query asks for different perspective on same topic from prior conversation

NON-FOLLOW-UP INDICATORS (clear signals that indicate NEW query):
- Complete, self-contained questions that make sense without context
- New topics unrelated to recent conversation
- Explicit project IDs mentioned (25-XX-XXX format) - these are explicit, not follow-ups
- Specific dates/locations that weren't discussed recently
- Questions that clearly introduce new information or shift focus to unrelated topic
- General questions about engineering concepts (not referencing prior results)
- Questions that could be answered independently without prior context

CLASSIFICATION RULES:
- If query contains pronouns/positional references ("it", "the second one", "that project"), it's likely a follow-up
- If query is self-contained and makes sense without context, it's likely NOT a follow-up
- BE CONSERVATIVE: When genuinely ambiguous, classify as "new" (not follow-up)
- Only classify as follow-up if you can identify what prior context is being referenced

CONFIDENCE GUIDELINES:
- 0.95-1.0: Strong evidence (pronouns, "the second one", "tell me more about it", etc.)
- 0.85-0.94: Clear evidence but some ambiguity
- 0.70-0.84: Ambiguous - classify as "new" unless very clear follow-up indicators
- 0.0-0.69: Clear standalone question - classify as "new"

REWRITING STRATEGY:
1. If follow-up: Expand query with specific terms from context
2. If follow-up: Resolve vague references to concrete entities
3. If follow-up: Include relevant project IDs from recent context
4. If not follow-up: Pass through unchanged

OUTPUT STRICT JSON (no markdown, no code fences):
{{
  "is_followup": boolean,
  "confidence": 0.0-1.0,
  "reasoning": "Why this is/isn't a follow-up based on context analysis",
  "rewritten_query": "Enhanced query with context or original if not followup",
  "filters": {{
    "project_keys": ["ID1", "ID2"],
    "keywords": ["term1", "term2"]
  }},
  "semantic_enrichment": ["topic1", "topic2"]
}}"""

    try:
        response = llm_fast.invoke(prompt).content.strip()
        log_query.info(f"🎯 LLM RESPONSE: {response}")
        
        # Parse JSON response
        try:
            # Extract JSON from response (in case LLM adds extra text)
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
            else:
                result = json.loads(response)
        except json.JSONDecodeError:
            log_query.error(f"🎯 JSON PARSE ERROR: {response}")
            return user_query, {}
        
        # Enhanced: LLM-based follow-up determination with confidence and reasoning
        confidence = result.get("confidence", 0.0)
        is_followup = result.get("is_followup", False)
        reasoning = result.get("reasoning", "No reasoning provided")
        semantic_enrichment = result.get("semantic_enrichment", [])
        
        log_query.info(f"🧠 LLM ANALYSIS: is_followup={is_followup}, confidence={confidence:.2f}")
        log_query.info(f"🧠 REASONING: {reasoning}")
        if semantic_enrichment:
            log_query.info(f"🧠 SEMANTIC ENRICHMENT: {semantic_enrichment}")
        
        # Process based on LLM's follow-up determination
        if is_followup and confidence >= 0.95:
            rewritten_query = result.get("rewritten_query", user_query)
            filters = result.get("filters", {})
            
            # Enhanced: Handle project keys from filters
            project_keys = filters.get("project_keys", [])
            
            # Fallback logic if LLM didn't identify specific projects
            if not project_keys:
                fallback_projects = focus_state["last_answer_projects"] or focus_state["recent_projects"]
                if fallback_projects:
                    project_keys = fallback_projects[:2]  # Limit to 2 most relevant
                    filters["project_keys"] = project_keys
                    log_query.info(f"🎯 FALLBACK TO CONTEXT PROJECTS: {project_keys}")
            
            log_query.info(f"🎯 FOLLOW-UP DETECTED: '{user_query}' → '{rewritten_query}'")
            log_query.info(f"🎯 ENRICHED WITH: projects={project_keys}, topics={semantic_enrichment}")
        else:
            # Not a follow-up or low confidence - pass through unchanged
            rewritten_query = user_query
            filters = {}
            log_query.info(f"🎯 NON-FOLLOW-UP: Passing through unchanged (confidence={confidence:.2f})")
        
        log_query.info(f"🎯 QUERY REWRITER: {user_query} → {rewritten_query}")
        log_query.info(f"🎯 FILTERS: {filters}")
        
        return rewritten_query, filters
        
    except Exception as e:
        log_query.error(f"🎯 QUERY REWRITER ERROR: {e}")
        return user_query, {}


def get_conversation_context(session_id: str, max_exchanges: int = 3) -> str:
    """
    Format recent conversation history for inclusion in prompts.
    Returns a formatted string with the last N question-answer pairs, prioritizing most recent.
    """
    session = SESSION_MEMORY.get(session_id, {})
    history = session.get("conversation_history", [])

    if not history:
        log_query.info("💭 CONVERSATION CONTEXT: No prior history found")
        return ""

    # Get last N exchanges (most recent first internally, but we'll format oldest-to-newest for clarity)
    recent = history[-max_exchanges:]

    # Log what we're retrieving
    log_query.info(f"💭 CONVERSATION CONTEXT: Retrieving {len(recent)} of {len(history)} total exchanges (prioritizing most recent)")
    for i, exchange in enumerate(recent, 1):
        q = exchange.get("question", "")[:80]  # First 80 chars
        projects = exchange.get("projects", [])
        log_query.info(f"   Exchange {i}: Q: {q}... | Projects: {projects[:3]}")

    lines = [
        "RECENT CONVERSATION HISTORY (last 3 exchanges, ordered oldest to newest):",
        "IMPORTANT: When the user asks a follow-up question, DEFAULT to the MOST RECENT exchange (the last one below) unless they EXPLICITLY reference an older one.",
        "Examples of explicit references: 'the first question', 'originally', 'earlier we discussed', 'back to...'",
        "If no explicit reference → assume MOST RECENT exchange."
    ]

    for i, exchange in enumerate(recent, 1):
        q = exchange.get("question", "")
        a = exchange.get("answer", "")
        projects = exchange.get("projects", [])

        # Truncate long answers to keep context manageable
        a_truncated = a[:300] + "..." if len(a) > 300 else a

        # Mark the most recent exchange
        is_most_recent = (i == len(recent))
        exchange_label = f"Exchange {i}" + (" (MOST RECENT - DEFAULT CONTEXT)" if is_most_recent else "")

        lines.append(f"\n{exchange_label}:")
        lines.append(f"Q: {q}")
        lines.append(f"A: {a_truncated}")
        if projects:
            lines.append(f"Projects mentioned: {', '.join(projects[:5])}")

    return "\n".join(lines)


# 2) Config, Paths, and Globals ------------------------------------------------------------
from pathlib import Path

BACKEND_DIR  = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent  # go up: <project>/
#--------------------------Load Playbook---------------------------------------------------
try:
    # Try current directory first (for Docker), then try Backend subdirectory (for local)
    playbook_paths = [
        BACKEND_DIR / "planner_playbook.md",  # Docker: /app/planner_playbook.md
        PROJECT_ROOT / "Backend" / "planner_playbook.md"  # Local: RAG/Backend/planner_playbook.md
    ]
    PLAYBOOK_PATH = next((p for p in playbook_paths if p.exists()), playbook_paths[0])
    PLANNER_PLAYBOOK = PLAYBOOK_PATH.read_text(encoding="utf-8")
except Exception as e:
    PLANNER_PLAYBOOK = "No playbook provided."
    print(f"Failed to load playbook: {e}")  # Debug log
#--------------------------Load Project Categories---------------------------------------------------
try:
    # Try current directory first (for Docker), then try Backend subdirectory (for local)
    category_paths = [
        BACKEND_DIR / "project_categories.md",  # Docker: /app/project_categories.md
        PROJECT_ROOT / "Backend" / "project_categories.md"  # Local: RAG/Backend/project_categories.md
    ]
    CATEGORIES_PATH = next((p for p in category_paths if p.exists()), category_paths[0])
    PROJECT_CATEGORIES = CATEGORIES_PATH.read_text(encoding="utf-8")
except Exception as e:
    PROJECT_CATEGORIES = "No project categories provided."
    print(f"Failed to load project categories: {e}")  # Debug log
# =============================================================================
# MODEL CONFIGURATION - Optimized for Cost & Performance
FAST_MODEL = os.getenv("FAST_MODEL", "gpt-4o-mini")  # Fast + cheap for simple tasks
ROUTER_MODEL = os.getenv("ROUTER_MODEL", "gpt-4o-mini")  # Routing decisions
GRADER_MODEL = os.getenv("GRADER_MODEL", "gpt-4o-mini")  # Document grading
SUPPORT_MODEL = os.getenv("SUPPORT_MODEL", "gpt-4o-mini")  # Support scoring

# High-Quality Models (for synthesis, final answers)
SYNTHESIS_MODEL = os.getenv("SYNTHESIS_MODEL", "gpt-5")  # Final answer synthesis
CORRECTIVE_MODEL = os.getenv("CORRECTIVE_MODEL", "gpt-4o")  # Corrective RAG

# Embedding Model
EMB_MODEL = os.getenv("EMB_MODEL", "text-embedding-3-small")

# Hybrid Retrieval Configuration
ENABLE_HYBRID_RETRIEVAL = False

PROJECT_RE = re.compile(r'(?<!\d)(?:\d{2}\D*\d{2}\D*\d{3}|\d{7})(?!\d)')

# CHUNK LIMIT CONSTANTS - CENTRALIZED CONTROL
# =============================================================================
MAX_RETRIEVAL_DOCS = 200        # How many docs to retrieve per subquery (legacy default)
MAX_GRADED_DOCS = 200          # How many docs after grading
MAX_SYNTHESIS_DOCS = 50       # How many docs to synthesize with
MAX_SUPPORT_DOCS = 6           # For support scoring
MAX_ROUTER_DOCS = 4            # For routing decisions
MAX_CORRECTIVE_DOCS = 15       # For corrective retrieval
MAX_CITATIONS_DISPLAY = 20      # How many citations to show in final answer

# Smart vs Large database chunk limits
MAX_SMART_RETRIEVAL_DOCS = 200  # More chunks for smart (concise constraints)
MAX_LARGE_RETRIEVAL_DOCS = 50   # Fewer chunks for large (multi-constraint queries)
MAX_CODE_RETRIEVAL_DOCS = 100   # Reasonable limit for code database

# =============================================================================
# MODEL INSTANCES - Create LLM instances for each task
# =============================================================================

# Model instances - only create if LangChain is available
if HAS_LANGCHAIN and ChatOpenAI is not None:
    # Fix for Pydantic v2 compatibility - rebuild model before instantiation
    try:
        ChatOpenAI.model_rebuild()
    except:
        pass  # If rebuild fails, continue anyway
    
    # Fast models (cheaper, faster)
    llm_fast = ChatOpenAI(model=FAST_MODEL, temperature=0)
    llm_router = ChatOpenAI(model=ROUTER_MODEL, temperature=0)
    llm_grader = ChatOpenAI(model=GRADER_MODEL, temperature=0)
    llm_support = ChatOpenAI(model=SUPPORT_MODEL, temperature=0)
    
    # High-quality models (more expensive, better quality)
    def make_llm(model_name: str, temperature: float = 0.1):
        try:
            if model_name.startswith("claude"):
                api_key = os.getenv("ANTHROPIC_API_KEY")
                if not api_key:
                    raise ValueError("ANTHROPIC_API_KEY not found in environment")
                if ChatAnthropic is None:
                    raise ImportError("ChatAnthropic not available")
                return ChatAnthropic(model=model_name, temperature=temperature, anthropic_api_key=api_key)
            else:
                if ChatOpenAI is None:
                    raise ImportError("ChatOpenAI not available")
                return ChatOpenAI(model=model_name, temperature=temperature)
        except Exception as e:
            log_syn.error(f"Failed to create LLM for {model_name}: {e}")
            raise
    
    llm_synthesis = make_llm(SYNTHESIS_MODEL, temperature=0.1)
    llm_corrective = make_llm(CORRECTIVE_MODEL, temperature=0.1)
    
    # Embeddings
    if OpenAIEmbeddings is not None:
        emb = OpenAIEmbeddings(model=EMB_MODEL)
    else:
        emb = None
else:
    # Dummy values if LangChain not available
    llm_fast = None
    llm_router = None
    llm_grader = None
    llm_support = None
    llm_synthesis = None
    llm_corrective = None
    emb = None
    
    def make_llm(model_name: str, temperature: float = 0.1):
        raise ImportError("LangChain not available. Please install: pip install langchain langchain-openai")


# =============================================================================
# HYBRID RETRIEVAL SYSTEM - Dense + Keyword Matching
# =============================================================================

from collections import defaultdict
from pathlib import Path

# Vector stores (Supabase)
# Match working RAG code exactly (backend/RAG/rag.py lines 878-887)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")  # Support both names
SUPA_SMART_TABLE = "smart_chunks"
SUPA_LARGE_TABLE = "page_chunks"
SUPA_CODE_TABLE = "code_chunks"
SUPA_COOP_TABLE = "coop_chunks"

vs_drawings = None  # legacy placeholder
vs_smart = None
vs_large = None
vs_code = None
vs_coop = None

# Simple check like working RAG code - just check URL and KEY
# Let try/except handle any missing dependencies
if SUPABASE_URL and SUPABASE_KEY:
    print("\nConnecting to Supabase pgvector tables...")
    _supa: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    try:
        vs_smart = SupabaseVectorStore(
            client=_supa,
            embedding=emb,
            table_name=SUPA_SMART_TABLE,
        )

        vs_code = SupabaseVectorStore(
            client=_supa,
            embedding=emb,
            table_name=SUPA_CODE_TABLE,
        )

        vs_coop = SupabaseVectorStore(
            client=_supa,
            embedding=emb,
            table_name=SUPA_COOP_TABLE,
        )

        vs_large = SupabaseVectorStore(
            client=_supa,
            embedding=emb,
            table_name=SUPA_LARGE_TABLE,
        )
        # Startup logging (only in DEBUG_MODE) - match working RAG code
        if DEBUG_MODE:
            print(f"Supabase vector stores ready:")
            print(f"   Smart table: '{SUPA_SMART_TABLE}' -> vs_smart")
            print(f"   Large table: '{SUPA_LARGE_TABLE}' -> vs_large")
            print(f"   Code table: '{SUPA_CODE_TABLE}' -> vs_code")
            print(f"   Coop table: '{SUPA_COOP_TABLE}' -> vs_coop")
            
            # Test connections by checking if tables exist
            try:
                smart_count = _supa.table(SUPA_SMART_TABLE).select("*", count="exact").limit(1).execute()
                large_count = _supa.table(SUPA_LARGE_TABLE).select("*", count="exact").limit(1).execute()
                code_count = _supa.table(SUPA_CODE_TABLE).select("*", count="exact").limit(1).execute()
                coop_count = _supa.table(SUPA_COOP_TABLE).select("*", count="exact").limit(1).execute()
                print(f"   Smart table rows: {smart_count.count}")
                print(f"   Large table rows: {large_count.count}")
                print(f"   Code table rows: {code_count.count}")
                print(f"   Coop table rows: {coop_count.count}") 
            except Exception as e:
                print(f"   WARNING: Could not count rows: {e}")
    except Exception as e:
        print(f"ERROR: Supabase vector store init failed: {e}")  # Always show errors
        vs_smart = None
        vs_large = None
        vs_code = None
        vs_coop = None
else:
    print("WARNING: SUPABASE_URL/ANON_KEY not set. Supabase vector stores are required.")
    vs_smart = None
    vs_large = None
    vs_code = None
    vs_coop = None

# Memory (LangGraph built-in in-memory checkpoint)
memory = MemorySaver() if HAS_LANGGRAPH_FULL and MemorySaver is not None else None

# 3) Supabase Project Metadata ------------------------------------------------------------

def fetch_project_metadata(project_ids: List[str]) -> Dict[str, Dict[str, str]]:
    """
    Fetch project names and addresses from Supabase project_info table for ALL project IDs.
    
    Args:
        project_ids: List of ALL unique project IDs from retrieved chunks
                    Example: ["25-08-005", "25-01-007", "25-07-118", "24-12-003"]
    
    Returns:
        Dict mapping EVERY project_id to {name, address, city, postal_code}
        Example: {
            "25-08-005": {"name": "Smith Residence", "address": "123 Main St...", "city": "Toronto", "postal_code": "M5V 3A8"},
            "25-01-007": {"name": "Jones Office", "address": "456 Oak Ave...", "city": "Vancouver"}
        }
    """
    if not project_ids:
        return {}
    
    # Check if Supabase is configured
    if not SUPABASE_URL or not SUPABASE_KEY:
        log_db.error("Supabase not configured, skipping project metadata lookup")
        return {}
    
    try:
        log_db.info(f"Fetching metadata for {len(project_ids)} projects from Supabase")
        
        # Create Supabase client
        _supa = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Query project_info table for all project IDs
        # Use .in_() filter for efficient batch lookup
        result = _supa.table("project_info").select(
            "project_key, project_name, project_address, project_city, project_postal_code"
        ).in_("project_key", project_ids).execute()
        
        # Build result dictionary for ALL found projects
        metadata = {}
        for row in result.data:
            project_key = row.get("project_key")
            if project_key:
                metadata[project_key] = {
                    "name": row.get("project_name") or "",
                    "address": row.get("project_address") or "",
                    "city": row.get("project_city") or "",
                    "postal_code": row.get("project_postal_code") or ""
                }
        
        log_db.info(f"Retrieved metadata for {len(metadata)}/{len(project_ids)} projects from Supabase project_info table")
        
        # Only log missing projects if DEBUG_MODE - don't spam warnings
        # Missing metadata is OK - it's just enrichment, not required
        if DEBUG_MODE:
            missing_count = sum(1 for proj_id in project_ids if proj_id not in metadata)
            if missing_count > 0:
                log_db.debug(f"{missing_count} projects not found in project_info table (metadata is optional)")
        
        return metadata
        
    except Exception as e:
        # Table doesn't exist or query failed - that's OK, metadata is optional enrichment
        # Only log error if DEBUG_MODE - don't spam console
        if DEBUG_MODE:
            log_db.debug(f"project_info table not available or query failed: {e}. Continuing without metadata enrichment.")
        return {}

def test_database_connection() -> Dict:
    """
    Lightweight healthcheck for Supabase project_info table.
    Returns:
        {
          "connected": bool,
          "project_count": int,     # number of projects in table
          "error": "..."            # present only when connected=False
        }
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        return {"connected": False, "error": "Missing SUPABASE_URL or SUPABASE_KEY env vars"}
    
    try:
        _supa = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Try to count projects in project_info table
        result = _supa.table("project_info").select("*", count="exact").limit(1).execute()
        
        return {
            "connected": True,
            "project_count": result.count
        }
    except Exception as e:
        return {"connected": False, "error": f"Supabase connection failed: {e}"}

# 4) Utilities: Routing, Planning, Expansion, Grading ------------------------------------------------------------

def detect_project_filter(q: str) -> Optional[str]:
    """
    Extract and normalize project ID from query with STRICT exact matching.
    Handles formats: 25-08-005, 2508005, 25/08/005, etc.
    Returns: Normalized format YY-MM-XXX (e.g., "25-08-005") ONLY if exact match
    """
    # More strict regex patterns for exact project ID matching
    patterns = [
        r'\b(\d{2})-(\d{2})-(\d{3})\b',  # 25-08-005 format
        r'\b(\d{2})/(\d{2})/(\d{3})\b',  # 25/08/005 format
        r'\b(\d{2})\.(\d{2})\.(\d{3})\b', # 25.08.005 format
        r'\b(\d{7})\b',                   # 2508005 format (7 digits)
    ]
    
    for pattern in patterns:
        match = re.search(pattern, q)
        if match:
            if len(match.groups()) == 3:  # Format with separators
                year, month, index = match.groups()
                # Validate ranges
                if (0 <= int(year) <= 99 and 
                    1 <= int(month) <= 12 and 
                    1 <= int(index) <= 999):
                    normalized = f"{year}-{month}-{index}"
                    log_query.info(f"🎯 PROJECT DETECTION: Exact match '{match.group(0)}' → '{normalized}'")
                    return normalized
            elif len(match.groups()) == 1:  # 7-digit format
                digits = match.group(1)
                year, month, index = digits[:2], digits[2:4], digits[4:]
                # Validate ranges
                if (0 <= int(year) <= 99 and 
                    1 <= int(month) <= 12 and 
                    1 <= int(index) <= 999):
                    normalized = f"{year}-{month}-{index}"
                    log_query.info(f"🎯 PROJECT DETECTION: Exact match '{digits}' → '{normalized}'")
                    return normalized
    
    log_query.info(f"🎯 PROJECT DETECTION: No exact project ID found in '{q}'")
    return None

#---------------------------------------------------For Checking timing of each node---------------------------------------------------
# --- timing utils ---
import time as _t
def _timeit(msg, fn, *a, **kw):
    t0 = _t.time()
    log_enh.info(f">>> {msg} START")
    out = fn(*a, **kw)
    dt = _t.time() - t0
    log_enh.info(f"<<< {msg} DONE in {dt:.2f}s")
    return out
#---------------------------------------------------Date ID---------------------------------------------------
import datetime as _dt
_PROJECT_ID_RE = re.compile(r"\b(?P<yy>\d{2})-(?P<mm>\d{2})-(?P<seq>\d{3})\b")

#---------------------------------------------------Hybrid Search Fusion---------------------------------------------------
def _rrf_fuse(dense_rows, kw_rows, k: int, k_base: int = 60):
    """
    Reciprocal Rank Fusion: combines dense and keyword search results by rank.
    
    Args:
        dense_rows: List of dicts with {"id","content","metadata","similarity"}
        kw_rows: List of dicts with {"id","content","metadata","score"}
        k: Final number of results to return
        k_base: RRF constant (default 60)
    
    Returns:
        List of fused results maintaining order and deduplication
    """
    rank = {}
    
    # Add dense results (using similarity score for ranking)
    for i, r in enumerate(dense_rows, 1):
        key = r["id"]
        rank[key] = rank.get(key, 0.0) + 1.0 / (k_base + i)
    
    # Add keyword results
    for i, r in enumerate(kw_rows, 1):
        key = r["id"]
        rank[key] = rank.get(key, 0.0) + 1.0 / (k_base + i)
    
    # Build unique ordered ids by RRF score
    ordered_ids = sorted(rank.items(), key=lambda x: x[1], reverse=True)
    keep = {i for i, _ in ordered_ids[:k]}
    
    # Dedupe keeping first appearance order: dense then keyword
    out = []
    seen = set()
    for row in dense_rows + kw_rows:
        if row["id"] in keep and row["id"] not in seen:
            out.append(row)
            seen.add(row["id"])
            if len(out) >= k:
                break
    
    return out

def _log_docs_summary(docs: List[Document], logger, prefix: str = "Documents"):
    """Helper to log document retrieval/grading summary"""
    if not docs:
        logger.info(f"{prefix}: 0 documents")
        return

    # Count unique projects
    projects = set()
    search_types = {}
    for d in docs:
        md = d.metadata or {}
        proj = md.get("drawing_number") or md.get("project_key")
        if proj:
            projects.add(proj)
        stype = md.get("search_type", "unknown")
        search_types[stype] = search_types.get(stype, 0) + 1

    logger.info(f"{prefix}: {len(docs)} docs from {len(projects)} projects | Search types: {search_types}")

    # Log top 3 doc previews
    for i, d in enumerate(docs[:3], 1):
        md = d.metadata or {}
        proj = md.get("drawing_number") or md.get("project_key", "?")
        page = md.get("page_id") or md.get("page", "?")
        preview = (d.page_content or "")[:100].replace("\n", " ")
        logger.info(f"  [{i}] {proj} p.{page}: {preview}...")

def _log_retrieved_chunks_detailed(docs: List[Document], logger):
    """
    Enhanced logging for retrieved chunks - shows projects, chunk distribution, and previews.
    THIS ALWAYS PRINTS - even in production mode.
    """
    if not docs:
        print("📦 RETRIEVED CHUNKS: None")
        # Add chunk tracking for empty results (only if enhanced logger is available)
        if HAS_ENHANCED_LOGGER and hasattr(enhanced_log_capture, 'add_chunk_step'):
            try:
                enhanced_log_capture.add_chunk_step(
                    "RETRIEVED_CHUNKS", 
                    0, 
                    projects=[],
                    details={"total_chunks": 0, "status": "empty"}
                )
            except (AttributeError, TypeError):
                pass  # enhanced_log_capture is a function, not an object
        return

    # Group chunks by project
    from collections import defaultdict
    project_chunks = defaultdict(list)
    for d in docs:
        md = d.metadata or {}
        proj = md.get("drawing_number") or md.get("project_key") or "UNKNOWN"
        project_chunks[proj].append(d)

    # Log summary - ALWAYS VISIBLE
    unique_projects = list(project_chunks.keys())
    print(f"📦 RETRIEVED CHUNKS: {len(docs)} total from {len(unique_projects)} projects: {', '.join(unique_projects[:5])}{'...' if len(unique_projects) > 5 else ''}")
    
    # Add chunk tracking (only if enhanced logger is available)
    if HAS_ENHANCED_LOGGER and hasattr(enhanced_log_capture, 'add_chunk_step'):
        try:
            enhanced_log_capture.add_chunk_step(
                "RETRIEVED_CHUNKS", 
                len(docs), 
                projects=unique_projects,
                details={"total_chunks": len(docs), "project_count": len(unique_projects)}
            )
        except (AttributeError, TypeError):
            pass  # enhanced_log_capture is a function, not an object

    # Detailed logging only in DEBUG_MODE
    if DEBUG_MODE:
        # Log chunk count per project
        for proj in unique_projects[:5]:
            chunks = project_chunks[proj]
            logger.info(f"   • {proj}: {len(chunks)} chunks")

        if len(unique_projects) > 5:
            logger.info(f"   ... and {len(unique_projects) - 5} more projects")

        # Log detailed chunk previews (first 5 chunks)
        logger.info("📄 CHUNK PREVIEWS:")
        for i, d in enumerate(docs[:5], 1):
            md = d.metadata or {}
            proj = md.get("drawing_number") or md.get("project_key", "?")
            page = md.get("page_id") or md.get("page", "?")
            title = md.get("title", "")
            search_type = md.get("search_type", "unknown")
            preview = (d.page_content or "")[:150].replace("\n", " ")

            logger.info(f"   [{i}] Project: {proj} | Page: {page} | Type: {search_type}")
            if title:
                logger.info(f"       Title: {title}")
            logger.info(f"       Content: {preview}...")

        if len(docs) > 5:
            logger.info(f"   ... and {len(docs) - 5} more chunks")

def date_from_project_id(pid: str) -> Optional[_dt.date]:
    """
    Parse 'YY-MM-XXX' → date(2000+YY, MM, 1).
    Returns None if it doesn't look like a project id.
    """
    m = _PROJECT_ID_RE.fullmatch(pid or "")
    if not m:
        return None
    yy = int(m.group("yy"))
    mm = int(m.group("mm"))
    year = 2000 + yy     # adjust if your convention differs
    if not (1 <= mm <= 12):
        return None
    return _dt.date(year, mm, 1)

#------------------------------------------------Checking if Q is follow up---------
def is_follow_up(new_q: str, last_q: Optional[str], session_id: str = "default") -> bool:
    """
    Use LLM to decide if query is follow-up vs new topic.
    Now uses full conversation history instead of just the last question.
    """
    session = SESSION_MEMORY.get(session_id, {})
    history = session.get("conversation_history", [])

    # If no conversation history, it's definitely not a follow-up
    if not history:
        return False

    try:
        # Get the last exchange from conversation history
        last_exchange = history[-1]
        last_q = last_exchange.get("question", "")
        last_response = last_exchange.get("answer", "No previous response")

        # Check if new question is a follow-up
        resp = llm_fast.invoke(FOLLOWUP_PROMPT.format(
            last_q=last_q,
            new_q=new_q,
            response=last_response
        ))
        decision = resp.content.strip().lower()
        is_followup = decision == "follow-up"

        log_query.info(f"Follow-up detection: {'YES' if is_followup else 'NO'}")
        return is_followup
    except Exception as e:
        log_query.error(f"Follow-up detection failed: {e}")
        return False

def make_hybrid_retriever(project: Optional[str] = None, sql_filters: Optional[Dict] = None, route: str = "smart"):
    """Create hybrid retriever (dense + keyword) with project filtering and SQL pre-filtering for project database"""
    
    # Cache for pre-filtered project keys (computed once for all subqueries)
    _prefiltered_project_keys_cache = None
    _total_content_count_cache = None
    
    # Supabase hybrid: dense vector + keyword search on the selected database
    if SUPABASE_URL and SUPABASE_KEY and 'vs_smart' in globals() and 'vs_large' in globals():
        def supabase_hybrid_search(query: str, k: int = 8, keyword_weight: float = None, 
                                  sql_filters: Optional[Dict] = None) -> List[Document]:
            """Enhanced Supabase hybrid search with SQL pre-filtering"""
            
            log_query.info(f"🔍 HYBRID SEARCH CALLED: sql_filters={sql_filters}")
            
            # Get the selected database based on route
            if route == "smart" and vs_smart is not None:
                selected_vs = vs_smart
                table_name = SUPA_SMART_TABLE
            elif route == "large" and vs_large is not None:
                selected_vs = vs_large
                table_name = SUPA_LARGE_TABLE
            elif vs_smart is not None:  # fallback to smart
                selected_vs = vs_smart
                table_name = SUPA_SMART_TABLE
            elif vs_large is not None:  # fallback to large
                selected_vs = vs_large
                table_name = SUPA_LARGE_TABLE
            else:
                log_query.error("No Supabase vector stores available")
                return []

            # Log which table is being used based on route
            log_query.info(f"🎯 ROUTE-BASED TABLE SELECTION: route='{route}' → table='{table_name}'")

            # Apply SQL pre-filtering if provided
            _supa = create_client(SUPABASE_URL, SUPABASE_KEY)
            if sql_filters:
                log_query.info(f"🗓️ SQL PRE-FILTER: Applying filters {sql_filters} to {table_name}")
                try:
                    # STEP 1: SQL Pre-filtering (done ONCE for all subqueries)
                    nonlocal _prefiltered_project_keys_cache, _total_content_count_cache
                    if _prefiltered_project_keys_cache is None:
                        log_query.info("🚀 OPTIMIZATION: Performing SQL pre-filtering ONCE for all subqueries")
                        
                        # Use Supabase client directly for filtering
                        log_query.info(f"🗓️ SQL PRE-FILTER: Creating Supabase client...")
                        
                        # Get filtered project keys first with pagination to bypass 1000 limit
                        log_query.info(f"🗓️ SQL PRE-FILTER: Building paginated query for table {table_name}")
                        
                        all_project_keys = []
                        offset = 0
                        page_size = 1000  # Supabase's max per request
                        
                        while True:
                            log_query.info(f"🗓️ SQL PRE-FILTER: Fetching page {offset//page_size + 1} (offset={offset})")
                            
                            # Build query with pagination
                            query_builder = _supa.table(table_name).select("project_key")
                            
                            # Apply filters
                            log_query.info(f"🗓️ SQL PRE-FILTER: Applying conditions: {sql_filters.get('and', [])}")
                            has_revit_filter = False
                            for condition in sql_filters.get("and", []):
                                if "like" in condition:
                                    key, op, value = condition.split(".", 2)
                                    log_query.info(f"🗓️ SQL PRE-FILTER: Adding LIKE condition: {key}.{op}.{value}")
                                    query_builder = query_builder.like(key, value)
                                elif "eq" in condition:
                                    key, op, value = condition.split(".", 2)
                                    log_query.info(f"🗓️ SQL PRE-FILTER: Adding EQ condition: {key}.{op}.{value}")
                                    # Convert string values to appropriate types
                                    if value.lower() == "true":
                                        value = True
                                    elif value.lower() == "false":
                                        value = False
                                    
                                    # Special logging for Revit filter
                                    if key == "has_revit":
                                        has_revit_filter = True
                                        log_query.info(f"🏗️ SQL QUERY EXECUTION: ✅ Applying Revit filter: has_revit={value} on table '{table_name}'")
                                    
                                    query_builder = query_builder.eq(key, value)
                            
                            # Add pagination
                            if has_revit_filter:
                                log_query.info(f"🏗️ SQL QUERY EXECUTION: Executing SQL query with Revit filter (has_revit=true) on table '{table_name}' (page {offset//page_size + 1})")
                            result = query_builder.range(offset, offset + page_size - 1).execute()
                            
                            if has_revit_filter:
                                log_query.info(f"🏗️ SQL QUERY RESULT: ✅ Revit-filtered query returned {len(result.data) if result.data else 0} rows from table '{table_name}'")
                            
                            if not result.data:
                                log_query.info(f"🗓️ SQL PRE-FILTER: No more data at offset {offset}, stopping pagination")
                                break
                            
                            page_keys = [row["project_key"] for row in result.data]
                            all_project_keys.extend(page_keys)
                            
                            log_query.info(f"🗓️ SQL PRE-FILTER: Page {offset//page_size + 1}: {len(page_keys)} keys")
                            
                            # If we got fewer than page_size, we're done
                            if len(result.data) < page_size:
                                log_query.info(f"🗓️ SQL PRE-FILTER: Last page reached (got {len(result.data)} < {page_size})")
                                break
                            
                            offset += page_size
                    
                        log_query.info(f"🗓️ SQL PRE-FILTER: Pagination complete! Total project keys: {len(all_project_keys)}")
                        filtered_project_keys = all_project_keys
                        
                        log_query.info(f"🗓️ SQL PRE-FILTER: Found {len(filtered_project_keys)} projects matching criteria")
                        log_query.info(f"🗓️ SQL PRE-FILTER: Project keys: {filtered_project_keys[:10]}{'...' if len(filtered_project_keys) > 10 else ''}")
                        
                        if not filtered_project_keys:
                            log_query.info("🗓️ SQL PRE-FILTER: No projects match criteria, returning empty results")
                            return []
                        
                        # Cache the results for future subqueries
                        _prefiltered_project_keys_cache = list(set(filtered_project_keys))
                        _total_content_count_cache = len(all_project_keys)  # Cache total content count
                        log_query.info(f"🗓️ SQL PRE-FILTER: Cached {len(_prefiltered_project_keys_cache)} unique projects for future subqueries")
                        log_query.info(f"🗓️ SQL PRE-FILTER: Total content rows matching criteria: {_total_content_count_cache}")
                    else:
                        log_query.info("🚀 OPTIMIZATION: Using cached SQL pre-filtering results")
                        log_query.info(f"🗓️ SQL PRE-FILTER: Using {len(_prefiltered_project_keys_cache)} cached unique projects")
                    
                    # Get query embedding for the Supabase function
                    log_query.info(f"🔍 HNSW SEARCH: Getting query embedding for semantic search...")
                    query_embedding = emb.embed_query(query)
                    
                    # Use cached project keys
                    unique_project_keys = _prefiltered_project_keys_cache
                    
                    # Call the new capped project function for better project diversity
                    log_query.info(f"🔍 CAP_PROJECTS SEARCH: Using capped project function with {len(unique_project_keys)} unique projects...")
                    
                    # Use the new capped project functions for better project diversity
                    rpc_function = 'match_documents_cap_projects' if table_name == SUPA_SMART_TABLE else 'match_documents_cap_projects_large'

                    # Calculate optimal parameters for project diversity
                    chunks_per_project = 20  # Limit each project to max 20 chunks for better coverage
                    projects_limit = min(50, len(unique_project_keys)) if unique_project_keys else 50  # Cap projects but allow more diversity
                    match_count = 1000  # Deep search for better recall
                    
                    log_query.info(f"🔍 CAP_PROJECTS SEARCH: Using {rpc_function} with projects_limit={projects_limit}, chunks_per_project={chunks_per_project}, match_count={match_count}")
                    
                    result = _supa.rpc(rpc_function, {
                        'query_embedding': query_embedding,
                        'match_count': match_count,
                        'projects_limit': projects_limit,
                        'chunks_per_project': chunks_per_project,
                        'project_keys': unique_project_keys
                    }).execute()
                    
                    # DEBUG: Check what Supabase actually returned
                    log_query.info(f"🔍 SIMILARITY CHECK: total_rows={len(result.data)}")
                    nonzero = sum(1 for r in result.data if r.get('similarity', 0) > 0)
                    zeros = len(result.data) - nonzero
                    sample = [r.get('similarity', r.get('score', 0.0)) for r in result.data[:5]]
                    log_query.info(f"🔍 SIMILARITY STATS: nonzero={nonzero}, zeros={zeros}, sample={sample}")
                    
                    # Convert HNSW result to rows for fusion
                    dense_rows = result.data or []
                    log_query.info(f"🔍 HNSW SEARCH: Got {len(dense_rows)} dense results from {table_name}")
                    
                    # IMPROVED: Ensure even distribution across projects
                    if dense_rows:
                        # Group chunks by project
                        project_chunks = {}
                        for row in dense_rows:
                            project_key = row.get('metadata', {}).get('project_key', 'unknown')
                            if project_key not in project_chunks:
                                project_chunks[project_key] = []
                            project_chunks[project_key].append(row)
                        
                        # Limit chunks per project to ensure even distribution
                        # SQL filter path uses fixed chunks_per_project = 5 (user preference)
                        balanced_rows = []
                        for project_key, chunks in project_chunks.items():
                            # Take top chunks per project (already sorted by similarity)
                            limited_chunks = chunks[:chunks_per_project]  # Use SQL filter's chunks_per_project = 5
                            balanced_rows.extend(limited_chunks)
                        
                        dense_rows = balanced_rows
                        log_query.info(f"🔍 HNSW BALANCE: Balanced to {len(dense_rows)} chunks across {len(project_chunks)} projects (max {chunks_per_project} per project, SQL filter path)")
                    
                    # Use dense vector search only (no keyword search for performance)
                    log_query.info(f"🔍 DENSE SEARCH MODE: Using HNSW only (keyword search disabled for performance)")
                    # Pure HNSW only - just take top k results
                    fused_rows = dense_rows[:k]
                    log_query.info(f"🔍 DENSE SEARCH MODE: Returning top {len(fused_rows)} HNSW results")
                    
                    # Convert fused rows to Document objects
                    dense_docs = []
                    for row in fused_rows:
                        # Add similarity score to metadata
                        metadata = row['metadata'].copy() if row['metadata'] else {}
                        metadata['similarity_score'] = row.get('similarity', row.get('score', 0.0))
                        
                        doc = Document(
                            page_content=row['content'],
                            metadata=metadata
                        )
                        dense_docs.append(doc)
                    
                    log_query.info(f"🔍 DENSE SEARCH: Returning {len(dense_docs)} docs from {table_name}")
                    return dense_docs
                    
                except Exception as e:
                    log_query.error(f"SQL pre-filtering failed: {e}")
                    import traceback
                    log_query.error(f"SQL pre-filtering traceback: {traceback.format_exc()}")
                    # Fall back to regular search
            else:
                log_query.info(f"🗓️ SQL PRE-FILTER: No sql_filters provided, skipping pre-filtering")

            # Regular dense vector search (fallback or when no filters)
            # Use the new capped project function without project key filtering
            log_query.info(f"🗓️ CAP_PROJECTS REGULAR SEARCH: No filters, using capped project function...")
            
            # Get query embedding
            query_embedding = emb.embed_query(query)
            
            # Use the new capped project functions for better project diversity
            rpc_function = 'match_documents_cap_projects' if table_name == SUPA_SMART_TABLE else 'match_documents_cap_projects_large'
            
            # Route-dependent chunk limits for better diversity
            # Large chunks (page_chunks) need more chunks per project for context
            # Smart chunks (smart_chunks) are smaller so fewer chunks needed
            if route == "large" or table_name == SUPA_LARGE_TABLE:
                chunks_per_project = 3  # More chunks for large/page table (bigger chunks need more context)
            elif route == "smart" or table_name == SUPA_SMART_TABLE:
                chunks_per_project = 1  # Fewer chunks for smart table (smaller chunks are more atomic)
            else:
                chunks_per_project = 1  # Default fallback
            projects_limit = 50    # Allow up to 50 different projects
            match_count = 1000      # Deep search for better recall
            
            log_query.info(f"🗓️ CAP_PROJECTS REGULAR SEARCH: Using {rpc_function} with projects_limit={projects_limit}, chunks_per_project={chunks_per_project}")
            
            result = _supa.rpc(rpc_function, {
                'query_embedding': query_embedding,
                'match_count': match_count,
                'projects_limit': projects_limit,
                'chunks_per_project': chunks_per_project,
                'project_keys': None
            }).execute()
            
            # DEBUG: Check what Supabase actually returned
            log_query.info(f"🔍 SIMILARITY CHECK: total_rows={len(result.data)}")
            nonzero = sum(1 for r in result.data if r.get('similarity', 0) > 0)
            zeros = len(result.data) - nonzero
            sample = [r.get('similarity', r.get('score', 0.0)) for r in result.data[:5]]
            log_query.info(f"🔍 SIMILARITY STATS: nonzero={nonzero}, zeros={zeros}, sample={sample}")
            
            # Convert HNSW result to rows for fusion
            dense_rows = result.data or []
            log_query.info(f"🔍 HNSW SEARCH: Got {len(dense_rows)} dense results from {table_name}")
            
            # Use dense vector search only (no keyword search for performance)
            log_query.info(f"🔍 DENSE SEARCH MODE: Using HNSW only (keyword search disabled for performance)")
            # Pure HNSW only - just take top k results
            fused_rows = dense_rows[:k]
            log_query.info(f"🔍 DENSE SEARCH MODE: Returning top {len(fused_rows)} HNSW results")
            
            # Convert fused rows to Document objects
            dense_docs = []
            for row in fused_rows:
                # Add similarity score to metadata
                metadata = row['metadata'].copy() if row['metadata'] else {}
                similarity_score = row.get('similarity', row.get('score', 0.0))
                metadata['similarity_score'] = similarity_score
                
                doc = Document(
                    page_content=row['content'],
                    metadata=metadata
                )
                dense_docs.append(doc)
            
            log_query.info(f"🔍 DENSE SEARCH: Returning {len(dense_docs)} docs from {table_name}")
            return dense_docs

        class SupabaseHybrid:
            def hybrid_search(self, query: str, k: int = 8, keyword_weight: float = None, sql_filters: Optional[Dict] = None) -> List[Document]:
                return supabase_hybrid_search(query, k, keyword_weight, sql_filters)

        hybrid_retriever = SupabaseHybrid()
    else:
        raise ValueError("No hybrid retriever available. Supabase tables not initialized.")
    
    def hybrid_search_with_filter(query: str, k: int = 8) -> List[Document]:
        """Enhanced hybrid search with smart SQL pre-filtering and project filtering"""
        
        log_query.info(f"🔍 HYBRID_SEARCH_WITH_FILTER: Called with query='{query[:50]}...', k={k}")
        log_query.info(f"🔍 HYBRID_SEARCH_WITH_FILTER: Using pre-extracted sql_filters={sql_filters}")
        
        # Use the pre-extracted SQL filters instead of extracting from individual query
        # This ensures all sub-queries use the same date filters from the original query
        
        if sql_filters:
            log_query.info(f"🗓️ DATE FILTERING: Using pre-extracted SQL filters: {sql_filters}")
        
        # Get hybrid results - fetch more when filtering
        fetch_count = k * 3 if project else k * 2
        log_query.info(f"🔍 HYBRID_SEARCH_WITH_FILTER: Calling hybrid_retriever.hybrid_search with sql_filters={sql_filters}")
        results = hybrid_retriever.hybrid_search(query, fetch_count, sql_filters=sql_filters)

        log_query.info(f"Hybrid search: requested k={k}, fetched {len(results)} docs before filtering")

        # Apply project filter if specified
        if project:
            # Normalize the filter (remove dashes for comparison)
            normalized_filter = re.sub(r'\D', '', project)

            filtered_results = []
            for i, doc in enumerate(results):
                md = doc.metadata or {}

                # Check multiple possible metadata fields
                doc_project = (md.get('drawing_number') or
                             md.get('project_key') or
                             md.get('project_id') or '')

                # Normalize document project ID (remove dashes)
                normalized_doc = re.sub(r'\D', '', doc_project)

                # Log first 10 docs to show what we're checking
                if i < 10:
                    log_query.info(f"  Doc {i+1}: metadata fields={list(md.keys())[:5]}, "
                                 f"project_value='{doc_project}', normalized='{normalized_doc}'")

                # Match either exact or normalized
                if (project in doc_project or
                    normalized_filter == normalized_doc or
                    project == doc_project):
                    filtered_results.append(doc)

            log_query.info(f"Project filter '{project}' (normalized: {normalized_filter}): "
                         f"{len(results)} -> {len(filtered_results)} docs")
            results = filtered_results

        final = results[:k]
        log_query.info(f"Returning {len(final)} docs after limit k={k}")
        return final

    return hybrid_search_with_filter

def make_code_hybrid_retriever():
    """Create hybrid retriever (dense + keyword) for code database"""
    
    # Supabase hybrid: dense vector + keyword search on code table
    if SUPABASE_URL and SUPABASE_KEY and 'vs_code' in globals() and vs_code is not None:
        def supabase_code_hybrid_search(query: str, k: int = 8, keyword_weight: float = None) -> List[Document]:
            """Enhanced Supabase hybrid search for code database"""
            
            table_name = SUPA_CODE_TABLE
            
            try:
                _supa = create_client(SUPABASE_URL, SUPABASE_KEY)
                query_embedding = emb.embed_query(query)
                match_count = min(1000, k * 5)  # Deep search for better recall
                
                result = _supa.rpc("match_code_documents", {
                    'query_embedding': query_embedding,
                    'match_count': match_count
                }).execute()
                
                # Convert HNSW result to rows for fusion
                dense_rows = result.data or []
                fused_rows = dense_rows[:k]
                
                # Convert fused rows to Document objects
                code_docs = []
                for i, row in enumerate(fused_rows):
                    # SUPABASE CODE_CHUNKS LOGGING: Log row structure from RPC (first row only)
                    if i == 0:
                        log_query.info(f"🔍 SUPABASE CODE_CHUNKS RPC ROW KEYS: {list(row.keys())}")
                        log_query.info(f"🔍 SUPABASE CODE_CHUNKS RPC ROW (first): filename={row.get('filename', 'NOT FOUND')}, page_number={row.get('page_number', 'NOT FOUND')}, has_metadata={bool(row.get('metadata'))}")
                        if row.get('metadata'):
                            log_query.info(f"🔍 SUPABASE CODE_CHUNKS RPC METADATA KEYS: {list(row.get('metadata', {}).keys())}")
                    
                    # Extract metadata - start with nested metadata if it exists
                    metadata = row.get('metadata', {}).copy() if isinstance(row.get('metadata'), dict) else {}
                    
                    # CRITICAL: Extract filename and page_number from TOP-LEVEL row (code_chunks table columns)
                    # The RPC function returns table columns at top level, not just in metadata
                    if 'filename' in row:
                        metadata['filename'] = row['filename']
                        if i == 0:
                            log_query.info(f"🔍 SUPABASE CODE_CHUNKS: Extracted filename from top-level: '{row['filename']}'")
                    elif 'filename' not in metadata:
                        log_query.error(f"🔍 SUPABASE CODE_CHUNKS ERROR: filename NOT found in row (row keys: {list(row.keys())})")
                    
                    if 'page_number' in row:
                        metadata['page_number'] = row['page_number']
                        # Also set 'page' for compatibility
                        metadata['page'] = row['page_number']
                        if i == 0:
                            log_query.info(f"🔍 SUPABASE CODE_CHUNKS: Extracted page_number from top-level: '{row['page_number']}'")
                    elif 'page_number' not in metadata:
                        # Check if it's in metadata with different name
                        if 'page' in metadata and 'page_number' not in metadata:
                            metadata['page_number'] = metadata['page']
                        else:
                            log_query.error(f"🔍 SUPABASE CODE_CHUNKS ERROR: page_number NOT found in row (row keys: {list(row.keys())})")
                    
                    # Copy other code_chunks table fields that might be useful
                    for field in ['source', 'section', 'title', 'file_path', 'id']:
                        if field in row and field not in metadata:
                            metadata[field] = row[field]
                    
                    # Add similarity score
                    metadata['similarity_score'] = row.get('similarity', row.get('score', 0.0))
                    
                    # SUPABASE CODE_CHUNKS LOGGING: Verify metadata after extraction (first 3 docs)
                    if i < 3:
                        log_query.info(f"🔍 SUPABASE CODE_CHUNKS DOC {i+1} METADATA: filename='{metadata.get('filename', 'MISSING')}', page_number='{metadata.get('page_number', 'MISSING')}'")
                    
                    doc = Document(
                        page_content=row['content'],
                        metadata=metadata
                    )
                    code_docs.append(doc)
                
                # SUPABASE CODE_CHUNKS LOGGING: Final verification
                if code_docs:
                    docs_with_filename = sum(1 for d in code_docs if d.metadata.get('filename'))
                    docs_with_page = sum(1 for d in code_docs if (d.metadata.get('page_number') or d.metadata.get('page')))
                    log_query.info(f"🔍 SUPABASE CODE_CHUNKS VERIFICATION: {docs_with_filename}/{len(code_docs)} docs have filename, {docs_with_page}/{len(code_docs)} docs have page_number")
                    if docs_with_filename < len(code_docs):
                        log_query.error(f"🔍 SUPABASE CODE_CHUNKS ERROR: {len(code_docs) - docs_with_filename} docs are MISSING filename!")
                    if docs_with_page < len(code_docs):
                        log_query.error(f"🔍 SUPABASE CODE_CHUNKS ERROR: {len(code_docs) - docs_with_page} docs are MISSING page_number!")
                
                return code_docs
                
            except Exception as e:
                log_query.error(f"🔍 SUPABASE CODE_CHUNKS ERROR: Code hybrid search failed: {e}")
                import traceback
                log_query.error(f"🔍 SUPABASE CODE_CHUNKS ERROR: Traceback: {traceback.format_exc()}")
                # Fall back to simple similarity search
                try:
                    return vs_code.similarity_search(query, k=k)
                except Exception as e2:
                    log_query.error(f"🔍 SUPABASE CODE_CHUNKS ERROR: Fallback also failed: {e2}")
                    return []

        class SupabaseCodeHybrid:
            def hybrid_search(self, query: str, k: int = 8, keyword_weight: float = None) -> List[Document]:
                return supabase_code_hybrid_search(query, k, keyword_weight)

        code_hybrid_retriever = SupabaseCodeHybrid()
    else:
        raise ValueError("No code hybrid retriever available. Code vector store not initialized.")
    
    def code_search(query: str, k: int = 8) -> List[Document]:
        """Code hybrid search function"""
        
        # Get hybrid results
        fetch_count = k * 2  # Fetch more for better quality
        results = code_hybrid_retriever.hybrid_search(query, fetch_count)
        final = results[:k]
        return final

    return code_search

def make_coop_hybrid_retriever():
    """Create hybrid retriever (dense + keyword) for coop manual database"""
    
    # Supabase hybrid: dense vector + keyword search on coop table
    if SUPABASE_URL and SUPABASE_KEY and 'vs_coop' in globals() and vs_coop is not None:
        def supabase_coop_hybrid_search(query: str, k: int = 8, keyword_weight: float = None) -> List[Document]:
            """Enhanced Supabase hybrid search for coop manual database"""
            
            table_name = SUPA_COOP_TABLE
            
            try:
                _supa = create_client(SUPABASE_URL, SUPABASE_KEY)
                query_embedding = emb.embed_query(query)
                match_count = min(1000, k * 5)  # Deep search for better recall
                
                # Try to use RPC function if it exists, otherwise fall back to similarity search
                try:
                    result = _supa.rpc("match_coop_documents", {
                        'query_embedding': query_embedding,
                        'match_count': match_count
                    }).execute()
                    
                    # Convert HNSW result to rows for fusion
                    dense_rows = result.data or []
                    fused_rows = dense_rows[:k]
                except Exception as rpc_error:
                    # If RPC function doesn't exist, use similarity search directly
                    log_query.info(f"🔍 SUPABASE COOP_CHUNKS: RPC function not available, using similarity search: {rpc_error}")
                    return vs_coop.similarity_search(query, k=k)
                
                # Convert fused rows to Document objects
                coop_docs = []
                for i, row in enumerate(fused_rows):
                    # SUPABASE COOP_CHUNKS LOGGING: Log row structure from RPC (first row only)
                    if i == 0:
                        log_query.info(f"🔍 SUPABASE COOP_CHUNKS RPC ROW KEYS: {list(row.keys())}")
                        log_query.info(f"🔍 SUPABASE COOP_CHUNKS RPC ROW (first): filename={row.get('filename', 'NOT FOUND')}, page_number={row.get('page_number', 'NOT FOUND')}, has_metadata={bool(row.get('metadata'))}")
                        if row.get('metadata'):
                            log_query.info(f"🔍 SUPABASE COOP_CHUNKS RPC METADATA KEYS: {list(row.get('metadata', {}).keys())}")
                    
                    # Extract metadata - the RPC function returns fields inside metadata jsonb object
                    metadata = row.get('metadata', {}).copy() if isinstance(row.get('metadata'), dict) else {}
                    
                    # CRITICAL: Extract filename and page_number from metadata jsonb object
                    # The RPC function returns: id, content, metadata (jsonb), similarity
                    # All table columns (filename, page_number, etc.) are inside the metadata jsonb
                    if 'filename' in row:
                        metadata['filename'] = row['filename']
                        if i == 0:
                            log_query.info(f"🔍 SUPABASE COOP_CHUNKS: Extracted filename from top-level: '{row['filename']}'")
                    elif 'filename' in metadata:
                        if i == 0:
                            log_query.info(f"🔍 SUPABASE COOP_CHUNKS: Extracted filename from metadata: '{metadata['filename']}'")
                    else:
                        log_query.error(f"🔍 SUPABASE COOP_CHUNKS ERROR: filename NOT found in row (row keys: {list(row.keys())}, metadata keys: {list(metadata.keys())})")
                    
                    if 'page_number' in row:
                        metadata['page_number'] = row['page_number']
                        # Also set 'page' for compatibility
                        metadata['page'] = row['page_number']
                        if i == 0:
                            log_query.info(f"🔍 SUPABASE COOP_CHUNKS: Extracted page_number from top-level: '{row['page_number']}'")
                    elif 'page_number' in metadata:
                        # Also set 'page' for compatibility
                        if 'page' not in metadata:
                            metadata['page'] = metadata['page_number']
                        if i == 0:
                            log_query.info(f"🔍 SUPABASE COOP_CHUNKS: Extracted page_number from metadata: '{metadata['page_number']}'")
                    else:
                        # Check if it's in metadata with different name
                        if 'page' in metadata:
                            metadata['page_number'] = metadata['page']
                            if i == 0:
                                log_query.info(f"🔍 SUPABASE COOP_CHUNKS: Extracted page_number from 'page' field in metadata: '{metadata['page_number']}'")
                        else:
                            log_query.error(f"🔍 SUPABASE COOP_CHUNKS ERROR: page_number NOT found in row (row keys: {list(row.keys())}, metadata keys: {list(metadata.keys())})")
                    
                    # Copy other coop_chunks table fields from metadata
                    # Note: 'id' is at top level from RPC function
                    # Table only has: id, filename, page_number, file_path, content, embedding, created_at
                    if 'id' in row and 'id' not in metadata:
                        metadata['id'] = row['id']
                    
                    # Extract file_path from metadata (only field not already extracted)
                    # filename and page_number are already extracted above
                    if 'file_path' in metadata:
                        # Already in metadata from RPC function, no action needed
                        pass
                    elif 'file_path' in row:
                        metadata['file_path'] = row['file_path']
                    
                    # Extract created_at if available
                    if 'created_at' in metadata:
                        # Already in metadata from RPC function
                        pass
                    elif 'created_at' in row:
                        metadata['created_at'] = row['created_at']
                    
                    # Add similarity score
                    metadata['similarity_score'] = row.get('similarity', row.get('score', 0.0))
                    
                    # SUPABASE COOP_CHUNKS LOGGING: Verify metadata after extraction (first 3 docs)
                    if i < 3:
                        log_query.info(f"🔍 SUPABASE COOP_CHUNKS DOC {i+1} METADATA: filename='{metadata.get('filename', 'MISSING')}', page_number='{metadata.get('page_number', 'MISSING')}', file_path='{metadata.get('file_path', 'MISSING')}'")
                    
                    doc = Document(
                        page_content=row['content'],
                        metadata=metadata
                    )
                    coop_docs.append(doc)
                
                # SUPABASE COOP_CHUNKS LOGGING: Final verification
                if coop_docs:
                    docs_with_filename = sum(1 for d in coop_docs if d.metadata.get('filename'))
                    docs_with_page = sum(1 for d in coop_docs if (d.metadata.get('page_number') or d.metadata.get('page')))
                    docs_with_file_path = sum(1 for d in coop_docs if d.metadata.get('file_path'))
                    log_query.info(f"🔍 SUPABASE COOP_CHUNKS VERIFICATION: {docs_with_filename}/{len(coop_docs)} docs have filename, {docs_with_page}/{len(coop_docs)} docs have page_number, {docs_with_file_path}/{len(coop_docs)} docs have file_path")
                    if docs_with_filename < len(coop_docs):
                        log_query.error(f"🔍 SUPABASE COOP_CHUNKS ERROR: {len(coop_docs) - docs_with_filename} docs are MISSING filename!")
                    if docs_with_page < len(coop_docs):
                        log_query.error(f"🔍 SUPABASE COOP_CHUNKS ERROR: {len(coop_docs) - docs_with_page} docs are MISSING page_number!")
                    if docs_with_file_path < len(coop_docs):
                        log_query.warning(f"🔍 SUPABASE COOP_CHUNKS WARNING: {len(coop_docs) - docs_with_file_path} docs are MISSING file_path!")
                
                return coop_docs
                
            except Exception as e:
                log_query.error(f"🔍 SUPABASE COOP_CHUNKS ERROR: Coop hybrid search failed: {e}")
                import traceback
                log_query.error(f"🔍 SUPABASE COOP_CHUNKS ERROR: Traceback: {traceback.format_exc()}")
                # Fall back to simple similarity search
                try:
                    return vs_coop.similarity_search(query, k=k)
                except Exception as e2:
                    log_query.error(f"🔍 SUPABASE COOP_CHUNKS ERROR: Fallback also failed: {e2}")
                    return []

        class SupabaseCoopHybrid:
            def hybrid_search(self, query: str, k: int = 8, keyword_weight: float = None) -> List[Document]:
                return supabase_coop_hybrid_search(query, k, keyword_weight)

        coop_hybrid_retriever = SupabaseCoopHybrid()
    else:
        raise ValueError("No coop hybrid retriever available. Coop vector store not initialized.")
    
    def coop_search(query: str, k: int = 8) -> List[Document]:
        """Coop hybrid search function"""
        
        # Get hybrid results
        fetch_count = k * 2  # Fetch more for better quality
        results = coop_hybrid_retriever.hybrid_search(query, fetch_count)
        final = results[:k]
        return final

    return coop_search
#------------------------------------------------------------------------------------------------------------Supabase-Only Retrieval Functions----------
#-------------------------------------------------------------------------------Query planner controls which to use--------------------------
def mmr_rerank_supabase(docs: List[Document], query_embedding, lambda_=0.7, k=30) -> List[Document]:
    """Apply MMR (Maximal Marginal Relevance) to diversify Supabase results"""
    if len(docs) <= k:
        return docs
    
    selected, remaining = [], docs[:]
    
    while remaining and len(selected) < k:
        def mmr_score(doc_idx):
            doc = remaining[doc_idx]
            # Relevance score (similarity to query)
            sim_to_q = doc.metadata.get('similarity_score', 0.0)
            
            # Diversity score (max similarity to already selected docs)
            sim_to_sel = 0.0
            if selected:
                for sel_doc in selected:
                    # Simple diversity calculation based on project differences
                    sel_project = sel_doc.metadata.get('project_key', '')
                    doc_project = doc.metadata.get('project_key', '')
                    if sel_project != doc_project:
                        sim_to_sel += 0.1  # Boost diversity for different projects
            
            return lambda_ * sim_to_q - (1 - lambda_) * sim_to_sel
        
        # Find document with highest MMR score
        best_idx = max(range(len(remaining)), key=mmr_score)
        pick = remaining.pop(best_idx)
        selected.append(pick)
    
    return selected

def mmr_rerank_code(docs: List[Document], query_embedding, lambda_=0.9, k=30) -> List[Document]:
    """Apply MMR (Maximal Marginal Relevance) to diversify code results - less diversity, more relevance"""
    if len(docs) <= k:
        return docs
    
    selected, remaining = [], docs[:]
    
    while remaining and len(selected) < k:
        def mmr_score(doc_idx):
            doc = remaining[doc_idx]
            # Relevance score (similarity to query) - higher weight for code
            sim_to_q = doc.metadata.get('similarity_score', 0.0)
            
            # Diversity score (max similarity to already selected docs)
            # Less diversity penalty for code - code snippets from same source might be related
            sim_to_sel = 0.0
            if selected:
                for sel_doc in selected:
                    # Code docs use 'source' field (e.g., "concrete", "steel", "obc")
                    sel_source = sel_doc.metadata.get('source', '')
                    doc_source = doc.metadata.get('source', '')
                    
                    # Less diversity boost - code from same source might be relevant together
                    if sel_source != doc_source:
                        sim_to_sel += 0.05  # Smaller boost (0.05 vs 0.1 for projects)
            
            return lambda_ * sim_to_q - (1 - lambda_) * sim_to_sel
        
        # Find document with highest MMR score
        best_idx = max(range(len(remaining)), key=mmr_score)
        pick = remaining.pop(best_idx)
        selected.append(pick)
    
    return selected

def mmr_rerank_coop(docs: List[Document], query_embedding, lambda_=0.9, k=30) -> List[Document]:
    """Apply MMR (Maximal Marginal Relevance) to diversify coop results - less diversity, more relevance"""
    if len(docs) <= k:
        return docs
    
    selected, remaining = [], docs[:]
    
    while remaining and len(selected) < k:
        def mmr_score(doc_idx):
            doc = remaining[doc_idx]
            # Relevance score (similarity to query) - higher weight for coop
            sim_to_q = doc.metadata.get('similarity_score', 0.0)
            
            # Diversity score (max similarity to already selected docs)
            # Less diversity penalty for coop - pages from same manual might be related
            sim_to_sel = 0.0
            if selected:
                for sel_doc in selected:
                    # Coop docs use 'filename' field (coop_chunks table only has: id, filename, page_number, file_path, content, embedding, created_at)
                    sel_filename = sel_doc.metadata.get('filename', '')
                    doc_filename = doc.metadata.get('filename', '')
                    
                    # Less diversity boost - coop from same filename might be relevant together
                    if sel_filename != doc_filename:
                        sim_to_sel += 0.05  # Smaller boost (0.05 vs 0.1 for projects)
            
            return lambda_ * sim_to_q - (1 - lambda_) * sim_to_sel
        
        # Find document with highest MMR score
        best_idx = max(range(len(remaining)), key=mmr_score)
        pick = remaining.pop(best_idx)
        selected.append(pick)
    
    return selected

# Prompt templates - only create if LangChain is available
if HAS_LANGCHAIN and PromptTemplate is not None:
    SELF_GRADE_PROMPT = PromptTemplate.from_template(
        "Question:\n{q}\n\nChunk:\n{chunk}\n\n"
        "Is this chunk directly useful to answer the question? "
        "Answer 'yes' or 'no' only."
    )

    BATCH_GRADE_PROMPT = PromptTemplate.from_template(
        "Question:\n{q}\n\n"
        "Chunks:\n{chunks}\n\n"
        "Rate each chunk as 'yes' if it contains ANY information relevant to the question, even if indirect. "
        "Be generous - include chunks that mention related terms, project details, or context. "
        "For each chunk, respond ONLY with 'yes' or 'no', one per line, matching the order of chunks."
    )
else:
    SELF_GRADE_PROMPT = None
    BATCH_GRADE_PROMPT = None

# ---------------- Generic Plan Executor (operator toolbox) ----------------

def extract_date_filters_from_query(query: str, project_filter: Optional[str] = None, follow_up_context: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract date/time filters AND project-specific filters from query.
    Now handles: dates, specific project IDs, and follow-up context.
    """
    import re
    from datetime import datetime
    
    log_query.info(f"🗓️ SMART FILTER EXTRACTION: Analyzing query: '{query}'")
    
    q_lower = query.lower()
    filters = {}
    
    # 1. EXISTING: Month extraction (keep current logic)
    month_patterns = {
        r'\bjanuary\b': '01', r'\bjan\b': '01',
        r'\bfebruary\b': '02', r'\bfeb\b': '02',
        r'\bmarch\b': '03', r'\bmar\b': '03',
        r'\bapril\b': '04', r'\bapr\b': '04',
        r'\bmay\b': '05',
        r'\bjune\b': '06', r'\bjun\b': '06',
        r'\bjuly\b': '07', r'\bjul\b': '07',
        r'\baugust\b': '08', r'\baug\b': '08',
        r'\bseptember\b': '09', r'\bsep\b': '09', r'\bsept\b': '09',
        r'\boctober\b': '10', r'\boct\b': '10',
        r'\bnovember\b': '11', r'\bnov\b': '11',
        r'\bdecember\b': '12', r'\bdec\b': '12'
    }
    
    for pattern, month_num in month_patterns.items():
        if re.search(pattern, q_lower):
            filters['month'] = month_num
            log_query.info(f"🗓️ DATE EXTRACTION: Found month pattern '{pattern}' → {month_num}")
            break
    
    # Year extraction
    year_match = re.search(r'\b(20\d{2})\b', query)
    if year_match:
        year = year_match.group(1)[2:]  # Convert 2025 to 25
        filters['year'] = year
        log_query.info(f"🗓️ DATE EXTRACTION: Found year pattern '{year_match.group(1)}' → {year}")
    
    # Relative time patterns
    current_year = datetime.now().year % 100  # Get last 2 digits
    
    if re.search(r'\bthis year\b', q_lower):
        filters['year'] = str(current_year)
        log_query.info(f"🗓️ DATE EXTRACTION: Found 'this year' → {current_year}")
    elif re.search(r'\blast year\b', q_lower):
        filters['year'] = str(current_year - 1)
        log_query.info(f"🗓️ DATE EXTRACTION: Found 'last year' → {current_year - 1}")
    elif re.search(r'\bcurrent year\b', q_lower):
        filters['year'] = str(current_year)
        log_query.info(f"🗓️ DATE EXTRACTION: Found 'current year' → {current_year}")
    
    # Time range patterns
    if re.search(r'\bafter\s+(january|february|march|april|may|june|july|august|september|october|november|december)', q_lower):
        # Handle "after month" - would need more complex logic
        pass
    
    # 2. NEW: Specific project ID detection
    project_id = detect_project_filter(query)
    if project_id:
        filters['project_id'] = project_id
        log_query.info(f"🎯 SMART FILTER: Detected specific project: {project_id}")
    
    # 3. NEW: Follow-up context project detection
    if follow_up_context:
        context_project = detect_project_filter(follow_up_context)
        if context_project:
            filters['project_id'] = context_project
            log_query.info(f"🔄 SMART FILTER: Detected follow-up project: {context_project}")
    
    # 4. NEW: Explicit project filter from state
    if project_filter:
        filters['project_id'] = project_filter
        log_query.info(f"🎯 SMART FILTER: Using state project filter: {project_filter}")
    
    # 5. NEW: Revit file detection
    revit_patterns = [
        r'\brevit\b',
        r'\brevit file\b',
        r'\brevit model\b',
        r'\brevit definition\b',
        r'\brevit project\b',
        r'\bhas revit\b',
        r'\bwith revit\b',
        r'\brevit available\b',
        r'\brevit drawing\b',
        r'\brevit design\b'
    ]
    
    for pattern in revit_patterns:
        match = re.search(pattern, q_lower)
        if match:
            filters['has_revit'] = True
            matched_text = match.group(0)
            log_query.info(f"🏗️ REVIT DETECTION: ✅ Revit query identified!")
            log_query.info(f"🏗️ REVIT DETECTION: Pattern matched: '{pattern}' → Found: '{matched_text}' in query")
            log_query.info(f"🏗️ REVIT DETECTION: Will filter to has_revit=true in SQL query")
            break
    
    log_query.info(f"🗓️ SMART FILTER EXTRACTION: Final extracted filters: {filters}")
    return filters

def create_sql_project_filter(filters: Dict[str, Any]) -> Optional[Dict]:
    """
    Create SQL filter for Supabase based on date filters AND project-specific filters.
    Now handles: dates, specific projects, and follow-up context.
    """
    if not filters:
        return None
    
    conditions = []
    
    # EXISTING: Date-based filtering
    if 'year' in filters:
        year = filters['year']
        conditions.append(f"project_key.like.{year}-%")
    
    if 'month' in filters:
        month = filters['month']
        if 'year' in filters:
            conditions.append(f"project_key.like.{year}-{month}-%")
        else:
            conditions.append(f"project_key.like.%-{month}-%")
    
    # NEW: Project-specific filtering
    if 'project_id' in filters:
        project_id = filters['project_id']
        conditions.append(f"project_key.like.{project_id}")
        log_query.info(f"🎯 SQL FILTER: Adding exact project match: {project_id}")
    
    # NEW: Revit file filtering
    if 'has_revit' in filters and filters['has_revit']:
        conditions.append("has_revit.eq.true")
        log_query.info(f"🏗️ SQL FILTER CREATION: ✅ Revit filter condition added")
        log_query.info(f"🏗️ SQL FILTER CREATION: Condition: 'has_revit.eq.true' → Will filter page_chunks/smart_chunks to has_revit=true")
    
    if conditions:
        return {"and": conditions}
    
    return None

def smart_infer_project_limit(question: str) -> int:
    """Use LLM to intelligently determine project limit based on question intent"""
    try:
        response = llm_fast.invoke(PROJECT_LIMIT_PROMPT.format(question=question)).content.strip()
        log_query.info(f"🧠 SMART PROJECT LIMIT: LLM response for '{question[:50]}...': '{response}'")
        
        # Extract the number from the response
        import re
        match = re.search(r'-?\d+', response)
        if match:
            limit = int(match.group(0))
            log_query.info(f"🧠 SMART PROJECT LIMIT: Extracted limit: {limit}")
            return limit
        else:
            log_query.warning(f"🧠 SMART PROJECT LIMIT: No number found in response, using default: 5")
            return 5  # Default fallback
    except Exception as e:
        log_query.error(f"Smart project limit inference failed: {e}")
        return 5  # Default fallback

def _infer_n_from_q(q: str, default_n: int = 5) -> int:
    """Intelligently infer project count from question using LLM"""
    # First try the existing pattern matching for explicit numbers
    explicit_n = requested_project_count(q)
    if explicit_n:
        log_query.info(f"🎯 PROJECT LIMIT: Found explicit number in query: {explicit_n}")
        return explicit_n
    
    # If no explicit number, use LLM to understand intent
    smart_limit = -1
    if smart_limit == -1:
        final_limit = -1  # Unlimited
    elif smart_limit > 0:
        final_limit = -1  # Specific number
    else:
        final_limit = default_n  # Fallback (0 or other)
    log_query.info(f"🎯 PROJECT LIMIT: Final limit determined: {final_limit}")
    return final_limit

def _group_by_project_all(docs: List[Document]):
    m, order = {}, []
    for d in docs:
        md = d.metadata or {}
        p = md.get("drawing_number") or md.get("project_key")
        if not p:
            m_ = PROJECT_RE.search(d.page_content or "")
            p = m_.group(0) if m_ else None
        if not p: 
            continue
        if p not in m:
            m[p] = []
            order.append(p)
        m[p].append(d)
    return m, order

def _doc_matches_tokens(d: Document, tokens: List[str], regex: List[str]) -> bool:
    text = (d.page_content or "")
    title = (d.metadata or {}).get("title") or ""
    hay = f"{title}\n{text}"
    return (
        any(t.lower() in hay.lower() for t in (tokens or [])) or
        any(re.search(r, hay, re.I) for r in (regex or []))
    )

def _rank_projects_by_recency(docs: List[Document]) -> List[str]:
    proj_to_docs, _ = _group_by_project_all(docs)
    scored = []
    for p, chunks in proj_to_docs.items():
        md = chunks[0].metadata or {}
        y,m,d = 0,0,0
        for k in ("date","issue_date","signed_date"):
            v = md.get(k)
            if v:
                nums = re.findall(r"\d+", v)
                if len(nums) >= 2:
                    y,m = int(nums[0]), int(nums[1]); d = int(nums[2]) if len(nums)>2 else 1
                    break
        if (y,m) == (0,0):
            dt = date_from_project_id(p)
            if dt: y,m,d = dt.year, dt.month, dt.day
        scored.append(((y,m,d), p))
    scored.sort(reverse=True)
    return [p for _,p in scored]

def _rank_projects_by_accuracy_then_recency(docs: List[Document]) -> List[str]:
    """Rank projects by average similarity (higher = better)."""
    proj_scores = {}

    for d in docs:
        metadata = d.metadata or {}
        project = metadata.get("drawing_number") or metadata.get("project_key")
        if not project:
            continue

        sim = metadata.get("similarity_score", 0.0)
        if project not in proj_scores:
            proj_scores[project] = []
        proj_scores[project].append(sim)

    # Average similarity per project
    scored = [(sum(sims) / len(sims), proj) for proj, sims in proj_scores.items()]
    scored.sort(reverse=True)  # higher similarity = better ranking

    ranked_projects = [proj for _, proj in scored]

    log_query.info(f"🎯 SIMPLE RANKING: Final project order (by similarity): {ranked_projects}")
    return ranked_projects

def _limit_docs_to_projects(docs: List[Document], projects: List[str], per_project_cap: int = 3) -> List[Document]:
    proj_to_docs, _ = _group_by_project_all(docs)
    out = []
    for p in projects:
        out += (proj_to_docs.get(p, [])[:per_project_cap])
    return out

def _hybrid(project: Optional[str], sql_filters: Optional[Dict] = None, route: str = "smart"):
    return make_hybrid_retriever(project, sql_filters, route)

@(track_function if HAS_ENHANCED_LOGGER else lambda x: x)
def execute_plan(state: RAGState) -> dict:
    steps = (state.query_plan or {}).get("steps", [])
    if not steps:
        return {}  # nothing to do

    working: List[Document] = []
    selected_projects: List[str] = []

    log_query.info(f"🔧 EXECUTE_PLAN: Starting with {len(steps)} steps")

    for step_idx, s in enumerate(steps, 1):
        op = (s.get("op") or "").upper()
        args = s.get("args") or {}
        log_query.info(f"🔧 EXECUTING STEP {step_idx}: op='{op}', args={args}")

        if op == "RETRIEVE":
            qlist = args.get("queries") or [state.user_query]
            k = int(args.get("k", MAX_RETRIEVAL_DOCS))
            
            # Get data source preferences from state (database selection comes from frontend toggle)
            data_sources = state.data_sources or {"project_db": True, "code_db": False, "coop_manual": False}
            project_db_enabled = data_sources.get("project_db", True)
            code_db_enabled = data_sources.get("code_db", False)
            coop_db_enabled = data_sources.get("coop_manual", False)
            
            log_query.info(f"🔍 EXECUTE_PLAN RETRIEVE: project_db={project_db_enabled}, code_db={code_db_enabled}, coop_manual={coop_db_enabled}")
            
            # Initialize lists to store results from each database separately
            project_docs = []
            code_docs = []
            coop_docs = []
            
            # ========== PROJECT DATABASE RETRIEVAL ==========
            if project_db_enabled:
                # Router only runs for project_db, so data_route will be smart/large if project_db was enabled
                # If data_route is None, it means code_db only mode (router didn't run)
                if hasattr(state, 'data_route') and state.data_route:
                    route = state.data_route
                    if route == "smart":
                        k = min(k, MAX_SMART_RETRIEVAL_DOCS)
                    elif route == "large":
                        k = min(k, MAX_LARGE_RETRIEVAL_DOCS)
                    else:
                        k = min(k, MAX_SMART_RETRIEVAL_DOCS)  # fallback to smart
                        route = "smart"
                else:
                    # Router didn't run or failed - use smart as default for project_db
                    route = "smart"
                    k = min(k, MAX_SMART_RETRIEVAL_DOCS)
                    log_query.info("⚠️  Router value missing, defaulting to 'smart' for project_db")

                # Extract smart filters for SQL pre-filtering from the original query
                # Get previous query from session memory for follow-up context
                prior = SESSION_MEMORY.get(state.session_id, {})
                prev_query = prior.get("last_query")
                
                smart_filters = extract_date_filters_from_query(
                    state.user_query, 
                    project_filter=state.project_filter,
                    follow_up_context=prev_query  # Use session memory for follow-up context
                )
                sql_filters = create_sql_project_filter(smart_filters)
                
                # Store active filters in state for synthesis
                state.active_filters = smart_filters
                log_query.info(f"🏗️ EXECUTE_PLAN: Stored active_filters in state: {smart_filters}")
                
                if sql_filters:
                    log_query.info(f"🗓️ RETRIEVAL: Extracted smart filters {smart_filters} → SQL filters: {sql_filters}")
                    log_query.info(f"🗓️ RETRIEVAL: Will apply these filters to the user query")

                # Log when auto-filtering by project
                if state.project_filter:
                    log_query.info(f"Auto-filtering retrieval to project: {state.project_filter}")

                # Create retriever with pre-extracted SQL filters and route
                # Route should be smart/large if project_db is enabled (router should have run)
                route = state.data_route if (hasattr(state, 'data_route') and state.data_route) else "smart"
                retr = _hybrid(state.project_filter, sql_filters, route)
                # 🎯 LOG THE QUERY BEING USED FOR RETRIEVAL
                log_query.info(f"🎯 RETRIEVAL QUERY: '{state.user_query}'")
                # Disable subquery logic - only use original user query for vector search
                project_docs = retr(state.user_query, k=k)
                
                # Always apply MMR diversification after hybrid search
                if project_docs:
                    log_query.info(f"🎯 EMBEDDING QUERY: '{state.user_query}'")
                    query_emb = emb.embed_query(state.user_query)
                    project_docs = mmr_rerank_supabase(project_docs, query_emb, lambda_=0.7, k=len(project_docs))
                    log_query.info(f"🔧 Step {step_idx}/{len(steps)} (RETRIEVE PROJECT + MMR): {len(project_docs)} docs from project database")
                else:
                    log_query.info(f"🔧 Step {step_idx}/{len(steps)} (RETRIEVE PROJECT): {len(project_docs)} docs from project database")
            
            elif not project_db_enabled:
                log_query.info("⏭️  Project database disabled, skipping project retrieval")
            
            # ========== CODE DATABASE RETRIEVAL ==========
            if code_db_enabled:
                log_query.info(f"🔍 EXECUTE_PLAN CODE RETRIEVE: chunk_limit={MAX_CODE_RETRIEVAL_DOCS}")
                
                try:
                    if 'vs_code' in globals() and vs_code is not None:
                        log_query.info(f"   💻 Using CODE table: '{SUPA_CODE_TABLE}'")
                        # Use hybrid retriever for code database
                        code_retriever = make_code_hybrid_retriever()
                        code_docs = code_retriever(state.user_query, k=MAX_CODE_RETRIEVAL_DOCS)
                        log_query.info(f"   ✅ Retrieved {len(code_docs)} docs from code table")
                        
                        # Apply MMR diversification to code docs too
                        if code_docs:
                            query_emb = emb.embed_query(state.user_query)
                            code_docs = mmr_rerank_code(code_docs, query_emb, lambda_=0.9, k=len(code_docs))
                            log_query.info(f"🔧 Step {step_idx}/{len(steps)} (RETRIEVE CODE + MMR): {len(code_docs)} docs from code database")
                    else:
                        log_query.warning("   ⚠️  Code vector store not available (vs_code is None)")
                        code_docs = []
                        
                except Exception as e:
                    log_query.error(f"❌ Code database retrieve failed: {e}")
                    code_docs = []
            else:
                log_query.info("⏭️  Code database disabled, skipping code retrieval")
            
            # ========== COOP MANUAL DATABASE RETRIEVAL ==========
            if coop_db_enabled:
                log_query.info(f"🔍 EXECUTE_PLAN COOP RETRIEVE: chunk_limit={MAX_CODE_RETRIEVAL_DOCS}")
                
                try:
                    if 'vs_coop' in globals() and vs_coop is not None:
                        log_query.info(f"   📚 Using COOP table: '{SUPA_COOP_TABLE}'")
                        # Use hybrid retriever for coop database
                        coop_retriever = make_coop_hybrid_retriever()
                        coop_docs = coop_retriever(state.user_query, k=MAX_CODE_RETRIEVAL_DOCS)
                        log_query.info(f"   ✅ Retrieved {len(coop_docs)} docs from coop table")
                        
                        # Apply MMR diversification to coop docs too
                        if coop_docs:
                            query_emb = emb.embed_query(state.user_query)
                            coop_docs = mmr_rerank_coop(coop_docs, query_emb, lambda_=0.9, k=len(coop_docs))
                            log_query.info(f"🔧 Step {step_idx}/{len(steps)} (RETRIEVE COOP + MMR): {len(coop_docs)} docs from coop database")
                    else:
                        log_query.warning("   ⚠️  Coop vector store not available (vs_coop is None)")
                        coop_docs = []
                        
                except Exception as e:
                    log_query.error(f"❌ Coop database retrieve failed: {e}")
                    coop_docs = []
            else:
                log_query.info("⏭️  Coop database disabled, skipping coop retrieval")
            
            # ========== KEEP THEM SEPARATE ==========
            # Project docs go through the normal pipeline (stored in 'working')
            # Code docs are kept separate for independent processing
            # Coop docs are kept separate for independent processing
            working = project_docs  # Only project docs go through subsequent operations
            log_query.info(f"📊 RETRIEVAL COMPLETE: {len(project_docs)} project docs (will be processed), {len(code_docs)} code docs (kept separate), {len(coop_docs)} coop docs (kept separate)")
            
            # Store code and coop docs separately in state for later processing
            # We'll access them via state._code_docs and state._coop_docs in synthesis
            if code_docs:
                state._code_docs = code_docs
            if coop_docs:
                state._coop_docs = coop_docs

        elif op == "LIMIT_PROJECTS":
            n = args.get("n")
            if isinstance(n, str) and n.lower()=="infer":
                n = _infer_n_from_q(state.user_query, default_n=5)
            n = int(n or 5)
            
            # PRESERVE MMR ORDER: Extract distinct projects from MMR-ranked documents
            # This respects MMR's careful relevance + diversity selection
            selected_projects = []
            seen_projects = set()
            
            for doc in working:
                md = doc.metadata or {}
                project = md.get("drawing_number") or md.get("project_key")
                if project and project not in seen_projects:
                    selected_projects.append(project)
                    seen_projects.add(project)
                    # Stop early if we've reached the limit (unless unlimited)
                    if n != -1 and len(selected_projects) >= n:
                        break
            
            # Handle unlimited case (-1 indicates "all")
            if n == -1:
                log_query.info(f"🔍 UNLIMITED QUERY DETECTED: Using all {len(selected_projects)} available projects (in MMR order)")
            else:
                log_query.info(f"🎯 LIMIT_PROJECTS: Selected {len(selected_projects)} projects in MMR order: {selected_projects}")
            
            # Filter to only selected projects (Supabase already limited chunks per project)
            working = [d for d in working if
                      (d.metadata or {}).get("drawing_number") in selected_projects or
                      (d.metadata or {}).get("project_key") in selected_projects]
            log_query.info(f"🔧 Step {step_idx}/{len(steps)} (LIMIT_PROJECTS): {len(working)} docs, n={n}, selected={selected_projects}")
            
            # Fetch project metadata early (for selected projects only) - improves latency
            if selected_projects:
                log_query.info(f"📋 Fetching project metadata for {len(selected_projects)} selected projects...")
                project_metadata = fetch_project_metadata(selected_projects)
                state._project_metadata = project_metadata
                log_query.info(f"📋 Fetched metadata for {len(project_metadata)} projects")
            else:
                state._project_metadata = {}

        elif op == "EXTRACT":
            # We keep the docs; the 'target' hint is passed through to synthesis if you want.
            # You can put it into state.query_plan for the answer prompt to emphasize.
            state.query_plan["extract_target"] = args.get("target","")
            log_query.info(f"🔧 Step {step_idx}/{len(steps)} (EXTRACT): {len(working)} docs, target={args.get('target','')}")

        else:
            # unknown op → no-op
            log_query.info(f"🔧 Step {step_idx}/{len(steps)} (UNKNOWN OP '{op}'): {len(working)} docs")

    # SEMANTIC INTELLIGENCE: Capture execution intelligence
    execution_intelligence = {
        "operations_performed": [step.get("op", "") for step in steps],
        "selected_projects": selected_projects or state.selected_projects or [],
        "extract_targets": [step.get("args", {}).get("target", "") for step in steps if step.get("op") == "EXTRACT"],
        "doc_processing_flow": {
            "final_doc_count": len(working),
            "selected_project_count": len(selected_projects) if selected_projects else 0,
        },
        "data_sources_used": {
            "project_db": state.data_sources.get("project_db", True) if state.data_sources else True,
            "code_db": state.data_sources.get("code_db", False) if state.data_sources else False,
            "coop_manual": state.data_sources.get("coop_manual", False) if state.data_sources else False
        },
        "scope_refinement": "project_limited" if selected_projects else "open_scope",
        "timestamp": time.time()
    }
    
    # Store in state for later capture in SESSION_MEMORY
    state._execution_intelligence = execution_intelligence
    
    # Return dict updates
    log_query.info(f"🔧 EXECUTE_PLAN: Final result: {len(working)} project docs, {len(getattr(state, '_code_docs', []))} code docs, {len(getattr(state, '_coop_docs', []))} coop docs, selected_projects={selected_projects}")

    # Get code and coop docs if they were stored
    code_docs = getattr(state, '_code_docs', [])
    coop_docs = getattr(state, '_coop_docs', [])
    
    result = {
        "selected_projects": selected_projects or state.selected_projects or [],
        "retrieved_docs": (working or [])[:MAX_GRADED_DOCS],
        "active_filters": getattr(state, 'active_filters', None)  # Include active_filters in state update
    }
    
    # Add code docs separately if they exist
    if code_docs:
        result["retrieved_code_docs"] = code_docs[:MAX_GRADED_DOCS]
        log_query.info(f"📦 Returning {len(code_docs)} code docs in retrieved_code_docs from execute_plan")
    
    # Add coop docs separately if they exist
    if coop_docs:
        result["retrieved_coop_docs"] = coop_docs[:MAX_GRADED_DOCS]
        log_query.info(f"📦 Returning {len(coop_docs)} coop docs in retrieved_coop_docs from execute_plan")
    
    return result

#---------------------------------------------------Dimension Capture---------------------------------------------------
DIM_Q_RE = re.compile(r'(\d{1,4})(?:\s*(?:\'|’|ft)?)\s*[x×]\s*(\d{1,4})(?:\s*(?:\'|’|ft)?)', re.I)
DIM_DOC_RE = re.compile(r'(\d{1,4})(?:\s*(?:\'|’|ft)?)\s*[x×]\s*(\d{1,4})(?:\s*(?:\'|’|ft)?)', re.I)

def _abs_int(x: str) -> int:
    try: return int(re.sub(r'\D', '', x))
    except: return 10**9

def rerank_by_dimension_similarity(q: str, docs: List[Document]) -> List[Document]:
    m = DIM_Q_RE.search(q)
    if not m or not docs:
        return docs  # nothing to do

    q_w, q_l = _abs_int(m.group(1)), _abs_int(m.group(2))

    def best_err(text: str) -> int:
        best = None
        for a,b in DIM_DOC_RE.findall(text or ""):
            w, l = _abs_int(a), _abs_int(b)
            # consider swapped orientation too
            e1 = abs(w - q_w) + abs(l - q_l)
            e2 = abs(w - q_l) + abs(l - q_w)
            e = min(e1, e2)
            best = e if best is None else min(best, e)
        return best if best is not None else 10**9

    scored = [(best_err(d.page_content[:2000]), i, d) for i, d in enumerate(docs)]
    scored.sort(key=lambda t: (t[0], t[1]))  # smaller error first, stable by original order
    return [d for _,__,d in scored]

def self_grade(q: str, docs: List[Document]) -> List[Document]:
    if not docs:
        return []
    
    # Build numbered chunk list
    chunks_text = "\n\n".join([f"[{i}] {d.page_content[:500]}" for i, d in enumerate(docs, 1)])
    resp = _timeit("grader llm (batch)", llm_grader.invoke, BATCH_GRADE_PROMPT.format(q=q, chunks=chunks_text)).content.strip().lower()
    # One LLM call to grade all
    resp = llm_grader.invoke(BATCH_GRADE_PROMPT.format(q=q, chunks=chunks_text)).content.strip().lower()
    labels = [line.strip() for line in resp.splitlines() if line.strip()]
    
    # Keep docs marked "yes"
    keep = [d for d, lab in zip(docs, labels) if lab.startswith("y")]
    
    #Force key word matches and then the top ranked chunks
    return docs[:5] + keep[:MAX_GRADED_DOCS-5]

#__------------------------------------ENSURE # of Projects is correct - ie. if I ask for 5, i get 5 projects-------------------------------------------------------------------
_WORD_TO_NUM = {
    "one":1,"two":2,"three":3,"four":4,"five":5,"six":6,"seven":7,"eight":8,"nine":9,"ten":10
}

import re
def requested_project_count(q: str) -> Optional[int]:
    ql = q.lower()
    # numeric like "3 projects" / "top 3" / "give me 3"
    m = re.search(r'\b(?:top\s*)?(\d{1,2})\b\s*(?:projects?|examples?)', ql)
    if m: 
        return int(m.group(1))
    # words like "three projects"
    for w,n in _WORD_TO_NUM.items():
        if re.search(rf'\b{w}\b\s*(?:projects?|examples?)', ql):
            return n
    return None

from collections import OrderedDict, defaultdict
def pick_top_n_projects(docs: List[Document], n: int, max_docs: int) -> List[Document]:
    """
    Keep documents from the first N distinct projects (in current order),
    then flatten their chunks back, capped by max_docs.
    """
    # order projects as they appear
    proj_to_docs = defaultdict(list)
    proj_order = []
    for d in docs:
        proj = (d.metadata or {}).get("drawing_number") or (d.metadata or {}).get("project_key")
        if not proj: 
            continue
        if proj not in proj_to_docs:
            proj_order.append(proj)
        proj_to_docs[proj].append(d)

    chosen = proj_order[:max(0, n)]
    # Flatten, preserving original order, cap by max_docs to protect synthesis token budget
    out = []
    for p in chosen:
        out.extend(proj_to_docs[p])
        if len(out) >= max_docs:
            break
    return out[:max_docs]

# 5) Corrective RAG (self-check + one reformulation) ------------------------------------------------------------

if HAS_LANGCHAIN and PromptTemplate is not None:
    SUPPORT_PROMPT = PromptTemplate.from_template(
        "Question:\n{q}\n\nAnswer:\n{a}\n\nDocs:\n{ctx}\n\n"
        "Rate support 0.0-1.0 (float only)."
    )

    REFORMULATE_PROMPT = PromptTemplate.from_template(
        "Original question:\n{q}\n\n"
        "Given the following retrieved passages were insufficient, write THREE better search queries "
        "that is more specific and uses synonyms/technical terms relevant to structural drawings:\n\n"
        "{ctx}\n\n"
        "Return the query only."
        "If insufficient, expand with synonyms"
    )
else:
    SUPPORT_PROMPT = None
    REFORMULATE_PROMPT = None

FOLLOWUP_PROMPT = """
You are a strict classifier. Decide if the NEW QUESTION is a follow-up to the PRIOR QUESTION and response.
Rules:
- "follow-up" → The new question clearly depends on, references, or asks for more about the prior question/answer.
- "new" → The new question starts a fresh topic, introduces new dimensions, or shifts focus to something else.
Be conservative: only call it follow-up if it's explicit.

PRIOR QUESTION: {last_q}
PRIOR RESPONSE: {response}
NEW QUESTION: {new_q}

Examples of follow-ups:
- "What are the dimensions of the first project?" (after listing projects)
- "Tell me more about project 25-07-003" (after mentioning that project)
- "What about the second one?" (after listing multiple items)

Answer with one word only: follow-up OR new.
"""

if HAS_LANGCHAIN and PromptTemplate is not None:
    PROJECT_LIMIT_PROMPT = PromptTemplate.from_template(
        """Analyze this question and determine the appropriate number of projects to retrieve.

Question: {question}

Consider these scenarios:
- If the user asks for a specific number (e.g., "3 projects", "top 5"), return that number
- If the user asks for "all", "every", "list all", "count", "how many", return -1 (meaning unlimited/all)
- If the user asks for examples or general information, return 5 (default)
- If the user asks to compare projects or needs comprehensive coverage, return a larger number (10-20)

Return ONLY a single integer. Examples:
- "show me 3 floating slab projects" → 3
- "list all floating slab projects" → -1
- "how many projects have floating slabs" → -1
- "find me floating slab projects" → 5
- "compare floating slab projects" → 10

Answer:"""
    )
else:
    PROJECT_LIMIT_PROMPT = None

def support_score(q: str, answer: str, docs: List[Document]) -> float:
    ctx = "\n\n".join(d.page_content[:1000] for d in docs[:MAX_SUPPORT_DOCS])
    raw = llm_support.invoke(SUPPORT_PROMPT.format(q=q, a=answer, ctx=ctx)).content.strip()
    try:
        return float(raw)
    except:
        return 0.0

def reformulate(q: str, docs: List[Document]) -> str:
    ctx = "\n\n".join(d.page_content[:600] for d in docs[:MAX_ROUTER_DOCS])
    return llm_corrective.invoke(REFORMULATE_PROMPT.format(q=q, ctx=ctx)).content.strip()

# 6) Synthesis with Citations (drawings & code) ------------------------------------------------------------
if HAS_LANGCHAIN and PromptTemplate is not None:
    ANSWER_PROMPT = PromptTemplate.from_template(
    "You are a civil/structural assistant. Answer strictly from the provided context. "
    
    "COUNT QUESTIONS: If the user asks 'How many projects...' or 'Count the projects...', "
    "respond with ONLY the number followed by a brief explanation. "
    "Example: '5 projects have floating slabs.' "
    "List a defualt of 5 projects unless the user asks for more if they match the query\n\n"
    
    "DETAILED QUESTIONS: For all other questions, provide comprehensive details as usual.\n\n"
    
    "PROJECT CATEGORIZATION: "
    "You MUST categorize each project based on the categorization rules below. "
    "Use the project name, address, context clues, and drawing content to determine the category. "
    "- If the user query asks for a specific project type (e.g., 'residential projects', 'commercial buildings', 'farm projects', 'breweries'), "
    "  you MUST FILTER and ONLY include projects that match that category. "
    "- If the user doesn't specify a category, include all relevant projects but organize them by category. "
    "- Group projects by category in your answer when listing multiple projects.\n\n"
    
    "CATEGORIZATION RULES:\n"
    "{project_categories}\n\n"
    
    "When referring to a project, ALWAYS use the FULL project details provided in the context headers. "
    "Format: 'Project [NUMBER] - Project Name: [NAME], Project Address: [ADDRESS], City: [CITY]' "
    "Example: 'Project 25-08-005 - Project Name: Smith Residence, Project Address: 123 Main St, City: Toronto' "
    "If the context header doesn't include all fields, use only what's available. "
    "Quote values with units. "

    "CRITICAL INSTRUCTIONS: "
    "- For queries about specific equipment, features, or topics (like 'forklift extensions', 'concrete slabs', 'steel beams', etc.), you MUST list EVERY SINGLE project that matches the criteria. "
    "- If asked for 'all projects' or 'find all', you MUST list EVERY SINGLE project that matches the criteria. "
    "- Do not summarize, limit, or provide examples - be exhaustive and comprehensive. "
    "- If there are 5 matching projects, list all 5. If there are 10, list all 10. "
    "- If unsure, always provide multiple projects if available...if less, provide all projects that match the user's query "
    "- IMPORTANT: Apply category filtering FIRST - if user asks for 'residential projects', exclude non-residential projects even if they match other criteria\n\n"
    
    "SORTING INSTRUCTIONS: "
    "- When listing multiple projects, ALWAYS sort by date with NEWEST/MOST RECENT projects FIRST. "
    "- Project numbers encode the date in YY-MM-XXX format (e.g., 25-08-118 = August 2025, 24-12-003 = December 2024). "
    "- Higher YY-MM values = newer projects. Sort descending: 25-08-XXX before 25-07-XXX before 24-12-XXX. "
    "- ONLY use a different sort order if the question EXPLICITLY requests it (e.g., 'oldest first', 'alphabetically', 'by size'). "
    "- Default behavior: newest first by project number. "
    "- When organizing by category, sort by date WITHIN each category.\n\n"
    
    "CONVERSATION CONTEXT: "
    "- If this appears to be a follow-up question, use the conversation history below to understand references. "
    "- PRIORITIZE THE MOST RECENT EXCHANGE - unless the user explicitly says 'originally', 'the first question', 'earlier', assume they mean the most recent exchange. "
    "- Answer should still come ONLY from the provided context chunks below, not from conversation history. "
    "- Conversation history is just for understanding what the user is asking about.\n\n"
    "{conversation_context}\n\n"
    "Be comprehensive and exhaustive in your response.\n\n"
    "Question: {q}\n\n"
        "Context (numbered):\n{ctx}\n"
    )
else:
    ANSWER_PROMPT = None

if HAS_LANGCHAIN and PromptTemplate is not None:
    CODE_ANSWER_PROMPT = PromptTemplate.from_template(
    "You are an expert assistant for building codes and standards. "
    "Answer the question based on the following building code references and standards. "
    
    "CITATION REQUIREMENTS: "
    "- Include citations for key facts, requirements, values, and statements "
    "- When you mention a section, table, figure, equation, or requirement, cite the document and page number "
    "- Use inline citations in the format [Document: filename, Page: X] immediately after relevant facts "
    "- The citations will automatically become clickable links to open the documents at the specified pages "
    "- DO NOT include a '## References' section at the end - only use inline citations\n\n"
    
    "CITATION FORMAT: "
    "- Format: [Document: filename, Page: X] "
    "- The filename is shown in the context headers as 'Document: filename' - use it exactly as shown "
    "- The page number is shown in the context headers as 'Page: X' - use the exact page number "
    "- Example: 'The basic wind speed V is determined from Figure 26.5-1A [Document: ASCE7-10WindLoadingProvisionsStaticProcedure, Page: 3]' "
    "- Example: 'Section 26.6 specifies the wind directionality factor Kd [Document: ASCE7-10WindLoadingProvisionsStaticProcedure, Page: 21]' "
    "- Multiple citations: 'Wind loads are calculated using Chapter 27 [Document: filename1, Page: X] and Chapter 28 [Document: filename2, Page: Y]' "
    "- IMPORTANT: Use the exact filename and page number from the context headers - each citation will link to its specific page "
    "- Keep citations concise - the system will convert them to clean clickable links automatically\n\n"
    
    "ADDITIONAL RESOURCE REFERENCE: "
    "- If the question or your answer relates to any of the following topics, you MUST add this reference at the end of your response: "
    "  * Farm code or farm-related building codes "
    "  * Wood design or timber design "
    "  * Concrete design "
    "  * Steel design "
    "  * Ontario Building Code (OBC) "
    "- When any of these topics are relevant, append this line at the end of your response: "
    "  'For more information you can refer to <a href=\"https://sidian-bot.vercel.app/\" target=\"_blank\">Sidcode</a>' "
    "- IMPORTANT: Use fully-formed HTML anchor tag format (same as citations) so the link is clickable "
    "- Display text should be 'Sidcode' "
    "- This reference should be added as a separate paragraph at the very end, after all citations\n\n"
    
    "ANSWER STRUCTURE: "
    "1. Provide your answer with inline citations using the format [Document: filename, Page: X] where appropriate "
    "2. DO NOT add a References section - only use inline citations in brackets "
    "3. If the question relates to farm code, wood design, concrete design, steel design, or Ontario Building Code, add the reference link at the end\n\n"
    
    "CONTEXT FORMAT: "
    "- Each code reference in the context below is formatted as: '[N] Document: filename | Page: X | ...' "
    "- The filename appears after 'Document: ' (e.g., 'Document: ASCE7-10WindLoadingProvisionsStaticProcedure') "
    "- The page number appears after 'Page: ' (e.g., 'Page: 3') "
    "- Use these values in your citations - if a document appears multiple times with different page numbers, cite each page separately\n\n"
    
    "EXAMPLE ANSWER FORMAT: "
    "To determine wind loads for a building, you must first establish the basic wind speed V [Document: ASCE7-10WindLoadingProvisionsStaticProcedure, Page: 3]. "
    "This value is found in Figure 26.5-1A, B, or C depending on the risk category of the building [Document: ASCE7-10WindLoadingProvisionsStaticProcedure, Page: 3]. "
    "The wind directionality factor Kd is specified in Section 26.6 [Document: ASCE7-10WindLoadingProvisionsStaticProcedure, Page: 21]. "
    "Internal pressure coefficients (GCpi) are provided in Table 26.11-1 [Document: ASCE7-10WindLoadingProvisionsStaticProcedure, Page: 28].\n\n"
    
    "EXAMPLE WITH ADDITIONAL REFERENCE (for wood/concrete/steel/farm/OBC topics): "
    "The design requirements for wood structures are specified in Section 9.23 [Document: OBC2012, Page: 245]. "
    "For more information you can refer to <a href=\"https://sidian-bot.vercel.app/\" target=\"_blank\">Sidcode</a>\n\n"
    
    "CONVERSATION CONTEXT: "
    "- If this appears to be a follow-up question, use the conversation history below to understand references. "
    "- Answer should come from the provided code references below.\n\n"
    "{conversation_context}\n\n"
    "Question: {q}\n\n"
    "Code References (numbered):\n{ctx}\n"
    )
if HAS_LANGCHAIN and PromptTemplate is not None:
    COOP_ANSWER_PROMPT = PromptTemplate.from_template(
        "You are a patient and knowledgeable teacher helping someone learn from the Co-op Training Manual. "
    "Your role is to explain concepts clearly, provide context, and help the user understand the material. "
    "Answer the question based on the following training manual references. "
    
    "TEACHING STYLE: "
    "- Explain concepts step-by-step when appropriate "
    "- Provide context and background information to help understanding "
    "- Use clear, accessible language while maintaining accuracy "
    "- Break down complex topics into understandable parts "
    "- Use examples or analogies when helpful "
    "- Be encouraging and supportive in your tone "
    "- Think about it this way: help the user truly understand, not just get an answer\n\n"
    
    "CITATION REQUIREMENTS: "
    "- Include citations for key facts, procedures, requirements, and statements "
    "- When you mention a section, procedure, requirement, or concept, cite the document and page number "
    "- Use inline citations in the format [Document: filename, Page: X] immediately after relevant facts "
    "- The citations will automatically become clickable links to open the documents at the specified pages "
    "- DO NOT include a '## References' section at the end - only use inline citations\n\n"
    
    "CITATION FORMAT: "
    "- Format: [Document: filename, Page: X] "
    "- The filename is shown in the context headers as 'Document: filename' - use it exactly as shown "
    "- The page number is shown in the context headers as 'Page: X' - use the exact page number "
    "- Example: 'The safety procedure requires proper equipment inspection [Document: Co-op Training Manual 2024 (20250204) PDF.pdf, Page: 15]' "
    "- Example: 'Section 3.2 outlines the reporting requirements [Document: Co-op Training Manual 2024 (20250204) PDF.pdf, Page: 22]' "
    "- Multiple citations: 'Training covers both safety protocols [Document: filename, Page: X] and reporting procedures [Document: filename, Page: Y]' "
    "- IMPORTANT: Use the exact filename and page number from the context headers - each citation will link to its specific page "
    "- Keep citations concise - the system will convert them to clean clickable links automatically\n\n"
    
    "ANSWER STRUCTURE: "
    "1. Provide your answer with inline citations using the format [Document: filename, Page: X] where appropriate "
    "2. Explain concepts clearly and provide context to help understanding "
    "3. Break down complex topics into understandable parts "
    "4. DO NOT add a References section - only use inline citations in brackets\n\n"
    
    "CONTEXT FORMAT: "
    "- Each training manual reference in the context below is formatted as: '[N] Document: filename | Page: X | ...' "
    "- The filename appears after 'Document: ' (e.g., 'Document: Co-op Training Manual 2021') "
    "- The page number appears after 'Page: ' (e.g., 'Page: 15') "
    "- Use these values in your citations - if a document appears multiple times with different page numbers, cite each page separately\n\n"
    
    "EXAMPLE ANSWER FORMAT: "
    "Let me explain how the safety inspection process works. First, you'll need to check all equipment before use [Document: Co-op Training Manual 2021, Page: 15]. "
    "Think of this like a pre-flight checklist - it ensures everything is in working order before you start. "
    "The manual specifies that you should inspect for visible damage, test functionality, and verify all safety features are operational [Document: Co-op Training Manual 2021, Page: 15]. "
    "If you find any issues, Section 3.2 requires you to report them immediately to your supervisor [Document: Co-op Training Manual 2021, Page: 22]. "
    "This reporting step is crucial because it helps prevent accidents and ensures proper maintenance.\n\n"
    
    "CONVERSATION CONTEXT: "
    "- If this appears to be a follow-up question, use the conversation history below to understand references. "
    "- Answer should come from the provided training manual references below.\n\n"
    "{conversation_context}\n\n"
    "Question: {q}\n\n"
        "Training Manual References (numbered):\n{ctx}\n"
    )
else:
    COOP_ANSWER_PROMPT = None

from collections import defaultdict

@(track_function if HAS_ENHANCED_LOGGER else lambda x: x)
def synthesize(q: str, docs: List[Document], session_id: str = "default", stream: bool = False, project_metadata: Optional[Dict[str, Dict[str, str]]] = None, code_docs: Optional[List[Document]] = None, use_code_prompt: bool = False, coop_docs: Optional[List[Document]] = None, use_coop_prompt: bool = False, active_filters: Optional[Dict[str, Any]] = None):
    """
    Group docs by project, use pre-fetched metadata (or fetch if not provided), synthesize answer.

    Args:
        q: User question
        docs: Retrieved documents (project documents)
        session_id: Session identifier
        stream: If True, returns generator yielding chunks. If False (default), returns complete answer.
        project_metadata: Optional pre-fetched project metadata dict. If None, will fetch for unique projects in docs.
        code_docs: Optional list of code documents to include in synthesis (no project metadata needed).
        use_code_prompt: If True, use CODE_ANSWER_PROMPT for code-focused answers.
        coop_docs: Optional list of coop manual documents to include in synthesis (no project metadata needed).
        use_coop_prompt: If True, use COOP_ANSWER_PROMPT for teacher-style coop answers.

    Returns:
        If stream=False: Tuple[str, List[Dict]] - (answer, citations)
        If stream=True: Generator yielding (chunk, citations_on_first_chunk)
    """
    # DEBUG: Log function entry
    log_query.info(f"🔍 SYNTHESIS DEBUG: synthesize() called - use_code_prompt={use_code_prompt}, use_coop_prompt={use_coop_prompt}, code_docs={len(code_docs) if code_docs else 0}, coop_docs={len(coop_docs) if coop_docs else 0}, docs={len(docs)}")
    log_query.info(f"🔍 SYNTHESIS DEBUG: active_filters={active_filters}")
    if code_docs:
        log_query.info(f"🔍 SYNTHESIS DEBUG: First code_doc metadata: {list(code_docs[0].metadata.keys()) if code_docs[0].metadata else 'NO METADATA'}")
        if code_docs[0].metadata:
            log_query.info(f"🔍 SYNTHESIS DEBUG: First code_doc filename: {code_docs[0].metadata.get('filename', 'MISSING')}")
            log_query.info(f"🔍 SYNTHESIS DEBUG: First code_doc page_number: {code_docs[0].metadata.get('page_number', 'MISSING')}")
    if coop_docs:
        log_query.info(f"🔍 SYNTHESIS DEBUG: First coop_doc metadata: {list(coop_docs[0].metadata.keys()) if coop_docs[0].metadata else 'NO METADATA'}")
        if coop_docs[0].metadata:
            log_query.info(f"🔍 SYNTHESIS DEBUG: First coop_doc filename: {coop_docs[0].metadata.get('filename', 'MISSING')}")
            log_query.info(f"🔍 SYNTHESIS DEBUG: First coop_doc page_number: {coop_docs[0].metadata.get('page_number', 'MISSING')}")

    # Synthesis input preparation

    grouped = defaultdict(list)
    cites = []
    unique_projects = set()

    for i, d in enumerate(docs[:MAX_SYNTHESIS_DOCS], 1):
        md = d.metadata or {}
        proj  = md.get("drawing_number") or md.get("project_key") or "?"
        page  = md.get("page_id") or md.get("page") or "?"
        title = md.get("title") or ""

        # Collect unique project IDs
        if proj and proj != "?":
            unique_projects.add(proj)

        # Derive date from metadata or project id
        derived_date = date_from_project_id(proj)
        date_str = (
            md.get("date")
            or md.get("issue_date")
            or md.get("signed_date")
            or (derived_date.isoformat() if derived_date else "")
        )

        # Store citations
        cites.append({
            "project": proj,
            "page": page,
            "title": title,
            "date": date_str,
            "bundle": md.get("bundle_file"),
            "chunk_index": md.get("chunk_index"),
        })

        # Group by project
        grouped[proj].append(
            f"[{i}] (proj {proj}, page {page}, date {date_str}) {title}\n{d.page_content}"
        )

    # Fetch metadata from Supabase for ALL unique projects (if not pre-fetched)
    if project_metadata is None:
        project_metadata = fetch_project_metadata(list(unique_projects))
    else:
        # Ensure we have metadata for all unique projects (fallback fetch if missing)
        missing_projects = [p for p in unique_projects if p not in project_metadata]
        if missing_projects:
            additional_metadata = fetch_project_metadata(missing_projects)
            project_metadata.update(additional_metadata)

    # Build grouped context with enriched project information
    lines = []
    for proj, chunks in grouped.items():
        # Get metadata if available from Supabase
        meta = project_metadata.get(proj, {})
        proj_name = meta.get("name", "")
        proj_addr = meta.get("address", "")
        proj_city = meta.get("city", "")

        # Format project header with full details
        if proj_name and proj_addr and proj_city:
            proj_header = f"### Project {proj} - Project Name: {proj_name}, Project Address: {proj_addr}, City: {proj_city}"
        elif proj_name and proj_addr:
            proj_header = f"### Project {proj} - Project Name: {proj_name}, Project Address: {proj_addr}"
        elif proj_name:
            proj_header = f"### Project {proj} - Project Name: {proj_name}"
        else:
            proj_header = f"### Project {proj}"

        lines.append(proj_header + "\n" + "\n\n".join(chunks))

    ctx = "\n\n".join(lines)

    # Format code docs (if any) - include their own metadata but no project metadata
    if code_docs:
        code_lines = []
        code_lines.append("\n\n### Code References")
        
        # SUPABASE CODE_CHUNKS LOGGING: Log metadata before formatting (using log_query for visibility)
        log_query.info(f"🔍 SUPABASE CODE_CHUNKS SYNTHESIS: Formatting {len(code_docs)} code documents")
        for i, cd in enumerate(code_docs[:3], 1):  # Log first 3
            md = cd.metadata or {}
            log_query.info(f"🔍 SUPABASE CODE_CHUNKS SYNTHESIS DOC {i} METADATA: filename='{md.get('filename', 'MISSING')}', page_number='{md.get('page_number', 'MISSING')}', page='{md.get('page', 'MISSING')}'")
        
        for i, cd in enumerate(code_docs[:MAX_SYNTHESIS_DOCS], 1):
            md = cd.metadata or {}
            filename = md.get("filename", "")
            source = md.get("source", "unknown")
            section = md.get("section", "")
            title = md.get("title", "")
            page = md.get("page", "")
            page_number = md.get("page_number", "")
            
            # Use page_number if available, otherwise page
            final_page = page_number or page
            
            # SUPABASE CODE_CHUNKS LOGGING: Error if missing (using log_query)
            if not filename:
                log_query.error(f"🔍 SUPABASE CODE_CHUNKS SYNTHESIS DOC {i} ERROR: filename is MISSING! Available metadata keys: {list(md.keys())}")
            if not final_page:
                log_query.error(f"🔍 SUPABASE CODE_CHUNKS SYNTHESIS DOC {i} ERROR: page_number is MISSING! Available metadata keys: {list(md.keys())}")
            
            # Format code chunk header with source metadata (filename FIRST for visibility)
            code_header_parts = [f"[{i}]"]
            if filename:
                code_header_parts.append(f"Document: {filename}")
            else:
                # Fallback to source if filename missing
                if source:
                    code_header_parts.append(f"Document: {source}")
            
            if source and source != filename:  # Don't duplicate if source == filename
                code_header_parts.append(f"Source: {source}")
            if section:
                code_header_parts.append(f"Section: {section}")
            if title:
                code_header_parts.append(f"Title: {title}")
            if final_page:
                code_header_parts.append(f"Page: {final_page}")
            
            code_header = " | ".join(code_header_parts)
            code_lines.append(f"{code_header}\n{cd.page_content}")
            
            # SUPABASE CODE_CHUNKS LOGGING: Log formatted header for first 3 (using log_query)
            if i <= 3:
                log_query.info(f"🔍 SUPABASE CODE_CHUNKS SYNTHESIS DOC {i} FORMATTED HEADER: {code_header}")
                log_query.info(f"🔍 SUPABASE CODE_CHUNKS SYNTHESIS DOC {i} CONTENT PREVIEW: {cd.page_content[:200]}...")
            
            # Add citation for code docs (different structure - no project)
            cites.append({
                "project": None,  # Code docs don't have projects
                "filename": filename or source,  # Use filename or fallback to source
                "page": final_page,
                "page_number": final_page,  # Also include page_number for compatibility
                "file_path": md.get("file_path", ""),  # Include file_path for file opening
                "title": title or section or source,
                "date": None,  # Code docs don't have dates
                "source": source,
                "section": section,
                "chunk_index": md.get("chunk_index"),
            })
        
        ctx = ctx + "\n\n" + "\n\n".join(code_lines)
        
        # SUPABASE CODE_CHUNKS LOGGING: Log context sample (using log_query)
        if len(code_lines) > 1:
            log_query.info(f"🔍 SUPABASE CODE_CHUNKS CONTEXT SAMPLE (first reference sent to LLM):\n{code_lines[1][:500]}...")
            log_query.info(f"🔍 SUPABASE CODE_CHUNKS FULL FIRST REFERENCE:\n{code_lines[1]}")

    # Format coop docs (if any) - include their own metadata but no project metadata
    if coop_docs:
        coop_lines = []
        coop_lines.append("\n\n### Training Manual References")
        
        # SUPABASE COOP_CHUNKS LOGGING: Log metadata before formatting (using log_query for visibility)
        log_query.info(f"🔍 SUPABASE COOP_CHUNKS SYNTHESIS: Formatting {len(coop_docs)} coop documents")
        for i, cd in enumerate(coop_docs[:3], 1):  # Log first 3
            md = cd.metadata or {}
            log_query.info(f"🔍 SUPABASE COOP_CHUNKS SYNTHESIS DOC {i} METADATA: filename='{md.get('filename', 'MISSING')}', page_number='{md.get('page_number', 'MISSING')}', page='{md.get('page', 'MISSING')}'")
        
        for i, cd in enumerate(coop_docs[:MAX_SYNTHESIS_DOCS], 1):
            md = cd.metadata or {}
            filename = md.get("filename", "")
            page = md.get("page", "")
            page_number = md.get("page_number", "")
            file_path = md.get("file_path", "")
            
            # Use page_number if available, otherwise page
            final_page = page_number or page
            
            # SUPABASE COOP_CHUNKS LOGGING: Error if missing (using log_query)
            if not filename:
                log_query.error(f"🔍 SUPABASE COOP_CHUNKS SYNTHESIS DOC {i} ERROR: filename is MISSING! Available metadata keys: {list(md.keys())}")
            if not final_page:
                log_query.error(f"🔍 SUPABASE COOP_CHUNKS SYNTHESIS DOC {i} ERROR: page_number is MISSING! Available metadata keys: {list(md.keys())}")
            
            # Format coop chunk header with filename and page (simplified - no source/section/title)
            coop_header_parts = [f"[{i}]"]
            if filename:
                coop_header_parts.append(f"Document: {filename}")
            if final_page:
                coop_header_parts.append(f"Page: {final_page}")
            
            coop_header = " | ".join(coop_header_parts)
            coop_lines.append(f"{coop_header}\n{cd.page_content}")
            
            # SUPABASE COOP_CHUNKS LOGGING: Log formatted header for first 3 (using log_query)
            if i <= 3:
                log_query.info(f"🔍 SUPABASE COOP_CHUNKS SYNTHESIS DOC {i} FORMATTED HEADER: {coop_header}")
                log_query.info(f"🔍 SUPABASE COOP_CHUNKS SYNTHESIS DOC {i} CONTENT PREVIEW: {cd.page_content[:200]}...")
            
            # Add citation for coop docs (simplified - only fields that exist in table)
            cites.append({
                "project": None,  # Coop docs don't have projects
                "filename": filename,  # Use filename (required field)
                "page": final_page,
                "page_number": final_page,  # Also include page_number for compatibility
                "file_path": file_path,  # Include file_path for file opening
                "title": filename,  # Use filename as title (no separate title field)
                "date": None,  # Coop docs don't have dates
                "source": None,  # No source field in table
                "section": None,  # No section field in table
                "chunk_index": md.get("chunk_index"),
            })
        
        ctx = ctx + "\n\n" + "\n\n".join(coop_lines)
        
        # SUPABASE COOP_CHUNKS LOGGING: Log context sample (using log_query)
        if len(coop_lines) > 1:
            log_query.info(f"🔍 SUPABASE COOP_CHUNKS CONTEXT SAMPLE (first reference sent to LLM):\n{coop_lines[1][:500]}...")
            log_query.info(f"🔍 SUPABASE COOP_CHUNKS FULL FIRST REFERENCE:\n{coop_lines[1]}")

    # Context is ready for LLM

    # Get conversation context for synthesis (last 3 Q&A pairs)
    conversation_context = get_conversation_context(session_id, max_exchanges=3)
    
    # Build filter context message if filters are active
    filter_context = ""
    if active_filters:
        filter_messages = []
        if active_filters.get('has_revit'):
            filter_messages.append(
                "CRITICAL FILTER INFORMATION: "
                "All projects in the retrieved context have Revit files available (has_revit=true). "
                "The user's query specifically requested projects with Revit files. "
                "You MUST acknowledge this filter and list all projects from the context, "
                "explicitly stating that they all have Revit files available. "
                "Do NOT say that the context doesn't mention Revit - the filter ensures all retrieved projects have Revit files."
            )
        # Add more filter messages here as needed in the future
        
        if filter_messages:
            filter_context = "\n\n" + "\n\n".join(filter_messages) + "\n\n"
            log_query.info(f"🏗️ SYNTHESIS: Adding filter context to prompt: {filter_context}")
    
    # Select appropriate prompt based on content type (coop takes priority, then code, then default)
    if use_coop_prompt:
        prompt_template = COOP_ANSWER_PROMPT
    elif use_code_prompt:
        prompt_template = CODE_ANSWER_PROMPT
    else:
        prompt_template = ANSWER_PROMPT
    
    # DEBUG: Log what's being sent to LLM for code/coop answers
    if use_code_prompt and code_docs:
        log_query.info(f"🔍 CODE ANSWER DEBUG: Using CODE_ANSWER_PROMPT with model {SYNTHESIS_MODEL}")
        log_query.info(f"🔍 CODE ANSWER DEBUG: Context length={len(ctx)} chars")
        # Find Code References section in context
        if "### Code References" in ctx:
            code_ref_start = ctx.find("### Code References")
            code_ref_section = ctx[code_ref_start:code_ref_start+2000]
            log_query.info(f"🔍 CODE ANSWER DEBUG: Code References section (first 2000 chars):\n{code_ref_section}...")
        # Check if prompt contains citation instructions
        prompt_preview = str(prompt_template.template)[:500]
        if "CITATION" in prompt_preview or "citation" in prompt_preview:
            log_query.info(f"🔍 CODE ANSWER DEBUG: ✅ Prompt contains citation instructions")
    
    if use_coop_prompt and coop_docs:
        log_query.info(f"🔍 COOP ANSWER DEBUG: Using COOP_ANSWER_PROMPT with model {SYNTHESIS_MODEL}")
        log_query.info(f"🔍 COOP ANSWER DEBUG: Context length={len(ctx)} chars")
        # Find Training Manual References section in context
        if "### Training Manual References" in ctx:
            coop_ref_start = ctx.find("### Training Manual References")
            coop_ref_section = ctx[coop_ref_start:coop_ref_start+2000]
            log_query.info(f"🔍 COOP ANSWER DEBUG: Training Manual References section (first 2000 chars):\n{coop_ref_section}...")
        # Check if prompt contains citation instructions
        prompt_preview = str(prompt_template.template)[:500]
        if "CITATION" in prompt_preview or "citation" in prompt_preview:
            log_query.info(f"🔍 COOP ANSWER DEBUG: ✅ Prompt contains citation instructions")

    # Synthesize answer (streaming or non-streaming)
    # Format prompt with categories for project prompts (not code or coop)
    if not use_coop_prompt and not use_code_prompt:
        # Project prompt - include categorization rules
        prompt_kwargs = {
            "q": q,
            "ctx": ctx,
            "conversation_context": (conversation_context or "(No prior conversation)") + filter_context,
            "project_categories": PROJECT_CATEGORIES
        }
    else:
        # Code or coop prompt - no categories needed
        prompt_kwargs = {
            "q": q,
            "ctx": ctx,
            "conversation_context": (conversation_context or "(No prior conversation)") + filter_context
        }
    
    # ALWAYS LOG: Chunks being sent to LLM
    total_chunks = len(docs) + (len(code_docs) if code_docs else 0) + (len(coop_docs) if coop_docs else 0)
    prompt_type = "COOP" if use_coop_prompt else ("CODE" if use_code_prompt else "PROJECT")
    print(f"📤 SENDING TO LLM: {total_chunks} chunks | Type: {prompt_type} | Context: {len(ctx)} chars")
    
    if stream:
        # Streaming mode: return generator
        def stream_generator():
            first_chunk = True
            for chunk in llm_synthesis.stream(prompt_template.format(**prompt_kwargs)):
                if chunk.content:
                    if first_chunk:
                        yield (chunk.content, cites)
                        first_chunk = False
                    else:
                        yield chunk.content
        return stream_generator()
    else:
        # Non-streaming mode (original behavior)
        formatted_prompt = prompt_template.format(**prompt_kwargs)
        
        # DEBUG: Log before LLM call for code answers
        if use_code_prompt and code_docs:
            log_query.info(f"🔍 CODE ANSWER DEBUG: Calling LLM with {len(code_docs)} code docs")
            # Log a sample of the formatted prompt to verify format
            log_query.info(f"🔍 CODE ANSWER DEBUG: Formatted prompt length={len(formatted_prompt)} chars")
            # Check if context has Document: and Page: in it
            if "Document:" in ctx and "Page:" in ctx:
                log_query.info(f"🔍 CODE ANSWER DEBUG: ✅ Context contains 'Document:' and 'Page:' fields")
            else:
                log_query.error(f"🔍 CODE ANSWER DEBUG: ❌ Context does NOT contain 'Document:' or 'Page:' fields!")
        
        ans = llm_synthesis.invoke(formatted_prompt).content.strip()
        
        # DEBUG: Log LLM response for code/coop answers
        if use_code_prompt and code_docs:
            log_query.info(f"🔍 CODE ANSWER DEBUG: LLM response length={len(ans)} chars")
            # Check if response contains citations
            has_inline_citations = "[Document:" in ans
            has_references = "## References" in ans or "References" in ans.lower()
            log_query.info(f"🔍 CODE ANSWER DEBUG: Response has inline citations [Document:]: {has_inline_citations}")
            log_query.info(f"🔍 CODE ANSWER DEBUG: Response has References section: {has_references}")
            if not has_inline_citations:
                log_query.error(f"🔍 CODE ANSWER DEBUG: ⚠️ WARNING: LLM response does NOT contain inline citations!")
                # Log first 1000 chars of response to see what we got
                log_query.info(f"🔍 CODE ANSWER DEBUG: Response preview (first 1000 chars):\n{ans[:1000]}")
            else:
                # Log a sample of citations found
                import re
                citation_matches = re.findall(r'\[Document:[^\]]+\]', ans)
                if citation_matches:
                    log_query.info(f"🔍 CODE ANSWER DEBUG: Found {len(citation_matches)} citations: {citation_matches[:5]}")
        
        if use_coop_prompt and coop_docs:
            log_query.info(f"🔍 COOP ANSWER DEBUG: LLM response length={len(ans)} chars")
            # Check if response contains citations
            has_inline_citations = "[Document:" in ans
            has_references = "## References" in ans or "References" in ans.lower()
            log_query.info(f"🔍 COOP ANSWER DEBUG: Response has inline citations [Document:]: {has_inline_citations}")
            log_query.info(f"🔍 COOP ANSWER DEBUG: Response has References section: {has_references}")
            if not has_inline_citations:
                log_query.error(f"🔍 COOP ANSWER DEBUG: ⚠️ WARNING: LLM response does NOT contain inline citations!")
                # Log first 1000 chars of response to see what we got
                log_query.info(f"🔍 COOP ANSWER DEBUG: Response preview (first 1000 chars):\n{ans[:1000]}")
            else:
                # Log a sample of citations found
                import re
                citation_matches = re.findall(r'\[Document:[^\]]+\]', ans)
                if citation_matches:
                    log_query.info(f"🔍 COOP ANSWER DEBUG: Found {len(citation_matches)} citations: {citation_matches[:5]}")
        
        return ans, cites

# 7) Graph Nodes (Plan → Route → Retrieve → Grade → Synthesize → Correct)  ------------------------------------------------------------
# NOTE: Nodes accept RAGState but RETURN dicts - LangGraph merges dict updates into state


if HAS_LANGCHAIN and PromptTemplate is not None:
    PLANNER_PROMPT = PromptTemplate.from_template(
        """You produce an executable query plan (a sequence of ops) for a RAG system over engineering drawings.

You have these GENERIC OPS (compose them as needed):
- RETRIEVE(queries, k)                             # query vector+keyword hybrid retriever (automatically includes MMR diversification for relevance)
- EXTRACT(target)                                   # synthesis focuses on 'target' using ALL retrieved content
- LIMIT_PROJECTS(n)                                 # after synthesis, keep docs from the first n distinct projects

Guidelines:
- Break the user question into steps using these ops.
- Use domain synonyms in queries/tokens (provide them explicitly).
- If the user mentions a specific month (e.g., "in March", "March projects"), note it but don't add metadata filters unless the table supports them.
- If the user asks for a specific number of projects, include LIMIT_PROJECTS(N).
- If the user asks for comprehensive coverage, counting, or "all" projects, use LIMIT_PROJECTS("infer") which will intelligently determine the appropriate limit.
- For general queries without specific requirements, use LIMIT_PROJECTS("infer") with default of 20.
- Use EXTRACT first to synthesize ALL retrieved content before limiting projects
- Use LIMIT_PROJECTS after synthesis to select the most relevant projects
- IMPORTANT: Recency sorting is handled automatically by the LLM during synthesis - documents are already ranked by relevance (via MMR), and the LLM will organize the response by recency when listing projects. Do NOT add RANK_BY_RECENCY operation.

CONVERSATION CONTEXT (if provided):
- Use conversation history below ONLY to resolve ambiguous references like "the second one", "that project", "it", etc.
- PRIORITIZE THE MOST RECENT EXCHANGE - unless the user explicitly mentions "originally", "the first question", "earlier", assume they mean the most recent exchange.
- DO NOT restrict retrieval based on prior projects - always search the full database unless the question explicitly asks about a specific prior project.
- Example 1: "Tell me about the 2nd project" → Look up which project that is from the MOST RECENT answer, then search specifically for it.
- Example 2: "Find me more projects with the same size as the 2nd project" → Look up the 2nd project's dimensions from the MOST RECENT answer, then search ALL projects for that size.
- Expand queries with concrete details (dimensions, features) extracted from the MOST RECENT conversation context, not just project IDs.

{conversation_context}

CRITICAL: Return ONLY valid JSON, no explanations or preamble. Start your response with {{ and end with }}.

JSON Format:
{{
  "reasoning": "...",
  "steps": [
    {{"op":"RETRIEVE","args":{{"queries":["...","..."]}}}},
    {{"op":"EXTRACT","args":{{"target":"..."}}}},
    {{"op":"LIMIT_PROJECTS","args":{{"n":"infer"}}}}
  ]
}}

PLAYBOOK:
{playbook}

CURRENT QUESTION:
{q}

Remember: Return ONLY the JSON object, nothing else.
"""
)

planner_llm = ChatOpenAI(model=FAST_MODEL, temperature=0, response_format={"type": "json_object"}) if HAS_LANGCHAIN and ChatOpenAI is not None else None  # Force JSON output

def validate_project_number(p: str) -> bool:
    return bool(PROJECT_RE.fullmatch(p))


def _normalize_plan(raw: dict, fallback_q: str) -> dict:
    """
    Force a stable schema for the UI and executor.

    Returns:
      {
        "reasoning": str,
        "steps": [ { "op": str, "args": dict } ],
        "subqueries": [str]   # derived convenience field for UI
      }
    """
    plan = {} if not isinstance(raw, dict) else dict(raw)

    # 1) reasoning
    reasoning = plan.get("reasoning")
    if not isinstance(reasoning, str):
        reasoning = "No explicit reasoning provided."

    # 2) steps -> list of {op,args}
    steps_in = plan.get("steps") or []
    norm_steps = []
    for s in steps_in if isinstance(steps_in, list) else []:
        if not isinstance(s, dict):
            continue
        op = (s.get("op") or "").strip().upper()
        args = s.get("args") or {}
        if not isinstance(args, dict):
            args = {}
        if op:
            norm_steps.append({"op": op, "args": args})

    # minimal fallback so executor still works
    if not norm_steps:
        norm_steps = [
            {"op": "RETRIEVE", "args": {"queries": [fallback_q], "k": 333}},
        ]

    # 3) subqueries (derived for UI, safe even if absent)
    subqs = []
    for s in norm_steps:
        ql = s["args"].get("queries")
        if isinstance(ql, list):
            for q in ql:
                if isinstance(q, str) and q.strip():
                    subqs.append(q.strip())
    if not subqs:
        subqs = [fallback_q]

    return {"reasoning": reasoning, "steps": norm_steps, "subqueries": subqs}

def _extract_complexity_from_reasoning(reasoning: str) -> str:
    """Extract complexity assessment from planner reasoning."""
    reasoning_lower = reasoning.lower()
    
    if any(word in reasoning_lower for word in ["comprehensive", "extensive", "detailed", "all projects", "complete list"]):
        return "comprehensive_analysis"
    elif any(word in reasoning_lower for word in ["specific", "particular", "focused", "single project"]):
        return "focused_query"  
    elif any(word in reasoning_lower for word in ["compare", "comparison", "versus", "different"]):
        return "comparative_analysis"
    elif any(word in reasoning_lower for word in ["recent", "latest", "newest", "current"]):
        return "temporal_query"
    else:
        return "general_query"

def node_plan(state: RAGState) -> dict:
    t_start = time.time()
    log_query.info(">>> PLAN START")

    # OPTIMIZATION: Run Plan + Route LLM calls in parallel to save ~1s
    def plan_task():
        # Get conversation context (last 2 exchanges) for the planner
        conversation_context = get_conversation_context(state.session_id, max_exchanges=2)

        # Log if we're using conversation context
        if conversation_context:
            log_query.info("📖 Using conversation context for planning")

        # Format prompt with conversation context
        full_prompt = PLANNER_PROMPT.format(
            q=state.user_query,
            playbook=PLANNER_PLAYBOOK,
            conversation_context=conversation_context or "(No prior conversation)"
        )
        return planner_llm.invoke(full_prompt).content.strip()

    def route_task():
        # Only run router if project_db is enabled
        data_sources = state.data_sources or {"project_db": True, "code_db": False}
        project_db_enabled = data_sources.get("project_db", True)
        
        if not project_db_enabled:
            # No router needed - code database only mode
            project_filter = detect_project_filter(state.user_query)
            log_route.info("⏭️  Skipping router - code database only mode (data_route=None means code)")
            return {"data_route": None, "project_filter": project_filter}
        
        try:
            project_filter = detect_project_filter(state.user_query)
            choice = router_llm.invoke(
                ROUTER_PROMPT.format(q=state.user_query)
            ).content.strip().lower()
            allowed = {"smart", "large"}
            data_route = choice if choice in allowed else "smart"
            
            # ADD DETAILED ROUTER LOGGING
            log_route.info(f"🎯 ROUTER DECISION: '{state.user_query[:50]}...' → '{choice}' → '{data_route}'")
            log_route.info(f"   LLM choice: '{choice}' | Allowed: {choice in allowed} | Final route: '{data_route}'")
            
            return {"data_route": data_route, "project_filter": project_filter}
        except Exception as e:
            log_route.error(f"Router failed: {e}")
            return {"data_route": None, "project_filter": None}

    # Run both LLM calls in parallel
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_plan = executor.submit(plan_task)
        future_route = executor.submit(route_task)

        raw = future_plan.result()
        route_result = future_route.result()

    # Store route result in state for node_route to return
    state._parallel_route_result = route_result

    # parse -> normalize -> store (same as before)
    try:
        # find first JSON object in case model leaks text
        m = re.search(r"\{.*\}\s*$", raw, flags=re.S)
        json_str = m.group(0) if m else raw
        log_query.info(f"🔍 PLANNER RAW JSON: {json_str}")
        obj = json.loads(json_str)
                        
    except Exception as e:
        log_query.error(f"Planner JSON parse failed: {e}\nRAW:\n{raw}")
        obj = {}

    plan = _normalize_plan(obj, fallback_q=state.user_query)

    # ENHANCED LOGGING: Show planning details clearly
    log_query.info("🎯 PLANNING DETAILS:")
    log_query.info(f"   Reasoning: {plan.get('reasoning', 'N/A')}")
    log_query.info(f"   Number of steps: {len(plan.get('steps', []))}")

    # Log each step with details
    for i, step in enumerate(plan.get('steps', []), 1):
        op = step.get('op', '?')
        args = step.get('args', {})
        log_query.info(f"   Step {i}: {op}")
        if args:
            # Pretty print important args
            for key, val in args.items():
                if key == 'queries' and isinstance(val, list):
                    log_query.info(f"      - {key}: {len(val)} queries")
                else:
                    log_query.info(f"      - {key}: {val}")

    # Log subqueries formed
    subqueries = plan.get('subqueries', [state.user_query])
    log_query.info(f"🔍 SUBQUERIES FORMED ({len(subqueries)} total):")
    for i, subq in enumerate(subqueries, 1):
        log_query.info(f"   [{i}] {subq}")

    t_elapsed = time.time() - t_start
    log_query.info(f"<<< PLAN DONE in {t_elapsed:.2f}s (including parallel route)")

    # SEMANTIC INTELLIGENCE: Capture planning intelligence
    planning_intelligence = {
        "reasoning": plan.get("reasoning", ""),
        "complexity_assessment": _extract_complexity_from_reasoning(plan.get("reasoning", "")),
        "topics_explored": plan.get("subqueries", [state.user_query])[:5],  # Limit to 5 topics
        "strategy_operations": [step.get("op") for step in plan.get("steps", [])],
        "extract_targets": [step.get("args", {}).get("target", "") for step in plan.get("steps", []) if step.get("op") == "EXTRACT"],
        "timestamp": time.time()
    }
    
    # Store in state for later capture in SESSION_MEMORY
    state._planning_intelligence = planning_intelligence
    
    # Return dict updates - LangGraph merges this into state
    return {
        "query_plan": plan,
        "expanded_queries": plan.get("subqueries", [state.user_query])
    }

if HAS_LANGCHAIN and PromptTemplate is not None:
    ROUTER_PROMPT = PromptTemplate.from_template(
        "You are a routing assistant for a retrieval system with two vector database tables, each using different chunking strategies:\n\n"
    
        "DATABASE CHUNKING METHODOLOGY:\n"
        "- smart: Contains SMALLER chunks broken down into granular pieces. Each chunk is more atomic and specific.\n"
        "  Best for: Broad searches, finding all instances of a concept across many projects, comprehensive lists,\n"
        "  pattern discovery, and queries requiring high recall (finding everything relevant).\n"
        "  Example use cases: 'show me all projects with floating slabs', 'find all mentions of steel beams',\n"
        "  'list projects in Toronto', 'what projects use engineered lumber'.\n\n"
        
        "- large: Contains LARGER chunks with more surrounding context preserved in each chunk.\n"
        "  Best for: Deep dives into specific details, understanding relationships between concepts,\n"
        "  multi-constraint queries, and questions requiring nuanced context to answer properly.\n"
        "  Example use cases: 'what are the bracing requirements for project 25-08-005',\n"
        "  'explain the connection details between the beam and column', 'find projects with both\n"
        "  floating slabs AND specific dimension requirements'.\n\n"
        
        "DECISION GUIDELINES:\n"
        "- Ask yourself: Does this query need to FIND MANY THINGS (→ smart) or UNDERSTAND ONE THING DEEPLY (→ large)?\n"
        "- Questions with 'all', 'list', 'show me', 'find projects' → usually smart\n"
        "- Questions asking 'what are the details', 'explain', 'describe', specific technical questions → usually large\n"
        "- Questions with multiple technical constraints or requiring context → usually large\n"
        "- When in doubt about coverage vs. detail → smart\n\n"
        "Output exactly ONE token from this set: smart|large.\n\n"
        "Question: {q}"
    )
else:
    ROUTER_PROMPT = None

router_llm = llm_router if HAS_LANGCHAIN and llm_router is not None else None  # Use router model for routing decisions

def _get_route_reasoning(data_route: str) -> str:
    """Get reasoning for routing decision."""
    route_reasoning = {
        "smart": "granular_chunks_for_broad_search",
        "large": "detailed_chunks_for_deep_analysis", 
        "hybrid": "mixed_strategy_for_complex_query"
    }
    return route_reasoning.get(data_route, "default_routing")

def node_route(state: RAGState) -> dict:
    """Route query to the correct source with guardrails."""
    t_start = time.time()
    log_route.info(">>> ROUTE START")

    # Check if routing was already done in parallel during node_plan
    if hasattr(state, '_parallel_route_result'):
        route_result = state._parallel_route_result
        log_route.info(f"Using pre-computed route from parallel execution")
        log_route.info(f"Routing to {route_result.get('data_route')} (filter={route_result.get('project_filter')})")

        # SEMANTIC INTELLIGENCE: Capture routing intelligence 
        routing_intelligence = {
            "data_route": route_result.get('data_route'),
            "project_filter": route_result.get('project_filter'),
            "route_reasoning": _get_route_reasoning(route_result.get('data_route', 'smart')) if route_result.get('data_route') else "code_database_only",
            "scope_assessment": "filtered" if route_result.get('project_filter') else "open",
            "timestamp": time.time(),
            "source": "parallel_execution"
        }
        
        # Store in state for later capture in SESSION_MEMORY
        state._routing_intelligence = routing_intelligence

        t_elapsed = time.time() - t_start
        log_route.info(f"<<< ROUTE DONE in {t_elapsed:.2f}s (used cached result)")
        return route_result

    # Fallback: run routing if it wasn't done in parallel
    try:
        # Only run router if project_db is enabled
        data_sources = state.data_sources or {"project_db": True, "code_db": False}
        project_db_enabled = data_sources.get("project_db", True)
        
        if not project_db_enabled:
            # No router needed - code database only mode
            project_filter = detect_project_filter(state.user_query)
            log_route.info("⏭️  Skipping router - code database only mode (data_route=None means code)")
            return {"data_route": None, "project_filter": project_filter}
        
        # keep your existing project filter by regex
        project_filter = detect_project_filter(state.user_query)

        # LLM chooses the source mix (only for project_db)
        choice = router_llm.invoke(
            ROUTER_PROMPT.format(q=state.user_query)
        ).content.strip().lower()

        allowed = {"smart", "large"}
        data_route = choice if choice in allowed else "smart"
        
        # ADD DETAILED ROUTER LOGGING
        log_route.info(f"🎯 ROUTER DECISION: '{state.user_query[:50]}...' → '{choice}' → '{data_route}'")
        log_route.info(f"   LLM choice: '{choice}' | Allowed: {choice in allowed} | Final route: '{data_route}'")
        log_route.info(f"Routing to {data_route} (filter={project_filter})")

        # SEMANTIC INTELLIGENCE: Capture routing intelligence (fallback path)
        routing_intelligence = {
            "data_route": data_route,
            "project_filter": project_filter,
            "route_reasoning": _get_route_reasoning(data_route) if data_route else "code_database_only",
            "scope_assessment": "filtered" if project_filter else "open",
            "timestamp": time.time(),
            "source": "fallback_execution"
        }
        
        # Store in state for later capture in SESSION_MEMORY
        state._routing_intelligence = routing_intelligence

        t_elapsed = time.time() - t_start
        log_route.info(f"<<< ROUTE DONE in {t_elapsed:.2f}s")

        return {"data_route": data_route, "project_filter": project_filter}
    except Exception as e:
        log_route.error(f"Router failed: {e}")
        t_elapsed = time.time() - t_start
        log_route.info(f"<<< ROUTE DONE (with error) in {t_elapsed:.2f}s")
        return {"data_route": None, "project_filter": None}


@(track_function if HAS_ENHANCED_LOGGER else lambda x: x)
# =============================================================================
# IMAGE SIMILARITY SEARCH NODES
# =============================================================================

def node_generate_image_embeddings(state: RAGState) -> dict:
    """
    Generate Vit-H14 embeddings for uploaded images.
    Only runs if images_base64 is provided and use_image_similarity is True.
    """
    t_start = time.time()
    log_query.info(">>> GENERATE IMAGE EMBEDDINGS START")
    
    # Early exit if not needed - preserves existing flow
    if not state.images_base64 or not state.use_image_similarity:
        log_query.info("⏭️  Skipping image embedding generation - no images or similarity disabled")
        return {}
    
    try:
        embeddings = []
        for i, image_base64 in enumerate(state.images_base64):
            try:
                embedding = generate_vit_h14_embedding(image_base64)
                embeddings.append(embedding)
                log_vlm.info(f"🖼️ Generated embedding {i+1}/{len(state.images_base64)}: {len(embedding)} dimensions")
            except Exception as e:
                log_vlm.error(f"🖼️ Failed to generate embedding for image {i+1}: {e}")
                # Continue with other images if one fails
                continue
        
        if not embeddings:
            log_vlm.warning("🖼️ No embeddings generated, falling back to text-only search")
            return {"use_image_similarity": False}  # Disable similarity search
        
        t_elapsed = time.time() - t_start
        log_vlm.info(f"<<< GENERATE IMAGE EMBEDDINGS DONE in {t_elapsed:.2f}s")
        
        return {
            "image_embeddings": embeddings
        }
        
    except Exception as e:
        log_vlm.error(f"🖼️ Image embedding generation failed: {e}")
        return {"use_image_similarity": False}  # Fail gracefully

def node_image_similarity_search(state: RAGState) -> dict:
    """
    Search for similar images using vector similarity on image_embeddings table.
    Only runs if image_embeddings are available.
    """
    t_start = time.time()
    log_vlm.info(">>> IMAGE SIMILARITY SEARCH START")
    
    # Early exit if not needed
    if not state.image_embeddings or not state.use_image_similarity:
        log_vlm.info("⏭️  Skipping image similarity search - no embeddings available")
        return {"image_similarity_results": []}
    
    try:
        if not SUPABASE_URL or not SUPABASE_KEY:
            log_vlm.warning("🖼️ Supabase not configured, skipping image similarity search")
            return {"image_similarity_results": []}
        
        _supa = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Use first image embedding (can be extended to handle multiple)
        query_embedding = state.image_embeddings[0]
        match_count = 10  # Get top 10 similar images
        
        log_vlm.info(f"🖼️ Searching for similar images with match_count={match_count}")
        
        # Call Supabase RPC function
        try:
            result = _supa.rpc("match_image_embeddings", {
                'query_embedding': query_embedding,
                'match_count': match_count
            }).execute()
            
            similar_images = result.data or []
            log_vlm.info(f"🖼️ Found {len(similar_images)} similar images")
            
            # Extract project_keys from results for potential filtering
            project_keys = []
            for img in similar_images:
                project_key = img.get("project_key")
                if project_key and project_key not in project_keys:
                    project_keys.append(project_key)
            
            log_vlm.info(f"🖼️ Images from {len(project_keys)} projects: {project_keys[:5]}")
            
            t_elapsed = time.time() - t_start
            log_vlm.info(f"<<< IMAGE SIMILARITY SEARCH DONE in {t_elapsed:.2f}s")
            
            return {
                "image_similarity_results": similar_images,
                # Optionally enrich selected_projects if we found good matches
                "selected_projects": list(set(project_keys + state.selected_projects)) if project_keys else state.selected_projects
            }
            
        except Exception as rpc_error:
            log_vlm.error(f"🖼️ Supabase RPC function failed: {rpc_error}")
            log_vlm.info("🖼️ Falling back to direct vector search (if available)")
            # Could implement fallback here if needed
            return {"image_similarity_results": []}
            
    except Exception as e:
        log_vlm.error(f"🖼️ Image similarity search failed: {e}")
        import traceback
        log_vlm.error(f"🖼️ Traceback: {traceback.format_exc()}")
        return {"image_similarity_results": []}  # Fail gracefully

def node_retrieve(state: RAGState) -> dict:
    t_start = time.time()
    try:
        log_query.info(">>> RETRIEVE START")

        if state.query_plan and state.query_plan.get("steps"):
            result = execute_plan(state)
            docs = result.get("retrieved_docs", [])
            code_docs = result.get("retrieved_code_docs", [])
            
            _log_docs_summary(docs, log_query, "Retrieved via plan (project)")
            if code_docs:
                _log_docs_summary(code_docs, log_query, "Retrieved via plan (code)")

            # ENHANCED LOGGING: Detailed chunk and project information
            try:
                _log_retrieved_chunks_detailed(docs, log_query)
            except Exception as log_err:
                log_query.warning(f"Logging error (non-fatal): {log_err}")
            if code_docs:
                try:
                    _log_retrieved_chunks_detailed(code_docs, log_query)
                except Exception as log_err:
                    log_query.warning(f"Logging error (non-fatal): {log_err}")

            # Check if code-only mode (no project docs but have code docs)
            data_sources = state.data_sources or {"project_db": True, "code_db": False}
            project_db_enabled = data_sources.get("project_db", True)
            
            if code_docs and not project_db_enabled and not docs:
                # Code-only mode: pass code docs through retrieved_docs so they flow through grader
                log_query.info(f"📊 CODE-ONLY MODE (plan): Passing {len(code_docs)} code docs through grader pipeline")
                result["retrieved_docs"] = code_docs
                state._code_docs = code_docs  # Also store separately for synthesis
                log_query.info(f"📦 Code docs stored separately: {len(code_docs)} docs")
            elif code_docs:
                # Both enabled or project mode: keep code docs separate
                # Return in retrieved_code_docs so it flows through state (not _code_docs which gets lost)
                result["retrieved_code_docs"] = code_docs
                log_query.info(f"📦 Returning {len(code_docs)} code docs in retrieved_code_docs (plan path)")

            t_elapsed = time.time() - t_start
            log_query.info(f"<<< RETRIEVE DONE in {t_elapsed:.2f}s")
            return result

        # fallback to legacy retrieval when no plan is provided
        # UPDATED: check data_sources to determine which databases to search
        log_query.info("Using legacy retrieval (no plan)")
        
        # Get data source preferences from state
        data_sources = state.data_sources or {"project_db": True, "code_db": False, "coop_manual": False}
        project_db_enabled = data_sources.get("project_db", True)
        code_db_enabled = data_sources.get("code_db", False)
        coop_db_enabled = data_sources.get("coop_manual", False)
        
        log_query.info(f"🔍 DATA SOURCES: project_db={project_db_enabled}, code_db={code_db_enabled}, coop_manual={coop_db_enabled}")
        
        # Initialize lists to store results from each database
        project_docs = []
        code_docs = []
        coop_docs = []
        
        # ========== PROJECT DATABASE RETRIEVAL ==========
        if project_db_enabled:
            # Router only runs for project_db, so data_route should be smart/large
            # If None, it means router didn't run (code_db only mode), but we're here because project_db=True
            # So we default to smart as fallback
            route = state.data_route if (state.data_route and state.data_route != "code") else "smart"
            
            # Set chunk limit based on route
            if route == "smart":
                chunk_limit = MAX_SMART_RETRIEVAL_DOCS
            elif route == "large":
                chunk_limit = MAX_LARGE_RETRIEVAL_DOCS
            else:  # fallback to smart
                chunk_limit = MAX_SMART_RETRIEVAL_DOCS
                route = "smart"  # Normalize route to smart for fallback
            
            log_query.info(f"🔍 PROJECT DB RETRIEVE: route='{route}', chunk_limit={chunk_limit}")
            
            try:
                if route == "smart" and 'vs_smart' in globals() and vs_smart is not None:
                    log_query.info(f"   📊 Using SMART table: '{SUPA_SMART_TABLE}'")
                    project_docs = vs_smart.similarity_search(state.user_query, k=chunk_limit)
                    log_query.info(f"   ✅ Retrieved {len(project_docs)} docs from smart table")
                    
                elif route == "large" and 'vs_large' in globals() and vs_large is not None:
                    log_query.info(f"   📊 Using LARGE table: '{SUPA_LARGE_TABLE}'")
                    project_docs = vs_large.similarity_search(state.user_query, k=chunk_limit)
                    log_query.info(f"   ✅ Retrieved {len(project_docs)} docs from large table")
                    
                else:
                    log_query.warning(f"   ⚠️  Unknown route '{route}', skipping project database")
                    
            except Exception as e:
                log_query.error(f"❌ Project database retrieve failed ({route}): {e}")
                project_docs = []
        else:
            log_query.info("⏭️  Project database disabled, skipping")
        
        # ========== CODE DATABASE RETRIEVAL ==========
        if code_db_enabled:
            log_query.info(f"🔍 CODE DB RETRIEVE: chunk_limit={MAX_CODE_RETRIEVAL_DOCS}")
            
            try:
                if 'vs_code' in globals() and vs_code is not None:
                    log_query.info(f"   💻 Using CODE table: '{SUPA_CODE_TABLE}'")
                    # Use hybrid retriever for code database
                    code_retriever = make_code_hybrid_retriever()
                    code_docs = code_retriever(state.user_query, k=MAX_CODE_RETRIEVAL_DOCS)
                    log_query.info(f"   ✅ Retrieved {len(code_docs)} docs from code table")
                    
                    # Apply MMR diversification to code docs too
                    if code_docs:
                        query_emb = emb.embed_query(state.user_query)
                        code_docs = mmr_rerank_code(code_docs, query_emb, lambda_=0.9, k=len(code_docs))
                        log_query.info(f"💻 CODE RETRIEVE + MMR: {len(code_docs)} docs from code database")
                else:
                    log_query.warning("   ⚠️  Code vector store not available (vs_code is None)")
                    code_docs = []
                    
            except Exception as e:
                log_query.error(f"❌ Code database retrieve failed: {e}")
                code_docs = []
        else:
            log_query.info("⏭️  Code database disabled, skipping")
        
        # ========== COOP MANUAL DATABASE RETRIEVAL ==========
        if coop_db_enabled:
            log_query.info(f"🔍 COOP DB RETRIEVE: chunk_limit={MAX_CODE_RETRIEVAL_DOCS}")
            
            try:
                if 'vs_coop' in globals() and vs_coop is not None:
                    log_query.info(f"   📚 Using COOP table: '{SUPA_COOP_TABLE}'")
                    # Use hybrid retriever for coop database
                    coop_retriever = make_coop_hybrid_retriever()
                    coop_docs = coop_retriever(state.user_query, k=MAX_CODE_RETRIEVAL_DOCS)
                    log_query.info(f"   ✅ Retrieved {len(coop_docs)} docs from coop table")
                    
                    # Apply MMR diversification to coop docs too
                    if coop_docs:
                        query_emb = emb.embed_query(state.user_query)
                        coop_docs = mmr_rerank_coop(coop_docs, query_emb, lambda_=0.9, k=len(coop_docs))
                        log_query.info(f"📚 COOP RETRIEVE + MMR: {len(coop_docs)} docs from coop database")
                else:
                    log_query.warning("   ⚠️  Coop vector store not available (vs_coop is None)")
                    coop_docs = []
                    
            except Exception as e:
                log_query.error(f"❌ Coop database retrieve failed: {e}")
                coop_docs = []
        else:
            log_query.info("⏭️  Coop database disabled, skipping")
        
        # ========== COMBINE RESULTS ==========
        # In code-only mode, put code docs into retrieved_docs so they flow through grader
        # In project mode or both, keep them separate
        
        # Check if code-only mode
        if code_docs and not project_db_enabled and not coop_db_enabled:
            # Code-only mode: put code docs in retrieved_docs so they flow through the pipeline
            retrieved = code_docs
            log_query.info(f"📊 CODE-ONLY MODE (legacy): Passing {len(code_docs)} code docs through grader pipeline")
            # Also store separately for synthesis
            state._code_docs = code_docs
            log_query.info(f"📦 Code docs stored separately (legacy): {len(code_docs)} docs")
        elif coop_docs and not project_db_enabled and not code_db_enabled:
            # Coop-only mode: put coop docs in retrieved_docs so they flow through the pipeline
            retrieved = coop_docs
            log_query.info(f"📊 COOP-ONLY MODE (legacy): Passing {len(coop_docs)} coop docs through grader pipeline")
            # Also store separately for synthesis
            state._coop_docs = coop_docs
            log_query.info(f"📦 Coop docs stored separately (legacy): {len(coop_docs)} docs")
        else:
            # Project mode or both: use project docs in retrieved_docs
            retrieved = project_docs
            # Code and coop docs will be returned in retrieved_code_docs and retrieved_coop_docs (not stored in _code_docs/_coop_docs which gets lost)
        
        # Log summary
        if not retrieved and not code_docs and not coop_docs:
            log_query.warning("⚠️  No documents retrieved from any enabled database")
            return {"retrieved_docs": [], "retrieved_code_docs": [], "retrieved_coop_docs": []}
        
        log_query.info(f"📊 TOTAL RETRIEVED: {len(project_docs)} project docs, {len(code_docs)} code docs, {len(coop_docs)} coop docs")
        
        # Revit filtering is handled in SQL pre-filtering, not here
        # No metadata filtering needed
        
        if project_docs:
            _log_docs_summary(project_docs, log_query, "Retrieved (legacy - project)")
        if code_docs:
            _log_docs_summary(code_docs, log_query, "Retrieved (legacy - code)")
        if coop_docs:
            _log_docs_summary(coop_docs, log_query, "Retrieved (legacy - coop)")

        # ENHANCED LOGGING: Detailed chunk and project information
        try:
            _log_retrieved_chunks_detailed(retrieved, log_query)
        except Exception as log_err:
            log_query.warning(f"Logging error (non-fatal): {log_err}")

        result = {"retrieved_docs": retrieved}
        if code_docs and project_db_enabled:
            # Only include retrieved_code_docs if both databases enabled (for separate processing)
            result["retrieved_code_docs"] = code_docs
        if coop_docs and (project_db_enabled or code_db_enabled):
            # Include retrieved_coop_docs if other databases are enabled (for separate processing)
            result["retrieved_coop_docs"] = coop_docs
        
        t_elapsed = time.time() - t_start
        log_query.info(f"<<< RETRIEVE DONE in {t_elapsed:.2f}s")
        return result
    except Exception as e:
        log_query.error(f"node_retrieve failed: {e}")
        import traceback
        log_query.error(f"Traceback: {traceback.format_exc()}")
        t_elapsed = time.time() - t_start
        log_query.info(f"<<< RETRIEVE DONE (with error) in {t_elapsed:.2f}s")
        # CRITICAL: If we have retrieved docs, return them even if there was an error
        # The error might just be in logging, not in the actual retrieval
        if 'retrieved' in locals() and retrieved:
            log_query.warning(f"⚠️ Error occurred but returning {len(retrieved)} retrieved docs")
            result = {"retrieved_docs": retrieved}
            if 'code_docs' in locals() and code_docs:
                result["retrieved_code_docs"] = code_docs
            if 'coop_docs' in locals() and coop_docs:
                result["retrieved_coop_docs"] = coop_docs
            return result
        return {"retrieved_docs": []}

def _serialize_docs(docs, limit=12):
    out = []
    for i, d in enumerate((docs or [])[:limit], 1):
        md = d.metadata or {}
        out.append({
            "rank": i,
            "doc_id": md.get("doc_id") or md.get("id"),
            "project_id": md.get("drawing_number") or md.get("project_key"),
            "sheet": md.get("page_id") or md.get("page"),
            "title": md.get("title"),
            "search_type": md.get("search_type"),
            "score": md.get("score"),
            "preview": (d.page_content or "")[:280]
        })
    return out


#--------------------------------------------------------added because it was taking so long to grade--------------------------------------------------------
USE_GRADER = False
USE_SUPPORT_SCORING = False  # Disable support scoring (saves ~10s per query, currently returns 0.00 anyway)
USE_VERIFIER = False  # Disable answer verification (currently reduces results from 20 to 3 citations)

def node_grade(state: RAGState) -> dict:
    """Grade documents - handles both project docs and code docs separately when both databases are enabled."""
    t_start = time.time()
    try:
        log_enh.info(">>> GRADE START")
        
        # Check data sources to determine if we need to grade code/coop docs separately
        data_sources = state.data_sources or {"project_db": True, "code_db": False, "coop_manual": False}
        project_db_enabled = data_sources.get("project_db", True)
        code_db_enabled = data_sources.get("code_db", False)
        coop_db_enabled = data_sources.get("coop_manual", False)
        
        log_enh.info(f"USE_GRADER={USE_GRADER}, Project docs: {len(state.retrieved_docs or [])}, Code docs: {len(state.retrieved_code_docs or [])}, Coop docs: {len(state.retrieved_coop_docs or [])}")

        # Grade project docs (always grade retrieved_docs)
        if not USE_GRADER:
            graded = (state.retrieved_docs or [])[:MAX_GRADED_DOCS]
            log_enh.info(f"Grading disabled - capping project docs to MAX_GRADED_DOCS={MAX_GRADED_DOCS}")
            _log_docs_summary(graded, log_enh, "Graded (capped)")
        else:
            log_enh.info("Running self_grade on project docs...")
            graded = self_grade(state.user_query, state.retrieved_docs)
            _log_docs_summary(graded, log_enh, "Graded (filtered)")

        # Grade code docs separately if code database is enabled
        graded_code = []
        if code_db_enabled and state.retrieved_code_docs:
            log_enh.info(f"Code database enabled - grading code docs separately: {len(state.retrieved_code_docs)} docs")
            if not USE_GRADER:
                graded_code = (state.retrieved_code_docs or [])[:MAX_GRADED_DOCS]
                log_enh.info(f"Grading disabled - capping code docs to MAX_GRADED_DOCS={MAX_GRADED_DOCS}")
                _log_docs_summary(graded_code, log_enh, "Graded code docs (capped)")
            else:
                log_enh.info("Running self_grade on code docs...")
                graded_code = self_grade(state.user_query, state.retrieved_code_docs)
                _log_docs_summary(graded_code, log_enh, "Graded code docs (filtered)")

        # Grade coop docs separately if coop database is enabled
        graded_coop = []
        if coop_db_enabled and state.retrieved_coop_docs:
            log_enh.info(f"Coop database enabled - grading coop docs separately: {len(state.retrieved_coop_docs)} docs")
            if not USE_GRADER:
                graded_coop = (state.retrieved_coop_docs or [])[:MAX_GRADED_DOCS]
                log_enh.info(f"Grading disabled - capping coop docs to MAX_GRADED_DOCS={MAX_GRADED_DOCS}")
                _log_docs_summary(graded_coop, log_enh, "Graded coop docs (capped)")
            else:
                log_enh.info("Running self_grade on coop docs...")
                graded_coop = self_grade(state.user_query, state.retrieved_coop_docs)
                _log_docs_summary(graded_coop, log_enh, "Graded coop docs (filtered)")

        t_elapsed = time.time() - t_start
        log_enh.info(f"<<< GRADE DONE in {t_elapsed:.2f}s")
        
        result = {"graded_docs": graded}
        if graded_code:
            result["graded_code_docs"] = graded_code
        if graded_coop:
            result["graded_coop_docs"] = graded_coop
        
        return result
    except Exception as e:
        log_enh.error(f"Grading failed: {e}")
        t_elapsed = time.time() - t_start
        log_enh.info(f"<<< GRADE DONE (with error) in {t_elapsed:.2f}s")
        graded = (state.retrieved_docs or [])[:MAX_GRADED_DOCS]
        graded_code = (state.retrieved_code_docs or [])[:MAX_GRADED_DOCS] if state.retrieved_code_docs else []
        graded_coop = (state.retrieved_coop_docs or [])[:MAX_GRADED_DOCS] if state.retrieved_coop_docs else []
        result = {"graded_docs": graded}
        if graded_code:
            result["graded_code_docs"] = graded_code
        if graded_coop:
            result["graded_coop_docs"] = graded_coop
        return result


def node_answer(state: RAGState) -> dict:
    """Synthesize an answer with guardrails."""
    try:
        docs = list(state.graded_docs or [])

        # >>> NEW: lock the number of distinct projects if the user asked for N <<<
        n = requested_project_count(state.user_query)
        if n:
            docs = pick_top_n_projects(docs, n=n, max_docs=MAX_SYNTHESIS_DOCS)

        if state.db_result and state.data_route in ("db", "hybrid"):
            docs.append(Document(
                page_content=f"[DB]\n{state.db_result}",
                metadata={"drawing_number": "DB", "page_id": "-"}
            ))

        # Check which databases are enabled
        data_sources = state.data_sources or {"project_db": True, "code_db": False, "coop_manual": False}
        project_db_enabled = data_sources.get("project_db", True)
        code_db_enabled = data_sources.get("code_db", False)
        coop_db_enabled = data_sources.get("coop_manual", False)
        
        # Get code docs from state - use graded_code_docs if available
        code_docs = list(state.graded_code_docs or [])
        if not code_docs:
            code_docs = list(state.retrieved_code_docs or [])
        if not code_docs:
            code_docs = getattr(state, '_code_docs', [])
        
        # Get coop docs from state - use graded_coop_docs if available
        coop_docs = list(state.graded_coop_docs or [])
        if not coop_docs:
            coop_docs = list(state.retrieved_coop_docs or [])
        if not coop_docs:
            coop_docs = getattr(state, '_coop_docs', [])
        
        if code_docs:
            code_docs = code_docs[:MAX_SYNTHESIS_DOCS]
            log_query.info(f"🔍 Found {len(code_docs)} code docs for synthesis")
        
        if coop_docs:
            coop_docs = coop_docs[:MAX_SYNTHESIS_DOCS]
            log_query.info(f"🔍 Found {len(coop_docs)} coop docs for synthesis")
        
        # Handle code-only mode
        if not code_docs and code_db_enabled and not project_db_enabled and not coop_db_enabled and docs:
            code_docs = docs[:MAX_SYNTHESIS_DOCS]
            docs = []
            log_query.info(f"🔍 CODE-ONLY MODE: Using graded_docs ({len(code_docs)} docs) as code_docs")
        
        # Handle coop-only mode
        if not coop_docs and coop_db_enabled and not project_db_enabled and not code_db_enabled and docs:
            coop_docs = docs[:MAX_SYNTHESIS_DOCS]
            docs = []
            log_query.info(f"🔍 COOP-ONLY MODE: Using graded_docs ({len(coop_docs)} docs) as coop_docs")
        
        # Count how many databases are enabled
        enabled_count = sum([project_db_enabled, code_db_enabled, coop_db_enabled])
        
        # Synthesize separately if multiple databases are enabled
        if enabled_count > 1 and (code_docs or coop_docs):
            log_query.info(f"🔍 MULTI-DB MODE: Synthesizing separately in parallel - {len(docs)} project docs, {len(code_docs)} code docs, {len(coop_docs)} coop docs")
            
            # Prepare metadata for project synthesis
            pre_fetched_metadata = getattr(state, '_project_metadata', None)
            
            def synthesize_project():
                """Synthesize project answer."""
                if not project_db_enabled or not docs:
                    return None, []
                log_query.info("Starting project synthesis...")
                project_ans, project_cites = synthesize(
                    state.user_query, 
                    docs, 
                    state.session_id, 
                    project_metadata=pre_fetched_metadata,
                    code_docs=None,
                    use_code_prompt=False,
                    coop_docs=None,
                    use_coop_prompt=False,
                    active_filters=getattr(state, 'active_filters', None)
                )
                log_query.info(f"Project synthesis complete - answer length={len(project_ans)}, citations={len(project_cites)}")
                return project_ans, project_cites
            
            def synthesize_code():
                """Synthesize code answer."""
                if not code_db_enabled or not code_docs:
                    return None, []
                log_query.info("Starting code synthesis...")
                code_ans, code_cites = synthesize(
                    state.user_query, 
                    [], 
                    state.session_id, 
                    project_metadata=None,
                    code_docs=code_docs,
                    use_code_prompt=True,
                    coop_docs=None,
                    use_coop_prompt=False,
                    active_filters=getattr(state, 'active_filters', None)
                )
                log_query.info(f"Code synthesis complete - answer length={len(code_ans)}, citations={len(code_cites)}")
                return code_ans, code_cites
            
            def synthesize_coop():
                """Synthesize coop answer."""
                if not coop_db_enabled or not coop_docs:
                    return None, []
                log_query.info("Starting coop synthesis...")
                coop_ans, coop_cites = synthesize(
                    state.user_query, 
                    [], 
                    state.session_id, 
                    project_metadata=None,
                    code_docs=None,
                    use_code_prompt=False,
                    coop_docs=coop_docs,
                    use_coop_prompt=True,
                    active_filters=getattr(state, 'active_filters', None)
                )
                log_query.info(f"Coop synthesis complete - answer length={len(coop_ans)}, citations={len(coop_cites)}")
                return coop_ans, coop_cites
            
            # Run synthesis tasks in parallel (up to 3 workers)
            futures = {}
            with ThreadPoolExecutor(max_workers=3) as executor:
                if project_db_enabled and docs:
                    futures['project'] = executor.submit(synthesize_project)
                if code_db_enabled and code_docs:
                    futures['code'] = executor.submit(synthesize_code)
                if coop_db_enabled and coop_docs:
                    futures['coop'] = executor.submit(synthesize_coop)
                
                project_ans, project_cites = futures['project'].result() if 'project' in futures else (None, [])
                code_ans, code_cites = futures['code'].result() if 'code' in futures else (None, [])
                coop_ans, coop_cites = futures['coop'].result() if 'coop' in futures else (None, [])
            
            log_query.info(f"🔍 MULTI-DB MODE: Project answer length={len(project_ans) if project_ans else 0}, Code answer length={len(code_ans) if code_ans else 0}, Coop answer length={len(coop_ans) if coop_ans else 0}")
            
            reranked = rerank_by_dimension_similarity(state.user_query, state.graded_docs) if project_db_enabled else []
            
            result = {"graded_docs": reranked}
            if project_ans:
                result["final_answer"] = project_ans
                result["answer_citations"] = project_cites
            if code_ans:
                result["code_answer"] = code_ans
                result["code_citations"] = code_cites
            if coop_ans:
                result["coop_answer"] = coop_ans
                result["coop_citations"] = coop_cites
            
            return result
        else:
            # Single answer mode (backward compatible)
            # Use pre-fetched project metadata if available (from LIMIT_PROJECTS), otherwise synthesize will fetch
            pre_fetched_metadata = getattr(state, '_project_metadata', None)
            
            # Handle single database modes
            if code_docs and not project_db_enabled and not coop_db_enabled:
                # Code-only mode
                ans, cites = synthesize(state.user_query, [], state.session_id, 
                                      project_metadata=None,
                                      code_docs=code_docs,
                                      use_code_prompt=True,
                                      coop_docs=None,
                                      use_coop_prompt=False,
                                      active_filters=getattr(state, 'active_filters', None))
                return {"code_answer": ans, "code_citations": cites, "graded_docs": []}
            elif coop_docs and not project_db_enabled and not code_db_enabled:
                # Coop-only mode
                ans, cites = synthesize(state.user_query, [], state.session_id, 
                                      project_metadata=None,
                                      code_docs=None,
                                      use_code_prompt=False,
                                      coop_docs=coop_docs,
                                      use_coop_prompt=True,
                                      active_filters=getattr(state, 'active_filters', None))
                return {"coop_answer": ans, "coop_citations": cites, "graded_docs": []}
            else:
                # Project docs only or combined (backward compatible)
                ans, cites = synthesize(state.user_query, docs, state.session_id, 
                                       project_metadata=pre_fetched_metadata,
                                       code_docs=code_docs if code_docs else None,
                                       use_code_prompt=False,
                                       coop_docs=coop_docs if coop_docs else None,
                                       use_coop_prompt=False,
                                       active_filters=getattr(state, 'active_filters', None))  # Project prompt (default)
                reranked = rerank_by_dimension_similarity(state.user_query, state.graded_docs)
                
                return {"final_answer": ans, "answer_citations": cites, "graded_docs": reranked}
    except Exception as e:
        log_syn.error(f"Answer synthesis failed: {e}")
        return {"final_answer": "Error synthesizing answer", "answer_citations": []}

#---------------------------------------------------VERIFIER---------------------------------------------------
# use your fast/cheap model; you can point this to llm_support or llm_fast
llm_verify = ChatOpenAI(model=FAST_MODEL, temperature=0,
                        max_retries=1, timeout=25,
                        response_format={"type": "json_object"}) if HAS_LANGCHAIN and ChatOpenAI is not None else None  # or llm_fast

if HAS_LANGCHAIN and PromptTemplate is not None:
    VERIFY_PROMPT = PromptTemplate.from_template("""
You are a strict verifier for a retrieval QA system.

Inputs:
- USER QUESTION (may ask for N projects, date filters like "after June", and features like "retaining wall" or "sandwich wall")
- CURRENT ANSWER (may be incomplete, have duplicates, or miss project numbers)
- DOC INDEX (list of retrieved evidence chunks with project IDs and short text)

Your job:
1) Interpret the USER QUESTION constraints:
   - Requested project count N (if any).
   - Feature keywords (e.g., "retaining wall", "sandwich wall", etc.).
   - Date constraint hints like "after/before <month[/year]>", or "most recent".
2) Using the DOC INDEX (not imagination), pick a set of DISTINCT project IDs that **best satisfy** the constraints,
   up to N if N is specified. Prefer newer/most relevant when ambiguous.
3) Decide if the CURRENT ANSWER must be repaired because of missing/extra/duplicated projects or count mismatch.
4) If fewer than N truly match in the DOC INDEX, acknowledge the shortfall and still select all the valid ones.

Return STRICT JSON only:
{{
  "needs_fix": true|false,
  "projects": ["25-07-118","25-08-205"],
  "note": "optional short note about shortfall or assumptions"
}}

USER QUESTION:
{q}

CURRENT ANSWER:
{a}

DOC INDEX (project | page | date? | text):
{doc_index}
""")
else:
    VERIFY_PROMPT = None

def _group_docs_by_project(docs: List[Document]):
    proj_to_docs, order = {}, []
    for d in docs or []:
        md = d.metadata or {}
        p = md.get("drawing_number") or md.get("project_key")
        if not p:
            # last-ditch: try to recover from text
            m = PROJECT_RE.search(d.page_content or "")
            p = m.group(0) if m else None
        if not p:
            continue
        if p not in proj_to_docs:
            proj_to_docs[p] = []
            order.append(p)
        proj_to_docs[p].append(d)
    return proj_to_docs, order

def _make_doc_index(docs: List[Document], max_per_project: int = 1, max_chars: int = 160) -> str:
    proj_to_docs, order = _group_docs_by_project(docs)
    rows = []
    for p in order:
        d = proj_to_docs[p][0]
        md = d.metadata or {}
        page = md.get("page_id") or md.get("page") or "?"
        date = md.get("date") or md.get("issue_date") or md.get("signed_date") or ""
        snippet = (d.page_content or "").replace("\n", " ")[:max_chars]
        rows.append(f"{p} | page={page} | date={date} | {snippet}")
    return "\n".join(rows)

def _json_from_text(s: str) -> dict | None:
    try:
        return json.loads(s)
    except Exception:
        return None

def node_verify(state: RAGState) -> dict:
    t_start = time.time()
    log_enh.info(">>> VERIFY START")

    # Skip verification if disabled
    if not USE_VERIFIER:
        t_elapsed = time.time() - t_start
        log_enh.info(f"Verification disabled - skipping")
        log_enh.info(f"<<< VERIFY DONE (skipped) in {t_elapsed:.2f}s")
        return {"needs_fix": False}

    try:
        doc_index = _make_doc_index(state.graded_docs)
        raw = llm_verify.invoke(VERIFY_PROMPT.format(
            q=state.user_query, a=state.final_answer or "", doc_index=doc_index or "(no docs)"
        )).content

        parsed = _json_from_text(raw) or {}
        needs_fix = bool(parsed.get("needs_fix"))
        selected  = [str(p).strip() for p in (parsed.get("projects") or []) if str(p).strip()]

        if not needs_fix:
            t_elapsed = time.time() - t_start
            log_enh.info(f"<<< VERIFY DONE (no fix needed) in {t_elapsed:.2f}s")
            return {"needs_fix": False}

        proj_to_docs, _ = _group_docs_by_project(state.graded_docs)
        # unknown IDs → allow a single retrieve loop; known IDs → fix locally
        unknown = [pid for pid in selected if pid not in proj_to_docs]
        updates = {"needs_fix": bool(unknown)}

        forced_docs = [d for pid in selected for d in proj_to_docs.get(pid, [])]
        if forced_docs:  # resynthesize immediately with the exact set
            # Use pre-fetched project metadata if available
            pre_fetched_metadata = getattr(state, '_project_metadata', None)
            code_docs = getattr(state, '_code_docs', [])
            if code_docs:
                code_docs = code_docs[:MAX_SYNTHESIS_DOCS]
            
            # Check which databases are enabled
            data_sources = state.data_sources or {"project_db": True, "code_db": False, "coop_manual": False}
            project_db_enabled = data_sources.get("project_db", True)
            code_db_enabled = data_sources.get("code_db", False)
            coop_db_enabled = data_sources.get("coop_manual", False)
            
            coop_docs = getattr(state, '_coop_docs', [])
            if coop_docs:
                coop_docs = coop_docs[:MAX_SYNTHESIS_DOCS]
            
            enabled_count = sum([project_db_enabled, code_db_enabled, coop_db_enabled])
            
            if enabled_count > 1 and (code_docs or coop_docs):
                # Multi-database mode - resynthesize separately
                if project_db_enabled and forced_docs:
                    project_ans, project_cites = synthesize(state.user_query, forced_docs, state.session_id, 
                                                          project_metadata=pre_fetched_metadata,
                                                          code_docs=None,
                                                          use_code_prompt=False,
                                                          coop_docs=None,
                                                          use_coop_prompt=False,
                                                          active_filters=getattr(state, 'active_filters', None))
                    updates.update({
                        "final_answer": project_ans,
                        "answer_citations": project_cites,
                        "graded_docs": forced_docs
                    })
                
                if code_db_enabled and code_docs:
                    code_ans, code_cites = synthesize(state.user_query, [], state.session_id, 
                                                      project_metadata=None,
                                                      code_docs=code_docs,
                                                      use_code_prompt=True,
                                                      coop_docs=None,
                                                      use_coop_prompt=False,
                                                      active_filters=getattr(state, 'active_filters', None))
                    updates.update({
                        "code_answer": code_ans,
                        "code_citations": code_cites
                    })
                
                if coop_db_enabled and coop_docs:
                    coop_ans, coop_cites = synthesize(state.user_query, [], state.session_id, 
                                                      project_metadata=None,
                                                      code_docs=None,
                                                      use_code_prompt=False,
                                                      coop_docs=coop_docs,
                                                      use_coop_prompt=True,
                                                      active_filters=getattr(state, 'active_filters', None))
                    updates.update({
                        "coop_answer": coop_ans,
                        "coop_citations": coop_cites
                    })
            elif code_docs and not project_db_enabled and not coop_db_enabled:
                # Code-only mode
                code_ans, code_cites = synthesize(state.user_query, [], state.session_id, 
                                                  project_metadata=None,
                                                  code_docs=code_docs,
                                                  use_code_prompt=True,
                                                  coop_docs=None,
                                                  use_coop_prompt=False,
                                                  active_filters=getattr(state, 'active_filters', None))
                updates.update({
                    "code_answer": code_ans,
                    "code_citations": code_cites,
                    "graded_docs": []
                })
            elif coop_docs and not project_db_enabled and not code_db_enabled:
                # Coop-only mode
                coop_ans, coop_cites = synthesize(state.user_query, [], state.session_id, 
                                                  project_metadata=None,
                                                  code_docs=None,
                                                  use_code_prompt=False,
                                                  coop_docs=coop_docs,
                                                  use_coop_prompt=True,
                                                  active_filters=getattr(state, 'active_filters', None))
                updates.update({
                    "coop_answer": coop_ans,
                    "coop_citations": coop_cites,
                    "graded_docs": []
                })
            else:
                # Project-only mode or combined
                ans, cites = synthesize(state.user_query, forced_docs, state.session_id, 
                                       project_metadata=pre_fetched_metadata,
                                       code_docs=code_docs if code_docs else None,
                                       use_code_prompt=False,
                                       coop_docs=coop_docs if coop_docs else None,
                                       use_coop_prompt=False,
                                       active_filters=getattr(state, 'active_filters', None))
                updates.update({
                    "final_answer": ans,
                    "answer_citations": cites,
                    "graded_docs": forced_docs
                })

        t_elapsed = time.time() - t_start
        log_enh.info(f"<<< VERIFY DONE (fix={'needed' if unknown else 'applied'}) in {t_elapsed:.2f}s")
        return updates

    except Exception as e:
        log_enh.error(f"LLM verifier failed: {e}")
        t_elapsed = time.time() - t_start
        log_enh.info(f"<<< VERIFY DONE (with error) in {t_elapsed:.2f}s")
        return {"needs_fix": False}

def _verify_route(state: RAGState) -> str:
    """Route based on whether verification flagged issues"""
    return "fix" if getattr(state, "needs_fix", False) else "ok"

def node_correct(state: RAGState, max_hops: int = 1, min_score: float = 0.6) -> dict:
    """Simplified corrective step - optionally calculate support score."""
    t_start = time.time()
    log_enh.info(">>> CORRECT START")

    if state.corrective_attempted:
        t_elapsed = time.time() - t_start
        log_enh.info(f"<<< CORRECT DONE (already attempted) in {t_elapsed:.2f}s")
        return {}

    # Calculate support score only if enabled
    if USE_SUPPORT_SCORING:
        score = support_score(state.user_query, state.final_answer or "", state.graded_docs)
        log_enh.info(f"Support score: {score:.2f}")
    else:
        score = 1.0  # Default to 1.0 when scoring is disabled
        log_enh.info(f"Support scoring disabled - using default score: {score:.2f}")

    t_elapsed = time.time() - t_start
    log_enh.info(f"<<< CORRECT DONE in {t_elapsed:.2f}s")

    return {"answer_support_score": score, "corrective_attempted": True}


    #hop = 0 ---------------------------------------------------REMOVE HOP FOR NOW------------------------------

    """ while score < min_score and hop < max_hops:
        hop += 1
        log_enh.info(f"Corrective hop {hop}: score={score:.2f}")

        better_q = reformulate(state.user_query, state.graded_docs)
        # Router should have run if project_db was enabled, so use route or default to smart
        route = state.data_route if (hasattr(state, 'data_route') and state.data_route) else "smart"
        r = make_hybrid_retriever(state.project_filter, route=route)
        new_docs = r(better_q, k=MAX_CORRECTIVE_DOCS)

        graded = self_grade(state.user_query, new_docs)
        ans, cites = synthesize(state.user_query, graded, state.session_id)

        new_score = support_score(state.user_query, ans, graded)

        if new_score > score:
            state.final_answer, state.answer_citations, state.answer_support_score = ans, cites, new_score
            score = new_score
            log_enh.info(f"Hop {hop} improved support to {new_score:.2f}")
        else:
            break """

    return state

# 8) Build the LangGraph ------------------------------------------------------------
def build_graph():
    if not HAS_LANGGRAPH_FULL or StateGraph is None:
        raise ImportError("LangGraph is not available. Please install langgraph package.")
    g = StateGraph(RAGState)

    # nodes
    g.add_node("plan",     node_plan)
    g.add_node("route",    node_route)
    g.add_node("generate_image_embeddings", node_generate_image_embeddings)  # NEW: Image embedding generation
    g.add_node("image_similarity", node_image_similarity_search)  # NEW: Image similarity search
    g.add_node("retrieve", node_retrieve)
    g.add_node("grade",    node_grade)
    g.add_node("answer",   node_answer)
    g.add_node("verify",   node_verify)
    g.add_node("correct",  node_correct)

    # entry
    g.set_entry_point("plan")

    # linear part
    g.add_edge("plan", "route")
    
    # Conditional: After route, check if we need image similarity search
    def should_use_image_search(state: RAGState) -> str:
        """Determine if we should run image similarity search"""
        if state.use_image_similarity and state.images_base64:
            return "generate_image_embeddings"
        return "retrieve"  # Default to existing path
    
    g.add_conditional_edges(
        "route",
        should_use_image_search,
        {
            "generate_image_embeddings": "generate_image_embeddings",
            "retrieve": "retrieve"
        }
    )
    
    # Image embedding generation always goes to image similarity search
    g.add_edge("generate_image_embeddings", "image_similarity")
    
    # Image similarity search feeds into retrieve (to merge results)
    g.add_edge("image_similarity", "retrieve")
    
    # Continue with existing flow
    g.add_edge("retrieve", "grade")
    g.add_edge("grade", "answer")
    g.add_edge("answer", "verify")

    # 🔁 conditional branch from verify
    g.add_conditional_edges(
        "verify",
        _verify_route,
        {"fix": "retrieve", "ok": "correct"}  # loop back only when verifier set needs_fix
    )

    g.add_edge("correct", END)

    return g.compile(checkpointer=memory)

# 9 = MEMORY ------------------------------------------------------------

def resolve_entity(user_q: str, session_id: str) -> Optional[str]:
    """Resolve references to specific entities (projects) from previous results."""
    prior = SESSION_MEMORY.get(session_id, {})
    items = prior.get("last_results", [])
    
    if DEBUG_MODE:
        print(f"\n=== DEBUG resolve_entity ===")
        print(f"Query: '{user_q}'")
        print(f"Session ID: {session_id}")
        print(f"Prior memory keys: {list(prior.keys())}")
        print(f"Last results count: {len(items)}")
        print(f"Last results: {items}")
    
    if not items:
        if DEBUG_MODE:
            print("No items in last_results, returning None")
        return None
    
    project_list = "\n".join([
        f"{i+1}. Project {r['project']}"
        for i, r in enumerate(items)
    ])
    
    if DEBUG_MODE:
        print(f"Project list for LLM:\n{project_list}")
    
    prompt = f"""Previous projects discussed:
{project_list}

New question: {user_q}

Does this question ask about ONE SPECIFIC project from the list (e.g., "the second one", "project 25-07-018", "the first project")?

If YES: Return ONLY the project ID
If NO: Return "NONE"

Answer:"""
    
    try:
        if DEBUG_MODE:
            print(f"Sending prompt to LLM...")
        response = llm_fast.invoke(prompt).content.strip()
        if DEBUG_MODE:
            print(f"LLM response: '{response}'")
        
        match = PROJECT_RE.search(response)
        if match:
            if DEBUG_MODE:
                print(f"Found project ID in response: {match.group(0)}")
            return match.group(0)
        else:
            if DEBUG_MODE:
                print("No project ID found in response")
            return None
    except Exception as e:
        if DEBUG_MODE:
            print(f"Exception in resolve_entity: {e}")
        return None

# 10) Run / Integrate ------------------------------------------------------------
@(track_function if HAS_ENHANCED_LOGGER else lambda x: x)
def run_agentic_rag(question: str, session_id: str = "default", data_sources: Optional[Dict[str, bool]] = None, images_base64: Optional[List[str]] = None) -> Dict:
    # Check if required dependencies are available
    if not HAS_LANGGRAPH_FULL:
        return {
            "answer": "RAG system requires LangGraph. Please install: pip install langgraph",
            "citations": [],
            "support": 0.0,
            "route": "error"
        }
    
    if not HAS_LANGCHAIN:
        return {
            "answer": "RAG system requires LangChain. Please install: pip install langchain langchain-openai langchain-community",
            "citations": [],
            "support": 0.0,
            "route": "error"
        }
    
    t0 = time.time()
    graph = build_graph()

    prior = SESSION_MEMORY.get(session_id, {})
    prev_q = prior.get("last_query")

    # Log memory state
    log_query.info(f"=== SESSION MEMORY (session_id={session_id}) ===")
    if prior:
        conv_history = prior.get('conversation_history', [])
        log_query.info(f"  conversation_history: {len(conv_history)} exchanges")
        log_query.info(f"  last_query: {prior.get('last_query')}")
        log_query.info(f"  project_filter: {prior.get('project_filter')}")
        log_query.info(f"  selected_projects: {prior.get('selected_projects')}")
        log_query.info(f"  last_results: {len(prior.get('last_results', []))} items")
    else:
        log_query.info("  No prior memory for this session")

    # 🖼️ PROCESS IMAGES IF PROVIDED - Convert to searchable text via VLM
    image_context = ""
    if images_base64 and len(images_base64) > 0:
        log_vlm.info(f"🖼️ {len(images_base64)} image(s) attached - processing with VLM...")
        image_descriptions = []
        for i, image_base64 in enumerate(images_base64):
            try:
                image_description = describe_image_for_search(image_base64, question)
                image_descriptions.append(f"Image {i+1}: {image_description}")
                log_vlm.info(f"🖼️ VLM Description {i+1} extracted: {len(image_description)} chars")
            except Exception as e:
                log_vlm.error(f"🖼️ VLM processing failed for image {i+1}, skipping: {e}")
        
        if image_descriptions:
            image_context = "\n\n[Image Context: " + " | ".join(image_descriptions) + "]"
            log_vlm.info(f"🖼️ Combined image context: {len(image_context)} chars")

    # Combine question with image context for enhanced search
    enhanced_question = question + image_context if image_context else question

    # 🎯 IMAGE INTENT CLASSIFICATION - Determine if image similarity search is needed
    use_image_similarity = False
    query_intent = None
    
    if images_base64 and len(images_base64) > 0:
        intent_result = classify_image_query_intent(question, images_base64[0])
        use_image_similarity = intent_result.get("use_image_similarity", False)
        query_intent = intent_result.get("intent", None)
        log_vlm.info(f"🖼️ IMAGE INTENT CLASSIFICATION: intent={query_intent}, use_similarity={use_image_similarity}, confidence={intent_result.get('confidence', 0.0):.2f}")

    # 🎯 INTELLIGENT QUERY REWRITING - Replace old entity resolution logic
    log_query.info(f"🎯 QUERY REWRITING INPUT: '{enhanced_question[:500]}...' (truncated)" if len(enhanced_question) > 500 else f"🎯 QUERY REWRITING INPUT: '{enhanced_question}'")
    rewritten_query, query_filters = intelligent_query_rewriter(enhanced_question, session_id)
    log_query.info(f"🎯 QUERY REWRITING OUTPUT: '{rewritten_query}'")
    log_query.info(f"🎯 QUERY FILTERS: {query_filters}")
    
    # Extract project filter from query_filters
    project_filter = None
    if query_filters.get("project_keys"):
        project_filter = query_filters["project_keys"][0]  # Use first project for now
        log_query.info(f"🎯 PROJECT FILTER FROM REWRITER: {project_filter}")
    
    base_query = rewritten_query
    log_query.info(f"🎯 FINAL QUERY FOR RAG: '{base_query}'")

    if data_sources is None:
        data_sources = {"project_db": True, "code_db": False, "coop_manual": False}
    
    init = RAGState(
        session_id=session_id,
        user_query=base_query,
        query_plan=None, data_route=None,
        project_filter=project_filter,
        expanded_queries=[], retrieved_docs=[], graded_docs=[],
        db_result=None, final_answer=None,
        answer_citations=[], code_answer=None, code_citations=[],
        coop_answer=None, coop_citations=[],
        answer_support_score=0.0,
        corrective_attempted=False,
        data_sources=data_sources,
        # Image similarity search fields (optional - won't affect existing pipeline)
        images_base64=images_base64 if images_base64 else None,
        use_image_similarity=use_image_similarity,
        query_intent=query_intent
    )

    # Convert dataclass to dict - graph.invoke expects a dict, not a dataclass
    final = graph.invoke(asdict(init), config={"configurable": {"thread_id": session_id}})

    # Normalize dict vs. object - LangGraph can return either
    if isinstance(final, dict):
        # Convert dict to RAGState with ALL required fields
        final_state = RAGState(
            session_id=final.get("session_id", session_id),
            user_query=final.get("user_query", base_query),
            query_plan=final.get("query_plan"),
            data_route=final.get("data_route"),
            project_filter=final.get("project_filter"),
            expanded_queries=final.get("expanded_queries", []),
            retrieved_docs=final.get("retrieved_docs", []),
            graded_docs=final.get("graded_docs", []),
            db_result=final.get("db_result"),
            final_answer=final.get("final_answer"),
            answer_citations=final.get("answer_citations", []),
            code_answer=final.get("code_answer"),
            code_citations=final.get("code_citations", []),
            coop_answer=final.get("coop_answer"),
            coop_citations=final.get("coop_citations", []),
            answer_support_score=final.get("answer_support_score", 0.0),
            corrective_attempted=final.get("corrective_attempted", False),
            needs_fix=final.get("needs_fix", False),
            selected_projects=final.get("selected_projects", []),
            # Image similarity fields (optional)
            images_base64=final.get("images_base64"),
            image_embeddings=final.get("image_embeddings"),
            image_similarity_results=final.get("image_similarity_results", []),
            use_image_similarity=final.get("use_image_similarity", False),
            query_intent=final.get("query_intent")
        )
    else:
        final_state = final

    # Extract projects from ACTUAL ANSWER TEXT (not just citations)
    # Use regex to find project IDs mentioned in the answer
    answer_text = final_state.final_answer or ""
    projects_in_answer = []
    seen_in_answer = set()

    # Find all project IDs in the answer text (format: YY-MM-XXX)
    project_matches = PROJECT_RE.finditer(answer_text)
    for match in project_matches:
        proj_id = match.group(0)
        if proj_id not in seen_in_answer:
            projects_in_answer.append(proj_id)
            seen_in_answer.add(proj_id)

    log_query.info(f"📋 Projects extracted from answer text: {projects_in_answer}")

    # Build result items from ANSWER TEXT projects only (for entity resolution)
    result_items = []
    for proj_id in projects_in_answer:
        result_items.append({"project": proj_id})

    log_query.info(f"📋 Result items for entity resolution: {[r['project'] for r in result_items]}")

    # Update conversation memory with sliding window
    session_data = SESSION_MEMORY.get(session_id, {})
    conversation_history = session_data.get("conversation_history", [])

    log_query.info("💾 UPDATING CONVERSATION MEMORY:")
    log_query.info(f"   Current history size: {len(conversation_history)} exchanges")

    # Append new exchange to conversation history
    # Include all answers if multiple databases were queried
    answer_text = final_state.final_answer or ""
    if final_state.code_answer:
        answer_text = f"{answer_text}\n\n--- Code References ---\n\n{final_state.code_answer}"
    if final_state.coop_answer:
        answer_text = f"{answer_text}\n\n--- Training Manual References ---\n\n{final_state.coop_answer}"
    
    new_exchange = {
        "question": question,  # Original question asked by user
        "answer": answer_text,  # Combined answer (project + code if both exist)
        "timestamp": time.time(),
        "projects": projects_in_answer  # Projects mentioned in this answer
    }
    conversation_history.append(new_exchange)

    log_query.info(f"   Added new exchange:")
    log_query.info(f"      Q: {question[:100]}...")
    log_query.info(f"      A: {(answer_text or '')[:100]}...")
    log_query.info(f"      Projects in answer: {projects_in_answer}")

    # Maintain sliding window - keep only last MAX_CONVERSATION_HISTORY exchanges
    if len(conversation_history) > MAX_CONVERSATION_HISTORY:
        dropped = len(conversation_history) - MAX_CONVERSATION_HISTORY
        conversation_history = conversation_history[-MAX_CONVERSATION_HISTORY:]
        log_query.info(f"   ⚠️  Sliding window: Dropped {dropped} oldest exchange(s), keeping last {MAX_CONVERSATION_HISTORY}")

    log_query.info(f"   Final history size: {len(conversation_history)} exchanges")

    # SEMANTIC INTELLIGENCE: Gather semantic data from graph execution
    current_semantic = {}
    
    # Capture planning intelligence if available
    if hasattr(final_state, '_planning_intelligence'):
        current_semantic["planning"] = final_state._planning_intelligence
        log_query.info(f"📊 CAPTURED PLANNING INTELLIGENCE: {final_state._planning_intelligence.get('complexity_assessment', 'unknown')}")
    
    # Capture routing intelligence if available  
    if hasattr(final_state, '_routing_intelligence'):
        current_semantic["routing"] = final_state._routing_intelligence
        log_query.info(f"📊 CAPTURED ROUTING INTELLIGENCE: {final_state._routing_intelligence.get('data_route', 'unknown')}")
    
    # Capture execution intelligence if available
    if hasattr(final_state, '_execution_intelligence'):
        current_semantic["execution"] = final_state._execution_intelligence
        log_query.info(f"📊 CAPTURED EXECUTION INTELLIGENCE: {len(final_state._execution_intelligence.get('operations_performed', []))} operations")
    
    # Get existing semantic history and manage sliding window
    session_data = SESSION_MEMORY.get(session_id, {})
    semantic_history = session_data.get("semantic_history", [])
    
    # Add current semantic intelligence to history
    if current_semantic:  # Only add if we captured semantic data
        semantic_history.append(current_semantic)
        
        # Maintain sliding window for semantic history
        if len(semantic_history) > MAX_SEMANTIC_HISTORY:
            dropped = len(semantic_history) - MAX_SEMANTIC_HISTORY
            semantic_history = semantic_history[-MAX_SEMANTIC_HISTORY:]
            log_query.info(f"   🧠 Semantic sliding window: Dropped {dropped} oldest semantic record(s), keeping last {MAX_SEMANTIC_HISTORY}")
    
    log_query.info(f"   🧠 Semantic history size: {len(semantic_history)} records")

    # Update session memory
    SESSION_MEMORY[session_id] = {
        "conversation_history": conversation_history,
        "project_filter": final_state.project_filter,
        "last_query": question,  # For backward compatibility
        "last_answer": final_state.final_answer,  # For backward compatibility
        "last_results": [r for r in result_items if r.get("project")],
        "selected_projects": final_state.selected_projects,
        # NEW: Semantic intelligence
        "semantic_history": semantic_history,
        "last_semantic": current_semantic  # Quick access to most recent semantic data
    }

    log_query.info("   ✅ Session memory updated successfully")
    
    # 🎯 UPDATE FOCUS STATE for intelligent query rewriting
    update_focus_state(
        session_id=session_id,
        query=question,  # Original user query
        projects=projects_in_answer,  # Projects mentioned in answer
        results_projects=final_state.selected_projects  # Projects from retrieval results
    )
    
    # Also update the focus state with last_answer_projects for follow-up detection
    if session_id in FOCUS_STATES:
        FOCUS_STATES[session_id]["last_answer_projects"] = projects_in_answer
        log_query.info(f"🎯 UPDATED LAST ANSWER PROJECTS: {projects_in_answer}")

    # Log final memory state summary
    log_query.info("📊 FINAL MEMORY STATE:")
    log_query.info(f"   Session ID: {session_id}")
    log_query.info(f"   Total exchanges stored: {len(conversation_history)}")
    log_query.info(f"   Total unique projects in memory: {len(set(p for ex in conversation_history for p in ex.get('projects', [])))}")
    log_query.info(f"   Current project filter: {final_state.project_filter or 'None'}")

    latency = round(time.time() - t0, 2)

    graded_preview = []
    for d in (final_state.graded_docs or [])[:MAX_CITATIONS_DISPLAY]:
        md = d.metadata or {}
        graded_preview.append({
            "project": md.get("drawing_number") or md.get("project_key"),
            "page": md.get("page_id") or md.get("page"),
            "title": md.get("title"),
            "content": d.page_content[:500] if d.page_content else "",  # First 500 chars
            "search_type": md.get("search_type", "unknown"),
        })
    plan_for_ui = final_state.query_plan if isinstance(final_state.query_plan, dict) else {}
    return {
        "answer": final_state.final_answer,
        "code_answer": final_state.code_answer,  # Separate code answer if code database enabled
        "coop_answer": final_state.coop_answer,  # Separate coop answer if coop database enabled
        "support": round(final_state.answer_support_score, 3),
        "citations": final_state.answer_citations,
        "code_citations": final_state.code_citations,  # Separate code citations if code database enabled
        "coop_citations": final_state.coop_citations,  # Separate coop citations if coop database enabled
        "route": final_state.data_route,
        "project_filter": final_state.project_filter,
        "expanded_queries": final_state.expanded_queries[:MAX_ROUTER_DOCS],
        "latency_s": latency,
        "graded_preview": graded_preview,
        "plan": {
            "reasoning": plan_for_ui.get("reasoning", ""),
            "steps": plan_for_ui.get("steps", []),
            "subqueries": plan_for_ui.get("subqueries", []),
        },
        "image_similarity_results": final_state.image_similarity_results or [],  # Similar images from embedding search
    }


def rag_healthcheck() -> Dict:
    project_db_status = test_database_connection()

    # Check Supabase vector stores and project info
    supabase_status = {
        "vs_smart": vs_smart is not None,
        "vs_large": vs_large is not None,
        "project_info": project_db_status
    }

    # Try to get document counts from Supabase
    try:
        if vs_smart is not None:
            _supa = create_client(SUPABASE_URL, SUPABASE_KEY)
            smart_count = _supa.table(SUPA_SMART_TABLE).select("*", count="exact").limit(1).execute()
            supabase_status["smart_count"] = smart_count.count
        if vs_large is not None:
            _supa = create_client(SUPABASE_URL, SUPABASE_KEY)
            large_count = _supa.table(SUPA_LARGE_TABLE).select("*", count="exact").limit(1).execute()
            supabase_status["large_count"] = large_count.count
    except Exception as e:
        supabase_status["error"] = str(e)

    return {
        "openai_key": bool(os.getenv("OPENAI_API_KEY")),
        "model": FAST_MODEL,  # Use FAST_MODEL as default
        "supabase": supabase_status
    }

# =============================================================================
# SearchOrchestrator Class - Wraps RAG system for TeamOrchestrator integration
# =============================================================================

# Import BaseAgent and execution trace
import sys
from pathlib import Path
from typing import TypedDict

# Add parent directory to path for imports
_agents_dir = Path(__file__).parent
_localagent_dir = _agents_dir.parent
sys.path.insert(0, str(_localagent_dir))

try:
    from agents.base_agent import BaseAgent, AgentState
    from execution.trace import ExecutionTrace, ExecutionStep, StepStatus, ExecutionStatus, create_step
    HAS_BASE_AGENT = True
except ImportError as e:
    print(f"WARNING: Failed to import BaseAgent: {e}")
    HAS_BASE_AGENT = False
    BaseAgent = None
    AgentState = None

# Try to import tools for metadata search LangGraph
try:
    from tools import ALL_TOOLS
    HAS_TOOLS = True
except ImportError:
    ALL_TOOLS = []
    HAS_TOOLS = False

# Try to import LangGraph for metadata search workflow
try:
    from langgraph.graph import StateGraph, END
    HAS_LANGGRAPH = True
except ImportError:
    HAS_LANGGRAPH = False
    StateGraph = None
    END = None


class ExecutionState(TypedDict, total=False):
    """State object for LangGraph metadata search execution."""
    user_query: str
    available_outputs: Dict[str, Any]
    results: Dict[str, Any]
    errors: List[str]
    trace: List[Dict[str, Any]]


if HAS_BASE_AGENT and BaseAgent:
    class SearchOrchestrator(BaseAgent):
        """
        Search Orchestrator that integrates RAG system with LangGraph metadata search.
        
        Uses strategic planning from TeamOrchestrator to decide:
        - When to use RAG (document search)
        - When to use LangGraph metadata search (project search)
        - When to use both
        """
        
        def __init__(self, api_key: Optional[str] = None, tools: List = None):
            super().__init__(name="search_orchestrator", tools=tools or ALL_TOOLS)
            self.api_key = api_key or os.getenv("OPENAI_API_KEY")
            self.tools = tools or ALL_TOOLS
            
            # Build LangGraph workflow for metadata search if tools available
            self.metadata_workflow = None
            if HAS_LANGGRAPH and self.tools:
                try:
                    self.metadata_workflow = self._build_metadata_langgraph()
                except Exception as e:
                    print(f"WARNING: Failed to build metadata LangGraph: {e}")
        
        def _build_metadata_langgraph(self):
            """Build LangGraph workflow for metadata search (from search_orchestratorr1.py)."""
            if not HAS_LANGGRAPH:
                return None
            
            tools_dict = {tool.__name__: tool for tool in self.tools}
            
            workflow = StateGraph(ExecutionState)
            
            # Node: extract_search_criteria
            def extract_node(state: ExecutionState) -> ExecutionState:
                tool_func = tools_dict.get("extract_search_criteria")
                if tool_func:
                    try:
                        state.setdefault("trace", []).append({
                            "step": "extract_search_criteria",
                            "thinking": f"Extracting search criteria from: '{state.get('user_query', '')}'",
                            "inputs": {"user_query": state.get("user_query")},
                            "status": "running"
                        })
                        result = tool_func(user_query=state.get("user_query", ""))
                        state.setdefault("available_outputs", {}).update(result)
                        dim_constraints = result.get("dimension_constraints", {})
                        is_complete = dim_constraints.get("complete", False) if isinstance(dim_constraints, dict) else False
                        
                        state["trace"][-1].update({
                            "outputs": result,
                            "status": "completed",
                            "thinking": f"Extracted criteria: {result}. Complete: {is_complete}"
                        })
                    except Exception as e:
                        state.setdefault("errors", []).append(f"extract_search_criteria: {str(e)}")
                return state
            
            # Node: search_projects_by_dimensions
            def search_node(state: ExecutionState) -> ExecutionState:
                tool_func = tools_dict.get("search_projects_by_dimensions")
                if tool_func:
                    try:
                        dim_constraints = state.get("available_outputs", {}).get("dimension_constraints", {})
                        state.setdefault("trace", []).append({
                            "step": "search_projects_by_dimensions",
                            "thinking": f"Searching Supabase via GraphQL for projects matching: {dim_constraints}",
                            "inputs": {"dimension_constraints": dim_constraints},
                            "status": "running"
                        })
                        result = tool_func(dimension_constraints=dim_constraints)
                        if isinstance(result, list):
                            state.setdefault("available_outputs", {})["candidate_projects"] = result
                        state["trace"][-1].update({
                            "outputs": {"candidate_projects": result},
                            "status": "completed"
                        })
                    except Exception as e:
                        state.setdefault("errors", []).append(f"search_projects_by_dimensions: {str(e)}")
                return state
            
            # Node: retrieve_project_metadata
            def retrieve_node(state: ExecutionState) -> ExecutionState:
                tool_func = tools_dict.get("retrieve_project_metadata")
                if tool_func:
                    try:
                        candidates = state.get("available_outputs", {}).get("candidate_projects", [])
                        project_ids = [p.get("project_id") for p in candidates[:5]]  # Top 5
                        state.setdefault("trace", []).append({
                            "step": "retrieve_project_metadata",
                            "thinking": f"Retrieving metadata for {len(project_ids)} projects",
                            "inputs": {"project_ids": project_ids},
                            "status": "running"
                        })
                        result = tool_func(project_ids=project_ids)
                        state.setdefault("results", {})["project_summaries"] = result
                        state["trace"][-1].update({
                            "outputs": {"project_summaries": result},
                            "status": "completed"
                        })
                    except Exception as e:
                        state.setdefault("errors", []).append(f"retrieve_project_metadata: {str(e)}")
                return state
            
            workflow.add_node("extract", extract_node)
            workflow.add_node("search", search_node)
            workflow.add_node("retrieve", retrieve_node)
            workflow.set_entry_point("extract")
            workflow.add_edge("extract", "search")
            workflow.add_edge("search", "retrieve")
            workflow.add_edge("retrieve", END)
            
            return workflow.compile()
        
        def execute(self, task: str, context: Dict = None) -> Dict:
            """
            Execute search using RAG and/or metadata search based on strategic planning.
            
            Args:
                task: User query
                context: Context from TeamOrchestrator (includes planning, session_id, data_sources)
                
            Returns:
                Dict with results, trace, planning info
            """
            context = context or {}
            
            # Initialize state
            self.state = AgentState(
                task=task,
                context=context,
                completed_steps=[],
                results={}
            )
            
            # Create execution trace
            trace = ExecutionTrace()
            trace.available_outputs = {"user_query": task}
            
            # Get strategic planning from TeamOrchestrator
            strategic_planning = context.get("planning", {})
            intent = strategic_planning.get("intent", "general")
            data_sources_list = strategic_planning.get("data_sources", [])
            strategy = strategic_planning.get("strategy", "document_first")
            
            # Get capability registry to know what's actually available
            try:
                from localagent.core.capability_registry import get_registry
                registry = get_registry()
            except ImportError:
                registry = None
            
            # Generate detailed tactical plan (like Cursor's step-by-step)
            tactical_plan = self._generate_tactical_plan(
                intent=intent,
                data_sources=data_sources_list,
                strategy=strategy,
                task=task,
                registry=registry
            )
            
            # Add tactical plan to trace
            trace.thinking_log.append(tactical_plan)
            
            # Log strategic planning with detailed explanation
            trace.thinking_log.append(f"## 🎯 Strategic Planning\n\n**What I'm analyzing:** Your query to determine the best approach.\n\n**Intent Classification:** {intent}\n- This tells me what type of query you're asking (project search, design guidance, etc.)\n\n**Data Sources Selected:** {', '.join(data_sources_list)}\n- These are the systems I'll query to find your answer\n\n**Execution Strategy:** {strategy}\n- This determines the order and approach I'll use to get the information\n\n**My reasoning:** Based on your query, I've determined this is the most efficient way to find what you're looking for.")
            
            # Convert strategic planning data_sources list to RAG format dict
            # Strategic planning uses: ["rag_documents", "rag_codes", "supabase_metadata"]
            # RAG expects: {"project_db": True, "code_db": False, "coop_manual": False}
            data_sources_config = context.get("data_sources", {})
            if not data_sources_config or not isinstance(data_sources_config, dict):
                # Convert from strategic planning format
                data_sources_config = {
                    "project_db": any("rag_documents" in src.lower() or "document" in src.lower() for src in data_sources_list),
                    "code_db": any("rag_codes" in src.lower() or "code" in src.lower() for src in data_sources_list),
                    "coop_manual": any("rag_internal" in src.lower() or "coop" in src.lower() or "internal" in src.lower() for src in data_sources_list)
                }
            
            # Determine what to execute
            # ALWAYS run RAG for search queries - it embeds and searches Supabase vector stores
            # This is the core functionality - embedding the query and searching smart_chunks, page_chunks, etc.
            needs_rag = True  # Always run RAG - it's what does the embedding and Supabase search
            needs_metadata = any("supabase" in src.lower() or "metadata" in src.lower() or "graphql" in src.lower() for src in data_sources_list)
            
            rag_result = None
            metadata_result = None
            
            # Execute RAG - this embeds the query and searches Supabase vector stores
            if needs_rag:
                try:
                    session_id = context.get("session_id", "default")
                    images_base64 = context.get("images_base64")
                    
                    trace.thinking_log.append(f"## 📚 Starting RAG Search\n\n**What I'm doing:** Embedding your query and searching Supabase vector stores (smart_chunks, page_chunks, code_chunks, coop_chunks) to find relevant documents.\n\n**Your query:** '{task}'\n\n**Searching in:**\n- Project documents: {'Yes' if data_sources_config.get('project_db', False) else 'No'}\n- Code references: {'Yes' if data_sources_config.get('code_db', False) else 'No'}\n- Coop manual: {'Yes' if data_sources_config.get('coop_manual', False) else 'No'}\n\n**How it works:**\n1. Convert your query to a vector embedding\n2. Search for similar document chunks in Supabase\n3. Retrieve the most relevant chunks\n4. Generate an answer based on the retrieved content")
                    
                    # Check if Supabase is configured before attempting RAG
                    if not SUPABASE_URL or not SUPABASE_KEY:
                        trace.thinking_log.append(f"⚠️ Supabase not configured - RAG requires vector stores")
                        rag_result = {
                            "answer": "RAG search requires Supabase configuration. Please set SUPABASE_URL and SUPABASE_ANON_KEY in your .env file.",
                            "citations": []
                        }
                    else:
                        # This is the core RAG function - embeds query and searches Supabase
                        # Same as backend/RAG/rag.py - uses vs_smart, vs_large, vs_code, vs_coop vector stores
                        rag_result = run_agentic_rag(
                            question=task,
                            session_id=session_id,
                            data_sources=data_sources_config,
                            images_base64=images_base64
                        )
                        answer = rag_result.get('answer', '')
                        answer_len = len(answer) if answer else 0
                        citations_count = len(rag_result.get('citations', []))
                        trace.thinking_log.append(f"## ✅ RAG Search Complete\n\n**Results:**\n- Answer generated: {answer_len} characters\n- Citations found: {citations_count} documents\n\n**What happened:**\n1. ✅ Query embedded successfully\n2. ✅ Searched Supabase vector stores\n3. ✅ Retrieved {citations_count} relevant document chunks\n4. ✅ Generated answer from retrieved content\n\n*Note: The final answer is shown in the chat panel. This log shows the process, not the answer itself.*")
                        if not answer or not answer.strip():
                            trace.thinking_log.append(f"## ⚠️ Warning: Empty Answer\n\n**Issue:** RAG search completed but returned an empty answer.\n\n**Debug info:**\n- Result keys: {list(rag_result.keys())}\n- Result preview: {str(rag_result)[:300]}\n\n**Possible reasons:**\n- No relevant documents found in database\n- Query didn't match any content\n- Answer generation failed")
                except Exception as e:
                    trace.thinking_log.append(f"⚠️ RAG failed: {str(e)}")
                    rag_result = {
                        "answer": f"RAG search encountered an error: {str(e)}",
                        "citations": []
                    }
            
            # Execute metadata search if needed (works even without Supabase - uses GraphQL)
            if needs_metadata:
                try:
                    if self.metadata_workflow:
                        trace.thinking_log.append(f"🔍 Starting metadata search via LangGraph...")
                        metadata_state = ExecutionState({
                            "user_query": task,
                            "available_outputs": {},
                            "results": {},
                            "errors": [],
                            "trace": []
                        })
                        metadata_final = self.metadata_workflow.invoke(metadata_state)
                        metadata_result = metadata_final.get("results", {})
                        trace.thinking_log.append(f"🔍 Metadata search completed")
                    elif self.tools:
                        # Fallback: Use tools directly if LangGraph workflow not available
                        trace.thinking_log.append(f"🔍 Starting metadata search via tools (LangGraph not available)...")
                        try:
                            from tools import extract_search_criteria, search_projects_by_dimensions, retrieve_project_metadata
                            
                            # Extract criteria
                            criteria = extract_search_criteria(user_query=task)
                            dim_constraints = criteria.get("dimension_constraints", {})
                            
                            # Search projects
                            if dim_constraints and dim_constraints.get("complete"):
                                search_result = search_projects_by_dimensions(dimension_constraints=dim_constraints)
                                project_summaries = search_result.get("project_summaries", [])
                                
                                # Get project IDs and retrieve full metadata
                                project_ids = [p.get("project_id") for p in project_summaries if p.get("project_id")]
                                if project_ids:
                                    full_metadata = retrieve_project_metadata(project_ids=project_ids)
                                    # Merge search results with full metadata
                                    for summary in project_summaries:
                                        project_id = summary.get("project_id")
                                        if project_id:
                                            metadata = next((m for m in full_metadata if m.get("id") == project_id), {})
                                            summary.update(metadata)
                                
                                metadata_result = {
                                    "project_summaries": project_summaries,
                                    "total_found": search_result.get("total_found", len(project_summaries))
                                }
                            else:
                                metadata_result = {"project_summaries": [], "total_found": 0}
                            
                            trace.thinking_log.append(f"🔍 Metadata search completed via tools: {metadata_result.get('total_found', 0)} projects found")
                        except Exception as e:
                            trace.thinking_log.append(f"⚠️ Tool-based metadata search failed: {str(e)}")
                            import traceback
                            trace.thinking_log.append(f"   Error details: {traceback.format_exc()}")
                            metadata_result = None
                    else:
                        trace.thinking_log.append(f"⚠️ Metadata search not available - no tools or workflow")
                        metadata_result = None
                except Exception as e:
                    trace.thinking_log.append(f"⚠️ Metadata search failed: {str(e)}")
                    import traceback
                    trace.thinking_log.append(f"   Error details: {traceback.format_exc()}")
                    metadata_result = None
            
            # Combine results - format for backend
            final_results = {}
            
            # Get RAG answer (check if it's valid)
            rag_answer = rag_result.get("answer", "") if rag_result else ""
            has_valid_answer = rag_answer and rag_answer.strip() and len(rag_answer.strip()) > 10  # At least 10 chars
            
            # RAG results
            if rag_result:
                if has_valid_answer:
                    # Backend expects "answer" - use the RAG answer
                    final_results["answer"] = rag_answer
                else:
                    # RAG ran but answer is empty/None - log this
                    trace.thinking_log.append(f"⚠️ RAG returned empty answer (length: {len(rag_answer) if rag_answer else 0})")
                
                final_results["citations"] = rag_result.get("citations", [])
                # Also include raw RAG result for reference
                final_results["rag_answer"] = rag_answer
                final_results["rag_citations"] = rag_result.get("citations", [])
            
            # Metadata results (project search)
            if metadata_result:
                final_results.update(metadata_result)
            
            # Ensure we have an answer - prioritize RAG answer, then project summaries, then fallback
            if not final_results.get("answer") or not final_results["answer"].strip():
                if has_valid_answer:
                    final_results["answer"] = rag_answer
                elif metadata_result and metadata_result.get("project_summaries"):
                    # If we have project summaries but no answer, format them
                    summaries = metadata_result.get("project_summaries", [])
                    if summaries:
                        final_results["answer"] = f"Found {len(summaries)} matching project(s)."
                    else:
                        final_results["answer"] = "No matching projects found."
                elif rag_result:
                    # RAG ran but returned empty answer
                    final_results["answer"] = "I searched the database but couldn't generate a specific answer. The retrieved documents may not contain enough information to answer your question. Please try rephrasing or being more specific."
                else:
                    final_results["answer"] = "No results found."
            
            return {
                "results": final_results,
                "trace": trace,
                "planning": strategic_planning,
                "success": True
            }
        
        def _generate_tactical_plan(self, intent: str, data_sources: List[str], strategy: str, task: str, registry=None) -> str:
            """
            Generate detailed tactical execution plan (like Cursor's detailed steps).
            
            Shows:
            - Which tables will be searched
            - Which tools will be used
            - Why each step is taken
            """
            plan_lines = [
                "## 🔍 Detailed Execution Plan",
                "",
                f"**Strategic Intent:** {intent}",
                f"**Data Sources:** {', '.join(data_sources) if data_sources else 'None'}",
                f"**Strategy:** {strategy}",
                "",
                "**Tactical Steps:**",
                ""
            ]
            
            # Determine which tables will be searched based on data_sources
            tables_to_search = []
            if "rag_documents" in data_sources:
                tables_to_search.append(("smart_chunks", "Project documents with detailed features"))
            if "rag_codes" in data_sources:
                tables_to_search.append(("code_chunks", "Building codes and standards"))
            if "rag_internal_docs" in data_sources:
                tables_to_search.append(("coop_chunks", "Company processes and training manuals"))
            
            # Step 1: Query Analysis
            plan_lines.append("1. **Query Analysis**")
            plan_lines.append(f"   - Extract: \"{task}\"")
            plan_lines.append(f"   - Query type: {intent.replace('_', ' ').title()}")
            if tables_to_search:
                table_names = [t[0] for t in tables_to_search]
                plan_lines.append(f"   - Tables needed: {', '.join(table_names)}")
            plan_lines.append("")
            
            # Step 2: Vector Search
            if tables_to_search:
                plan_lines.append("2. **Vector Search**")
                for table_name, description in tables_to_search:
                    plan_lines.append(f"   - Table: `{table_name}`")
                    plan_lines.append(f"   - Query: \"{task}\" (embedded)")
                    plan_lines.append(f"   - Expected: ~50 document chunks")
                    plan_lines.append(f"   - Why: {description}")
                plan_lines.append("")
            
            # Step 3: Document Grading
            plan_lines.append("3. **Document Grading**")
            plan_lines.append("   - Tool: LLM relevance scoring")
            plan_lines.append("   - Filter: Keep top 45 chunks (relevance >= 0.7)")
            plan_lines.append("   - Why: Ensure only relevant projects are included")
            plan_lines.append("")
            
            # Step 4: Project Metadata Retrieval (if project search)
            step_num = 4
            if intent == "project_search" and "rag_documents" in data_sources:
                plan_lines.append("4. **Project Metadata Retrieval**")
                plan_lines.append("   - Tool: `fetch_project_metadata`")
                plan_lines.append("   - Projects: Extract from graded chunks")
                plan_lines.append("   - Why: Enrich with dimensions, types, materials")
                plan_lines.append("")
                step_num = 5
            
            # Step 5: Answer Synthesis
            plan_lines.append(f"{step_num}. **Answer Synthesis**")
            plan_lines.append("   - Tool: LLM synthesis")
            plan_lines.append("   - Input: Graded chunks + metadata")
            plan_lines.append("   - Output: Formatted answer with citations")
            plan_lines.append("")
            
            # Step 6: Verification
            plan_lines.append(f"{step_num + 1}. **Verification**")
            plan_lines.append("   - Tool: LLM verification")
            plan_lines.append("   - Check: Completeness, accuracy")
            plan_lines.append("   - Fix: If needed, re-retrieve and re-synthesize")
            
            return "\n".join(plan_lines)
else:
    # Fallback: Create a minimal SearchOrchestrator if BaseAgent not available
    class SearchOrchestrator:
        def __init__(self, api_key=None, tools=None):
            self.name = "search_orchestrator"
            self.tools = tools or []
            self.api_key = api_key
            self.metadata_workflow = None
        
        def execute(self, task: str, context: Dict = None) -> Dict:
            """Fallback execute - just use RAG."""
            context = context or {}
            session_id = context.get("session_id", "default")
            data_sources_config = context.get("data_sources", {})
            images_base64 = context.get("images_base64")
            
            result = run_agentic_rag(
                question=task,
                session_id=session_id,
                data_sources=data_sources_config,
                images_base64=images_base64
            )
            
            return {
                "results": {
                    "rag_answer": result.get("answer", ""),
                    "rag_citations": result.get("citations", [])
                },
                "success": True
            }


if __name__ == "__main__":
    q = "What are the roof truss bracing notes for 25-07-003?"
    result = run_agentic_rag(q, session_id="demo1")
    print("\n=== ANSWER ===\n", result["answer"])
    print("\n=== SUPPORT ===\n", result["support"])
    print("\n=== ROUTE / FILTER ===\n", result["route"], result["project_filter"])
    print("\n=== CITATIONS ===")
    for c in result["citations"]:
        print(c)