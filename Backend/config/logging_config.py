"""
Logging Configuration for RAG System
Centralized logging setup for all modules
"""
import logging
from .settings import DEBUG_MODE

# Set logging level based on DEBUG_MODE
LOG_LEVEL = logging.INFO if DEBUG_MODE else logging.WARNING
# Enhanced format with timestamp for VLM logs - makes it easier to track
# Configure logging - use force=True to reconfigure if already set
try:
    logging.basicConfig(
        level=LOG_LEVEL, 
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
        force=True  # Force reconfiguration even if already configured (Python 3.8+)
    )
except TypeError:
    # Python < 3.8 doesn't support force parameter
    if not logging.root.handlers:
        logging.basicConfig(
            level=LOG_LEVEL, 
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%H:%M:%S"
        )
    else:
        # If already configured, just update the level
        logging.root.setLevel(LOG_LEVEL)
        for handler in logging.root.handlers:
            handler.setLevel(LOG_LEVEL)

# Always ensure root logger level is set correctly
logging.root.setLevel(LOG_LEVEL)
for handler in logging.root.handlers:
    handler.setLevel(LOG_LEVEL)

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
    # Debug message to confirm DEBUG_MODE is enabled
    print(f"✅ DEBUG_MODE is ENABLED - All logs will be visible (LOG_LEVEL={logging.getLevelName(LOG_LEVEL)})")
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
    print(f"⚠️ DEBUG_MODE is DISABLED - Only WARNING and above will be visible (LOG_LEVEL={logging.getLevelName(LOG_LEVEL)})")


def log_chunk_info(message: str):
    """Log chunk-related info that should always be visible"""
    print(f"📦 {message}")  # Using print to bypass log level

