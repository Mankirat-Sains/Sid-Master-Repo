"""
Logging Configuration for RAG System
Centralized logging setup for all modules
"""
import logging
from .settings import DEBUG_MODE

# Set logging level based on DEBUG_MODE
LOG_LEVEL = logging.INFO if DEBUG_MODE else logging.WARNING
logging.basicConfig(level=LOG_LEVEL, format="%(message)s")  # Simple format - just the message

# Create loggers for different components
log_query = logging.getLogger("QUERY_FLOW")
log_route = logging.getLogger("ROUTING")
log_db = logging.getLogger("DATABASE")
log_enh = logging.getLogger("ENHANCEMENT")
log_syn = logging.getLogger("SYNTHESIS")
log_vlm = logging.getLogger("VLM")

# Set log levels based on DEBUG_MODE
if DEBUG_MODE:
    # Show INFO level for all loggers when DEBUG_MODE is True
    log_vlm.setLevel(logging.INFO)
    log_query.setLevel(logging.INFO)
    log_route.setLevel(logging.INFO)
    log_db.setLevel(logging.INFO)
    log_enh.setLevel(logging.INFO)
    log_syn.setLevel(logging.INFO)
    log_chunks = logging.getLogger("CHUNKS")
    log_chunks.setLevel(logging.INFO)
else:
    # VLM logger - ONLY logger that shows INFO level (for image processing)
    log_vlm.setLevel(logging.INFO)
    # Suppress ALL other loggers - only show WARNING and above
    log_query.setLevel(logging.WARNING)
    log_route.setLevel(logging.WARNING)
    log_db.setLevel(logging.WARNING)
    log_enh.setLevel(logging.WARNING)
    log_syn.setLevel(logging.WARNING)
    log_chunks = logging.getLogger("CHUNKS")
    log_chunks.setLevel(logging.WARNING)  # Suppress chunk logs too


def log_chunk_info(message: str):
    """Log chunk-related info that should always be visible"""
    print(f"📦 {message}")  # Using print to bypass log level

