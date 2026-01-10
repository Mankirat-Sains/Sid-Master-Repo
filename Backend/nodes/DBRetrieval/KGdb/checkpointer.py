"""
Checkpointer for LangGraph

Currently using MemorySaver (in-memory, not persistent across restarts).
For persistent storage, you need to install langgraph-checkpoint-sqlite:
    pip install langgraph-checkpoint-sqlite

Then uncomment the SqliteSaver code below and comment out MemorySaver.
"""
from langgraph.checkpoint.memory import MemorySaver
from config.settings import DEBUG_MODE

# Use MemorySaver for now (in-memory, not persistent)
# TODO: Install langgraph-checkpoint-sqlite and switch to SqliteSaver for persistence
checkpointer = MemorySaver()

if DEBUG_MODE:
    print("✅ Checkpointer initialized (MemorySaver - in-memory only)")
    print("⚠️  Note: For persistent storage, install: pip install langgraph-checkpoint-sqlite")

# ============================================================================
# PERSISTENT CHECKPOINTER SETUP (requires langgraph-checkpoint-sqlite)
# ============================================================================
# Uncomment below once langgraph-checkpoint-sqlite is installed:
#
# import os
# import sqlite3
# from pathlib import Path
# from langgraph.checkpoint.sqlite import SqliteSaver
#
# # Get database path from environment or use default
# CHECKPOINT_DB_PATH = os.getenv("CHECKPOINT_DB_PATH", "checkpoints.db")
#
# # Ensure absolute path (relative to Backend directory)
# if not os.path.isabs(CHECKPOINT_DB_PATH):
#     # Now we're in Backend/nodes/DBRetrieval/KGdb/, so go up 4 levels to Backend/
#     BACKEND_DIR = Path(__file__).resolve().parent.parent.parent.parent
#     CHECKPOINT_DB_PATH = str(BACKEND_DIR / CHECKPOINT_DB_PATH)
#
# # Create SQLite connection
# _checkpoint_conn = sqlite3.connect(CHECKPOINT_DB_PATH, check_same_thread=False)
#
# # Create persistent checkpointer
# checkpointer = SqliteSaver(_checkpoint_conn)
#
# # Run setup once to create tables (idempotent - safe to call multiple times)
# try:
#     checkpointer.setup()
#     if DEBUG_MODE:
#         print(f"✅ Persistent checkpointer initialized: {CHECKPOINT_DB_PATH}")
# except Exception as e:
#     print(f"⚠️  Checkpointer setup warning (may already exist): {e}")
#
# # For production, you can use PostgresSaver instead:
# # from langgraph.checkpoint.postgres import PostgresSaver
# # POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://user:pass@localhost:5432/dbname")
# # checkpointer = PostgresSaver.from_conn_string(POSTGRES_URL)
# # await checkpointer.asetup()  # For async version
