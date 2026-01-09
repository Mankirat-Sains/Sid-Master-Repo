"""
RAG System Configuration Settings
All constants, environment variables, and model configuration
"""
import os
import re
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# =============================================================================
# PATHS
# =============================================================================
BACKEND_DIR = Path(__file__).resolve().parent.parent  # Backend/Backend/
PROJECT_ROOT = BACKEND_DIR.parent.parent  # Go up to RAG/ root
REFERENCES_DIR = BACKEND_DIR / "references"

# =============================================================================
# EXTERNAL FILES - Playbook & Categories
# =============================================================================
# Load Playbook
try:
    playbook_paths = [
        REFERENCES_DIR / "planner_playbook.md",  # Backend/Backend/references/planner_playbook.md
        BACKEND_DIR / "planner_playbook.md",  # Fallback: Backend/Backend/planner_playbook.md
        PROJECT_ROOT / "Backend" / "planner_playbook.md"  # Legacy: RAG/Backend/planner_playbook.md
    ]
    PLAYBOOK_PATH = next((p for p in playbook_paths if p.exists()), playbook_paths[0])
    PLANNER_PLAYBOOK = PLAYBOOK_PATH.read_text(encoding="utf-8")
except Exception as e:
    PLANNER_PLAYBOOK = "No playbook provided."
    PLAYBOOK_PATH = None
    print(f"❌ Failed to load playbook: {e}")

# Load Project Categories
try:
    category_paths = [
        REFERENCES_DIR / "project_categories.md",  # Backend/Backend/references/project_categories.md
        BACKEND_DIR / "project_categories.md",  # Fallback: Backend/Backend/project_categories.md
        PROJECT_ROOT / "Backend" / "project_categories.md"  # Legacy: RAG/Backend/project_categories.md
    ]
    CATEGORIES_PATH = next((p for p in category_paths if p.exists()), category_paths[0])
    PROJECT_CATEGORIES = CATEGORIES_PATH.read_text(encoding="utf-8")
except Exception as e:
    PROJECT_CATEGORIES = "No project categories provided."
    CATEGORIES_PATH = None
    print(f"❌ Failed to load project categories: {e}")

# =============================================================================
# API KEYS
# =============================================================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# =============================================================================
# MODEL CONFIGURATION - Optimized for Cost & Performance
# =============================================================================

# Fast models (cheaper, faster for simple tasks)
# Use Groq models for speed optimization (llama-3.1-8b-instant for classification, llama-3.3-70b-versatile for planning)
FAST_MODEL = os.getenv("FAST_MODEL", "llama-3.1-8b-instant")
ROUTER_MODEL = os.getenv("ROUTER_MODEL", "llama-3.1-8b-instant")
GRADER_MODEL = os.getenv("GRADER_MODEL", "llama-3.1-8b-instant")
SUPPORT_MODEL = os.getenv("SUPPORT_MODEL", "llama-3.1-8b-instant")
RAG_PLANNER_MODEL = os.getenv("RAG_PLANNER_MODEL", "llama-3.1-70b")  # For query rewriting + planning (updated from decommissioned llama-3.1-70b-versatile)
VERIFY_MODEL = os.getenv("VERIFY_MODEL", "llama-3.1-8b-instant")  # For verification tasks (updated from decommissioned mixtral-8x7b-32768)

# High-quality models (for synthesis, final answers - keep using OpenAI/Anthropic)
SYNTHESIS_MODEL = os.getenv("SYNTHESIS_MODEL", "gpt-4o")
CORRECTIVE_MODEL = os.getenv("CORRECTIVE_MODEL", "gpt-4o")

# Embedding Model
EMB_MODEL = os.getenv("EMB_MODEL", "text-embedding-3-small")

# =============================================================================
# SUPABASE CONFIGURATION
# =============================================================================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPA_SMART_TABLE = "image_descriptions"
SUPA_LARGE_TABLE = "project_description"
SUPA_CODE_TABLE = "code_chunks"
SUPA_COOP_TABLE = "coop_chunks"

# =============================================================================
# RETRIEVAL CONFIGURATION
# =============================================================================
ENABLE_HYBRID_RETRIEVAL = False

# Project ID Pattern (matches: 25-08-001 or 2508001)
PROJECT_RE = re.compile(r'(?<!\d)(?:\d{2}\D*\d{2}\D*\d{3}|\d{7})(?!\d)')

# =============================================================================
# CHUNK LIMIT CONSTANTS - CENTRALIZED CONTROL
# =============================================================================
MAX_RETRIEVAL_DOCS = 200        # How many docs to retrieve per subquery (legacy default)
MAX_GRADED_DOCS = 200          # How many docs after grading
MAX_SYNTHESIS_DOCS = 50        # How many docs to synthesize with
MAX_SUPPORT_DOCS = 6           # For support scoring
MAX_ROUTER_DOCS = 4            # For routing decisions
MAX_CORRECTIVE_DOCS = 15       # For corrective retrieval
MAX_CITATIONS_DISPLAY = 20     # How many citations to show in final answer

