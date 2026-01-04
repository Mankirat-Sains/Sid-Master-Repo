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
# MODEL CONFIGURATION - Optimized for Cost & Performance
# =============================================================================

# Fast models (cheaper, faster for simple tasks)
FAST_MODEL = os.getenv("FAST_MODEL", "gpt-4o-mini")
ROUTER_MODEL = os.getenv("ROUTER_MODEL", "gpt-4o-mini")
GRADER_MODEL = os.getenv("GRADER_MODEL", "gpt-4o-mini")
SUPPORT_MODEL = os.getenv("SUPPORT_MODEL", "gpt-4o-mini")

# High-quality models (for synthesis, final answers)
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
MAX_CODE_RETRIEVAL_DOCS = 100   # Reasonable limit for code database
MAX_COOP_RETRIEVAL_DOCS = 100   # Reasonable limit for coop database

# Hybrid retrieval weights
MAX_HYBRID_RETRIEVAL_DOCS = 100  # Total docs for hybrid retrieval

# =============================================================================
# MEMORY CONFIGURATION
# =============================================================================
MAX_CONVERSATION_HISTORY = 5  # Keep last 5 Q&A exchanges
MAX_SEMANTIC_HISTORY = 5      # Keep semantic intelligence for last 5 exchanges

# =============================================================================
# DEBUG MODE
# =============================================================================
DEBUG_MODE = True  # ON - Show all INFO level logs

