"""
Checkpointer for LangGraph - Follows LangGraph Protocols

Supports multiple backends:
- InMemorySaver: Development/testing (in-memory, not persistent)
- SqliteSaver: Local development (file-based, persistent)
- PostgresSaver: Production (database-backed, persistent) - Works with Supabase!

Follows LangGraph's official patterns:
- Uses thread_id in config for conversation threads
- Automatically persists state after each node execution
- Supports state recovery and resumption

Reference: https://docs.langchain.com/oss/python/langgraph/add-memory
"""
import os
from pathlib import Path
from config.settings import DEBUG_MODE

# Get checkpointer type from environment (default: memory for development)
CHECKPOINTER_TYPE = os.getenv("CHECKPOINTER_TYPE", "memory").lower()

# Global variables to store async checkpointer state (for postgres/supabase)
_checkpointer_init_func = None
_checkpointer_ctx = None
_checkpointer_instance = None
_postgres_uri = None

# Initialize checkpointer based on type
if CHECKPOINTER_TYPE == "postgres" or CHECKPOINTER_TYPE == "supabase":
    # Production: Use AsyncPostgresSaver (works with Supabase since it uses PostgreSQL)
    # Using async version because we use graph.astream() for streaming
    try:
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        import asyncio
        
        # Priority order for connection string:
        # 1. SUPABASE_DB_URL (Supabase direct connection)
        # 2. CHECKPOINT_POSTGRES_URI (explicit checkpointer DB)
        # 3. POSTGRES_URI (generic Postgres)
        # 4. Build from Supabase credentials (if available)
        
        POSTGRES_URI = os.getenv("SUPABASE_DB_URL") or \
                      os.getenv("CHECKPOINT_POSTGRES_URI") or \
                      os.getenv("POSTGRES_URI")
        
        # If no explicit URI, try to build from Supabase credentials
        if not POSTGRES_URI:
            SUPABASE_URL = os.getenv("SUPABASE_URL")
            SUPABASE_DB_PASSWORD = os.getenv("SUPABASE_DB_PASSWORD")
            
            if SUPABASE_URL and SUPABASE_DB_PASSWORD:
                # Extract project ref from Supabase URL
                # Format: https://[project-ref].supabase.co
                try:
                    project_ref = SUPABASE_URL.replace("https://", "").replace(".supabase.co", "")
                    # Use direct connection (port 5432) for better performance
                    POSTGRES_URI = f"postgresql://postgres:{SUPABASE_DB_PASSWORD}@db.{project_ref}.supabase.co:5432/postgres"
                    if DEBUG_MODE:
                        print(f"🔗 Built Supabase connection string from credentials")
                except Exception as e:
                    if DEBUG_MODE:
                        print(f"⚠️  Could not build Supabase connection string: {e}")
                    POSTGRES_URI = None
        
        # Fallback to default if still not set
        if not POSTGRES_URI:
            POSTGRES_URI = "postgresql://postgres:postgres@localhost:5432/langgraph_checkpoints"
            if DEBUG_MODE:
                print(f"⚠️  Using default Postgres URI (set SUPABASE_DB_URL for production)")
        
        # Store connection info at module level
        _postgres_uri = POSTGRES_URI
        
        # Create async checkpointer using LangGraph's from_conn_string pattern
        # from_conn_string returns an async context manager
        # We'll store the context manager and enter it lazily via init_checkpointer_async()
        _checkpointer_ctx = AsyncPostgresSaver.from_conn_string(POSTGRES_URI)
        
        # Lazy initialization function - will be called from FastAPI startup
        async def _init_checkpointer():
            """Initialize checkpointer asynchronously - called from FastAPI startup"""
            global _checkpointer_instance
            if _checkpointer_instance is None:
                _checkpointer_instance = await _checkpointer_ctx.__aenter__()
                # Setup tables (idempotent - safe to call multiple times)
                try:
                    await _checkpointer_instance.setup()
                    if DEBUG_MODE:
                        masked_uri = _postgres_uri.split("@")[-1] if "@" in _postgres_uri else _postgres_uri
                        print(f"✅ Postgres/Supabase checkpointer initialized (async): postgresql://***@{masked_uri}")
                except Exception as e:
                    if DEBUG_MODE:
                        print(f"⚠️  Postgres checkpointer setup (tables may already exist or auto-created): {e}")
            return _checkpointer_instance
        
        # Store init function globally for FastAPI startup
        _checkpointer_init_func = _init_checkpointer
        
        # For now, use InMemorySaver as placeholder (will be replaced during startup)
        from langgraph.checkpoint.memory import InMemorySaver
        checkpointer = InMemorySaver()
        
    except ImportError:
        print("❌ ERROR: langgraph-checkpoint-postgres not installed")
        print("   Install with: pip install langgraph-checkpoint-postgres")
        print("   Falling back to InMemorySaver")
        from langgraph.checkpoint.memory import InMemorySaver
        checkpointer = InMemorySaver()
    except Exception as e:
        print(f"❌ ERROR: Failed to initialize Postgres/Supabase checkpointer: {e}")
        print("   Falling back to InMemorySaver")
        from langgraph.checkpoint.memory import InMemorySaver
        checkpointer = InMemorySaver()