# Smart vs Large database chunk limits
MAX_SMART_RETRIEVAL_DOCS = 200  # More chunks for smart (concise constraints)
MAX_LARGE_RETRIEVAL_DOCS = 50   # Fewer chunks for large (multi-constraint queries)
MAX_CODE_RETRIEVAL_DOCS = 30   # Reasonable limit for code database
MAX_COOP_RETRIEVAL_DOCS = 100   # Reasonable limit for coop database

# Hybrid retrieval weights
MAX_HYBRID_RETRIEVAL_DOCS = 100  # Total docs for hybrid retrieval

# =============================================================================
# MEMORY CONFIGURATION
# =============================================================================
MAX_CONVERSATION_HISTORY = 5  # Keep last 5 Q&A exchanges
MAX_SEMANTIC_HISTORY = 5      # Keep semantic intelligence for last 5 exchanges

# =============================================================================
# ROLE-BASED DATABASE PREFERENCES
# =============================================================================
# Defines which databases should be preferred/prioritized for different user roles
# Used by the router to guide database selection in query routing
#
# DATABASES:
# 1. project_db: Project database with two sub-tables:
#    - image_descriptions (smart chunks): VLM-described small images, more accurate for specific info
#    - project_description (large chunks): Overall project summaries from all image summaries
# 2. code_db: Building codes, standards, guidelines, and recommendations
# 3. coop_manual (internal_docs): Company-specific data, resources, procedures, and training materials
# 4. speckle_db (models_db): BIM information - materials, structural elements, dimensions, member connections
#
# Format: {
#     "role_name": {
#         "project_db": priority (0-1),    # 1.0 = highest priority, 0.0 = lowest
#         "code_db": priority (0-1),
#         "coop_manual": priority (0-1),
#         "speckle_db": priority (0-1),
#         "description": "Role description for router context"
#     }
# }
#
# Priorities guide the router but don't force exclusive selection - the router
# can still select multiple databases when the query requires it.
ROLE_DATABASE_PREFERENCES = {
    "structural_engineer": {
        "project_db": 1.0,      # Primary focus: project documents and drawings
        "code_db": 0.9,         # High: code references for design compliance
        "coop_manual": 0.4,     # Low: training materials less relevant
        "speckle_db": 0.9,      # High: BIM models for structural analysis
        "description": "Structural engineers primarily work with project documents, building codes, and BIM models for design and analysis."
    },
    "design_engineer": {
        "project_db": 0.9,      # High: project documents essential
        "code_db": 0.9,         # High: design standards and codes critical
        "coop_manual": 0.5,     # Medium: some procedures relevant
        "speckle_db": 1.0,      # Primary: BIM models for design work
        "description": "Design engineers need project context, code standards, and BIM models for design work."
    },
    "project_manager": {
        "project_db": 1.0,      # Primary: project documents and history
        "code_db": 0.5,         # Medium: some code awareness needed
        "coop_manual": 0.8,     # High: procedures and workflows very relevant
        "speckle_db": 0.6,      # Medium: BIM models for project overview
        "description": "Project managers focus on project documents, timelines, organizational procedures, and project overview."
    },
    "code_specialist": {
        "project_db": 0.6,      # Medium: project context helpful
        "code_db": 1.0,         # Primary: codes and standards are main focus
        "coop_manual": 0.5,     # Medium: some company procedures
        "speckle_db": 0.4,      # Low: BIM models less relevant
        "description": "Code specialists primarily work with building codes, standards, and regulatory requirements."
    },
    "trainer": {
        "project_db": 0.6,      # Medium: example projects for training
        "code_db": 0.6,         # Medium: code references for training
        "coop_manual": 1.0,     # Primary: training materials and procedures
        "speckle_db": 0.5,      # Medium: example models for training
        "description": "Trainers focus on training materials, procedures, and educational content."
    },
    "bim_specialist": {
        "project_db": 0.7,      # Medium: project context helpful
        "code_db": 0.6,         # Medium: some code awareness
        "coop_manual": 0.5,     # Medium: company procedures
        "speckle_db": 1.0,      # Primary: BIM models and structural information
        "description": "BIM specialists focus on model data, structural elements, materials, and dimensions."
    },
    "default": {
        "project_db": 0.8,      # Balanced: all databases equally accessible
        "code_db": 0.8,
        "coop_manual": 0.8,
        "speckle_db": 0.8,
        "description": "Default role with balanced access to all databases."
    }
}

# Valid role names (for validation)
VALID_ROLES = list(ROLE_DATABASE_PREFERENCES.keys())

# =============================================================================
# DEBUG MODE
# =============================================================================
DEBUG_MODE = True  # ON - Show all INFO level logs

