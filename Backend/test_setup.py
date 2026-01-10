"""
Quick test script to verify the refactored setup works
Run this before starting the API server to check for import errors
"""
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 60)
print("Testing Backend_new Setup")
print("=" * 60)

# Test imports
print("\n1. Testing config imports...")
try:
    from config.settings import PROJECT_CATEGORIES, PLANNER_PLAYBOOK
    print("   ✓ Config settings imported")
except Exception as e:
    print(f"   ✗ Config import failed: {e}")
    sys.exit(1)

print("\n2. Testing model imports...")
try:
    from models.rag_state import RAGState
    from models.memory import SESSION_MEMORY
    print("   ✓ Models imported")
except Exception as e:
    print(f"   ✗ Model import failed: {e}")
    sys.exit(1)

print("\n3. Testing database imports...")
try:
    from nodes.DBRetrieval.KGdb import test_database_connection
    from nodes.DBRetrieval.KGdb.supabase_client import vs_smart, vs_large
    print("   ✓ Database imports successful")
    print(f"   ✓ vs_smart initialized: {vs_smart is not None}")
    print(f"   ✓ vs_large initialized: {vs_large is not None}")
except Exception as e:
    print(f"   ⚠ Database import warning: {e}")
    print("   (This is OK if Supabase credentials are not set)")

print("\n4. Testing node imports...")
try:
    from nodes.plan import node_plan
    from nodes.DBRetrieval.SQLdb.rag import node_rag
    from nodes.DBRetrieval.SQLdb.retrieve import node_retrieve
    print("   ✓ Nodes imported")
except Exception as e:
    print(f"   ✗ Node import failed: {e}")
    sys.exit(1)

print("\n5. Testing graph builder...")
try:
    from graph.builder import build_graph
    graph = build_graph()
    print("   ✓ Graph built successfully")
except Exception as e:
    print(f"   ✗ Graph build failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n6. Testing main entry point...")
try:
    from main import run_agentic_rag, rag_healthcheck
    print("   ✓ Main functions imported")
except Exception as e:
    print(f"   ✗ Main import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n7. Testing API server imports...")
try:
    from api_server import app
    print("   ✓ API server imported")
except Exception as e:
    print(f"   ✗ API server import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ All imports successful! Setup looks good.")
print("=" * 60)
print("\nYou can now start the server with:")
print("  python api_server.py")
print("\nOr test the health endpoint:")
print("  python -c \"from main import rag_healthcheck; print(rag_healthcheck())\"")

