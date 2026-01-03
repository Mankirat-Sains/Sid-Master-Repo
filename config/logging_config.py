"""
Logging Configuration for RAG System
Centralized logging setup for all modules
"""
import logging
from .settings import DEBUG_MODE

# Set logging level to WARNING (suppress INFO/DEBUG from all loggers)
LOG_LEVEL = logging.WARNING
logging.basicConfig(level=LOG_LEVEL, format="%(message)s")  # Simple format - just the message

# Create loggers for different components
log_query = logging.getLogger("QUERY_FLOW")
log_route = logging.getLogger("ROUTING")
log_db = logging.getLogger("DATABASE")
log_enh = logging.getLogger("ENHANCEMENT")
log_syn = logging.getLogger("SYNTHESIS")
log_vlm = logging.getLogger("VLM")

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


def log_chunk_info(message: str):
    """Log chunk-related info that should always be visible"""
    print(f"📦 {message}")  # Using print to bypass log level

