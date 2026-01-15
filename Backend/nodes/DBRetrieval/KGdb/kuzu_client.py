"""
Kuzu Graph Database Manager
Thread-safe singleton manager for embedded Kuzu database
"""
import kuzu
import os
import logging
from threading import Lock
from pathlib import Path
from config.settings import DEBUG_MODE

logger = logging.getLogger("KUZU_DB")
if DEBUG_MODE:
    logger.setLevel(logging.INFO)
else:
    logger.setLevel(logging.WARNING)

class KuzuManager:
    _instance = None
    _lock = Lock()
    
    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(KuzuManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, db_path: str = None):
        if self._initialized:
            return
            
        with self._lock:
            if self._initialized:
                return
                
            # Set default path if not provided
            if db_path is None:
                # Store in Backend/data/kuzu_db
                backend_dir = Path(__file__).resolve().parent.parent
                db_path = str(backend_dir / "data" / "kuzu_db")
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
            logger.info(f"🚀 Initializing Kuzu database at: {db_path}")
            try:
                self.db = kuzu.Database(db_path)
                self.conn = kuzu.Connection(self.db)
                self._initialized = True
                logger.info("✅ Kuzu database initialized successfully")
                
                # Auto-initialize if empty and in DEBUG_MODE
                self._initialize_if_empty()
            except Exception as e:
                logger.error(f"❌ Failed to initialize Kuzu database: {e}")
                raise

    def _initialize_if_empty(self):
        """
        In DEBUG_MODE, if the database has no tables, initialize it 
        using the hardcoded schema and insertions.
        """
        if not DEBUG_MODE:
            return
            
        try:
            schema = self.get_schema()
            if schema["success"] and not schema["tables"]:
                logger.info("🗄️ Database is empty, initializing with hardcoded schema and data...")
                
                base_path = Path(__file__).resolve().parent / "hardcoded-graphs"
                schema_path = base_path / "BimDB.cypher"
                insert_path = base_path / "insertions.cypher"
                
                if schema_path.exists():
                    logger.info(f"📜 Loading schema from {schema_path}")
                    with open(schema_path, "r", encoding="utf-8") as f:
                        schema_content = f.read()
                    # Execute the whole schema at once as requested
                    self.conn.execute(schema_content)
                
                if insert_path.exists():
                    logger.info(f"📥 Loading data from {insert_path}")
                    with open(insert_path, "r", encoding="utf-8") as f:
                        insert_content = f.read()
                    # Execute all insertions at once as requested
                    self.conn.execute(insert_content)
                    
                logger.info("✅ Database initialization complete")
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")

    def execute(self, query: str, params: dict = None):
        """
        Execute a Cypher query against the graph database.
        Uses a lock for write operations to ensure thread safety.
        """
        is_write = any(keyword in query.upper() for keyword in ["CREATE", "MERGE", "SET", "DELETE", "REMOVE", "DROP"])
        
        try:
            if is_write:
                with self._lock:
                    logger.info(f"📝 Executing WRITE query: {query[:100]}...")
                    result = self.conn.execute(query, params or {})
            else:
                logger.info(f"🔍 Executing READ query: {query[:100]}...")
                result = self.conn.execute(query, params or {})
            
            # Process results into a standard format
            columns = result.get_column_names()
            rows = []
            while result.has_next():
                rows.append(result.get_next())
                
            return {
                "success": True,
                "columns": columns,
                "rows": rows,
                "row_count": len(rows)
            }
        except Exception as e:
            logger.error(f"❌ Cypher execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": query
            }

    def get_schema(self):
        """Returns the current graph schema (node and rel tables)"""
        try:
            # Kuzu doesn't have a direct 'get_schema' method like some others,
            # but we can query metadata or use internal methods if available.
            # For now, we'll return a simple placeholder or common metadata query.
            tables = self.conn.execute("CALL SHOW_TABLES() RETURN *").get_as_df().to_dict(orient='records')
            return {
                "success": True,
                "tables": tables
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

# Helper function to get the global instance
def get_kuzu_manager() -> KuzuManager:
    return KuzuManager()