elif CHECKPOINTER_TYPE == "sqlite":
    # Local development: Use SqliteSaver (file-based, persistent)
    try:
        from langgraph.checkpoint.sqlite import SqliteSaver
        import sqlite3
        
        # Get database path from environment or use default
        CHECKPOINT_DB_PATH = os.getenv("CHECKPOINT_DB_PATH", "checkpoints.db")
        
        # Ensure absolute path (relative to Backend directory)
        if not os.path.isabs(CHECKPOINT_DB_PATH):
            # Now we're in Backend/graph/, so go up 1 level to Backend/
            BACKEND_DIR = Path(__file__).resolve().parent.parent
            CHECKPOINT_DB_PATH = str(BACKEND_DIR / CHECKPOINT_DB_PATH)
        
        # Create SQLite connection
        _checkpoint_conn = sqlite3.connect(CHECKPOINT_DB_PATH, check_same_thread=False)
        
        # Create persistent checkpointer
        checkpointer = SqliteSaver(_checkpoint_conn)
        
        # Run setup once to create tables (idempotent - safe to call multiple times)
        try:
            checkpointer.setup()
            if DEBUG_MODE:
                print(f"✅ SQLite checkpointer initialized: {CHECKPOINT_DB_PATH}")
        except Exception as e:
            if DEBUG_MODE:
                print(f"⚠️  SQLite checkpointer setup (tables may already exist): {e}")
        
    except ImportError:
        print("❌ ERROR: langgraph-checkpoint-sqlite not installed")
        print("   Install with: pip install langgraph-checkpoint-sqlite")
        print("   Falling back to InMemorySaver")
        from langgraph.checkpoint.memory import InMemorySaver
        checkpointer = InMemorySaver()
    except Exception as e:
        print(f"❌ ERROR: Failed to initialize SQLite checkpointer: {e}")
        print("   Falling back to InMemorySaver")
        from langgraph.checkpoint.memory import InMemorySaver
        checkpointer = InMemorySaver()

else:
    # Default: Use InMemorySaver (in-memory, not persistent)
    # Good for development/testing, but data is lost on restart
    from langgraph.checkpoint.memory import InMemorySaver
    checkpointer = InMemorySaver()
    
    if DEBUG_MODE:
        print("✅ Checkpointer initialized (InMemorySaver - in-memory only)")
        print("⚠️  Note: Conversation history will be lost on restart")
        print("   For persistent storage, set CHECKPOINTER_TYPE=sqlite or CHECKPOINTER_TYPE=postgres")
        print("   SQLite: pip install langgraph-checkpoint-sqlite")
        print("   Postgres: pip install langgraph-checkpoint-postgres")

# Export checkpointer and initialization function
# The checkpointer will be properly initialized during FastAPI startup
__all__ = ["checkpointer", "init_checkpointer_async"]

# Function to initialize async checkpointer (called from FastAPI startup)
async def init_checkpointer_async():
    """Initialize async checkpointer - call this from FastAPI startup event"""
    global checkpointer, _checkpointer_init_func, _checkpointer_instance
    if CHECKPOINTER_TYPE == "postgres" or CHECKPOINTER_TYPE == "supabase":
        if _checkpointer_init_func is not None:
            _checkpointer_instance = await _checkpointer_init_func()
            checkpointer = _checkpointer_instance
        else:
            # Fallback if init function wasn't created
            from langgraph.checkpoint.memory import InMemorySaver
            checkpointer = InMemorySaver()
    # For other types (sqlite, memory), checkpointer is already initialized synchronously
    return checkpointer
