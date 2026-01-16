#!/usr/bin/env python3
"""
Test Script for Plan Node Routing
Simulates the plan node with different queries to see routing decisions.
"""
import sys
import os
from pathlib import Path

# Add Backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

# Import models first (no dependencies)
from models.orchestration_state import OrchestrationState

# Import node_plan directly from the file to avoid circular imports
# (nodes/__init__.py imports router_dispatcher which causes circular dependency)
import importlib.util
plan_path = backend_path / "nodes" / "plan.py"
spec = importlib.util.spec_from_file_location("plan_module", plan_path)
plan_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plan_module)
node_plan = plan_module.node_plan

# Import logging config (after plan module is loaded)
from config.logging_config import log_query

# Configure logging to see plan node output
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S"
)


def test_plan_routing(query: str, description: str = ""):
    """
    Test the plan node with a specific query and display the routing decision.
    
    Args:
        query: The user query to test
        description: Optional description of what this test is checking
    """
    print("\n" + "="*80)
    if description:
        print(f"TEST: {description}")
    print(f"QUERY: {query}")
    print("-"*80)
    
    # Create orchestration state with the query
    state = OrchestrationState(
        session_id="test_session",
        user_query=query,
        original_question=query,
    )
    
    try:
        # Call the plan node
        result = node_plan(state)
        
        # Extract routing decision
        selected_routers = result.get("selected_routers", [])
        
        # Display results
        print(f"✅ ROUTING DECISION:")
        print(f"   Selected Routers: {selected_routers}")
        print(f"   Router Count: {len(selected_routers)}")
        
        # Show what each router means
        router_descriptions = {
            "database": "→ Database/Document Search (Supabase, BIM, drawings, specs)",
            "web": "→ Web Tools/Calculations (SkyCiv, Jabacus, calculators)",
            "desktop": "→ Desktop Apps/Files (Excel, Word, local file access)"
        }
        
        if selected_routers:
            print(f"\n   Router Details:")
            for router in selected_routers:
                desc = router_descriptions.get(router, "→ Unknown router")
                print(f"   • {router.upper()}: {desc}")
        else:
            print("   ⚠️  No routers selected!")
        
        return selected_routers
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Run a series of test queries to see routing decisions."""
    
    print("\n" + "="*80)
    print("PLAN NODE ROUTING TEST SUITE")
    print("="*80)
    print("\nThis script tests the plan node's routing decisions for various queries.")
    print("The plan node determines which routers (database, web, desktop) should handle each query.\n")
    
    # Test queries organized by expected router
    test_cases = [
        # RAG queries (database/document search)
        ("Find projects with floating slabs", "RAG - Project search"),
        ("Search for retaining wall designs", "RAG - Design search"),
        ("Show me barndominium projects", "RAG - Project type search"),
        ("What are the specifications for beam design?", "RAG - Specification search"),
        ("Find drawings related to foundation design", "RAG - Drawing search"),
        
        # Web queries (calculations/tools)
        ("Calculate beam deflection", "WEB - Calculation"),
        ("Use SkyCiv to analyze this structure", "WEB - SkyCiv API"),
        ("Run a calculation using Jabacus", "WEB - Jabacus API"),
        ("What is the moment capacity of a W12x50 beam?", "WEB - Engineering calculation"),
        ("Calculate the load on this column", "WEB - Structural calculation"),
        
        # Desktop queries (file operations)
        ("What files are in my Desktop?", "DESKTOP - File listing"),
        ("Open the Excel file on my desktop", "DESKTOP - Excel file access"),
        ("Read data from a spreadsheet", "DESKTOP - Excel data read"),
        ("List files in my Documents folder", "DESKTOP - File system access"),
        ("Show me files on my computer", "DESKTOP - File system query"),
        ("What's in the Excel file at /Users/james/Desktop/file.xlsx?", "DESKTOP - Specific file path"),
        ("Create a Word document", "DESKTOP - Word operation"),
        ("Edit the document in Word", "DESKTOP - Word editing"),
        
        # Edge cases / ambiguous queries
        ("How do I design a steel beam?", "EDGE - Could be web (calc) or rag (info)"),
        ("Tell me about beam design", "EDGE - Information query (likely RAG)"),
        ("Design a beam for a 20ft span", "EDGE - Could be web (calc) or rag (info)"),
        ("What is a beam?", "EDGE - General knowledge (likely RAG)"),
        
        # Multi-router queries (should select multiple)
        ("Find projects with beams and calculate the load", "MULTI - DATABASE + WEB"),
        ("Search for Excel files on my desktop", "MULTI - DATABASE + DESKTOP"),
        ("Calculate beam capacity and save to Excel", "MULTI - WEB + DESKTOP"),
    ]
    
    # Run all tests
    results = {}
    for query, description in test_cases:
        routers = test_plan_routing(query, description)
        if routers:
            router_key = ",".join(sorted(routers))
            if router_key not in results:
                results[router_key] = []
            results[router_key].append((query, description))
    
    # Summary
    print("\n" + "="*80)
    print("ROUTING SUMMARY")
    print("="*80)
    
    for router_key, queries in sorted(results.items()):
        print(f"\n{router_key.upper()}: {len(queries)} queries")
        for query, desc in queries:
            print(f"  • {query}")
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
