"""
Configuration Settings for RAG System
Centralized configuration for all modules
"""
import os
import re
from pathlib import Path

# =============================================================================
# Environment Variables
# =============================================================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY", "")
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"

# =============================================================================
# Model Configuration
# =============================================================================
FAST_MODEL = os.getenv("FAST_MODEL", "gpt-4o-mini")
ROUTER_MODEL = os.getenv("ROUTER_MODEL", "gpt-4o-mini")
GRADER_MODEL = os.getenv("GRADER_MODEL", "gpt-4o-mini")
SUPPORT_MODEL = os.getenv("SUPPORT_MODEL", "gpt-4o-mini")
SYNTHESIS_MODEL = os.getenv("SYNTHESIS_MODEL", "gpt-4o")
CORRECTIVE_MODEL = os.getenv("CORRECTIVE_MODEL", "gpt-4o-mini")
EMB_MODEL = os.getenv("EMB_MODEL", "text-embedding-3-small")

# =============================================================================
# Retrieval Limits
# =============================================================================
MAX_RETRIEVAL_DOCS = int(os.getenv("MAX_RETRIEVAL_DOCS", "50"))
MAX_SMART_RETRIEVAL_DOCS = int(os.getenv("MAX_SMART_RETRIEVAL_DOCS", "30"))
MAX_LARGE_RETRIEVAL_DOCS = int(os.getenv("MAX_LARGE_RETRIEVAL_DOCS", "50"))
MAX_HYBRID_RETRIEVAL_DOCS = int(os.getenv("MAX_HYBRID_RETRIEVAL_DOCS", "40"))
MAX_CODE_RETRIEVAL_DOCS = int(os.getenv("MAX_CODE_RETRIEVAL_DOCS", "20"))
MAX_GRADED_DOCS = int(os.getenv("MAX_GRADED_DOCS", "15"))
MAX_SYNTHESIS_DOCS = int(os.getenv("MAX_SYNTHESIS_DOCS", "10"))
MAX_CITATIONS_DISPLAY = int(os.getenv("MAX_CITATIONS_DISPLAY", "5"))
MAX_ROUTER_DOCS = int(os.getenv("MAX_ROUTER_DOCS", "10"))

# =============================================================================
# Supabase Table Names
# =============================================================================
SUPA_SMART_TABLE = os.getenv("SUPA_SMART_TABLE", "embeddings_smart")
SUPA_LARGE_TABLE = os.getenv("SUPA_LARGE_TABLE", "embeddings_large")
SUPA_CODE_TABLE = os.getenv("SUPA_CODE_TABLE", "embeddings_code")
SUPA_COOP_TABLE = os.getenv("SUPA_COOP_TABLE", "embeddings_coop")

# =============================================================================
# Project ID Regex Pattern
# =============================================================================
PROJECT_RE = re.compile(r'\d{2}-\d{2}-\d{3,4}')

# =============================================================================
# Reference Files
# =============================================================================
BASE_DIR = Path(__file__).parent.parent
REFERENCES_DIR = BASE_DIR / "references"
CATEGORIES_PATH = REFERENCES_DIR / "project_categories.md"
PLAYBOOK_PATH = REFERENCES_DIR / "planner_playbook.md"

# =============================================================================
# Load Reference Content
# =============================================================================
def _load_file_content(file_path: Path) -> str:
    """Load content from a reference file"""
    if file_path.exists():
        try:
            return file_path.read_text(encoding='utf-8')
        except Exception as e:
            print(f"Warning: Could not load {file_path}: {e}")
            return ""
    return ""

# Load project categories
PROJECT_CATEGORIES = _load_file_content(CATEGORIES_PATH)

# Load planner playbook
PLANNER_PLAYBOOK = _load_file_content(PLAYBOOK_PATH)

