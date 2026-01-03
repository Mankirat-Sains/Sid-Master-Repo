"""
Supabase Vector Store Client
Initializes and manages connections to Supabase vector stores
"""
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_openai import OpenAIEmbeddings
from supabase import create_client, Client
from langgraph.checkpoint.memory import MemorySaver
from config.settings import (
    SUPABASE_URL, SUPABASE_KEY, SUPA_SMART_TABLE,
    SUPA_LARGE_TABLE, SUPA_CODE_TABLE, SUPA_COOP_TABLE,
    DEBUG_MODE
)
from config.llm_instances import emb

# Global vector store instances
vs_smart = None
vs_large = None
vs_code = None
vs_coop = None
vs_drawings = None  # legacy placeholder

# Memory (LangGraph built-in in-memory checkpoint)
memory = MemorySaver()


def initialize_vector_stores():
    """Initialize all Supabase vector stores"""
    global vs_smart, vs_large, vs_code, vs_coop
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("⚠️ SUPABASE_URL/ANON_KEY not set. Supabase vector stores are required.")
        vs_smart = None
        vs_large = None
        vs_code = None
        vs_coop = None
        return
    
    print("\n🔍 Connecting to Supabase pgvector tables...")
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
        
        # Startup logging (only in DEBUG_MODE)
        if DEBUG_MODE:
            print(f"✅ Supabase vector stores ready:")
            print(f"   📊 Smart table: '{SUPA_SMART_TABLE}' → vs_smart")
            print(f"   📊 Large table: '{SUPA_LARGE_TABLE}' → vs_large")
            print(f"   📊 Code table: '{SUPA_CODE_TABLE}' → vs_code")
            print(f"   📊 Coop table: '{SUPA_COOP_TABLE}' → vs_coop")
            
            # Test connections by checking if tables exist
            try:
                smart_count = _supa.table(SUPA_SMART_TABLE).select("*", count="exact").limit(1).execute()
                large_count = _supa.table(SUPA_LARGE_TABLE).select("*", count="exact").limit(1).execute()
                code_count = _supa.table(SUPA_CODE_TABLE).select("*", count="exact").limit(1).execute()
                coop_count = _supa.table(SUPA_COOP_TABLE).select("*", count="exact").limit(1).execute()
                print(f"   📈 Smart table rows: {smart_count.count}")
                print(f"   📈 Large table rows: {large_count.count}")
                print(f"   📈 Code table rows: {code_count.count}")
                print(f"   📈 Coop table rows: {coop_count.count}")
            except Exception as e:
                print(f"   ⚠️  Could not count rows: {e}")
    except Exception as e:
        print(f"❌ Supabase vector store init failed: {e}")
        vs_smart = None
        vs_large = None
        vs_code = None
        vs_coop = None


# Initialize on import
initialize_vector_stores()

