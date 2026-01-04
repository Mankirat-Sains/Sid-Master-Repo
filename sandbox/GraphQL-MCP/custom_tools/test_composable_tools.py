#!/usr/bin/env python3
"""
Test the minimal composable tools: find_element_types and find_material_types
Demonstrates how they can be combined for complex queries.
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add paths for imports
current_dir = Path(__file__).parent
if (current_dir.parent / "python_client.py").exists():
    sys.path.insert(0, str(current_dir.parent))

sys.path.insert(0, str(Path(__file__).parent.parent / "trainexcel" / "backend"))

# Try to import graphql_mcp_tool, with fallback
try:
    from agents.graphql_mcp_tool import get_graphql_tool
except ImportError:
    try:
        from python_client import GraphQLMCPClient
        
        class GraphQLMCPToolWrapper:
            def __init__(self, endpoint, headers=None, use_mcp=True):
                self.mcp_client = GraphQLMCPClient(
                    endpoint=endpoint,
                    headers=headers or {},
                    allow_mutations=False
                )
                self._started = False
            
            def introspect_schema(self):
                if not self._started:
                    self.mcp_client.start()
                    self._started = True
                return self.mcp_client.introspect_schema()
            
            def query(self, query, variables=None):
                if not self._started:
                    self.mcp_client.start()
                    self._started = True
                return self.mcp_client.query(query, variables)
            
            def get_tool_definitions(self):
                if not self._started:
                    self.mcp_client.start()
                    self._started = True
                return self.mcp_client.get_tool_definitions()
        
        def get_graphql_tool(endpoint, headers=None, use_mcp=True):
            return GraphQLMCPToolWrapper(endpoint=endpoint, headers=headers, use_mcp=use_mcp)
    except ImportError:
        raise ImportError("Could not import graphql_mcp_tool or python_client")

from custom_tools.tool_registry import ToolRegistry

# Load environment
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)


def test_composable_tools():
    """Test the composable tools."""
    
    # Initialize GraphQL client
    graphql_endpoint = os.getenv(
        "GRAPHQL_ENDPOINT",
        "http://k8s-speckle-a8a45c467f-1674783884.ca-central-1.elb.amazonaws.com/graphql"
    )
    auth_token = os.getenv("GRAPHQL_AUTH_TOKEN")
    
    headers = {}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    graphql_tool = get_graphql_tool(
        endpoint=graphql_endpoint,
        headers=headers if headers else None,
        use_mcp=True
    )
    
    # Initialize tool registry
    registry = ToolRegistry(graphql_client=graphql_tool)
    
    # Test project
    PROJECT_ID = "b45612e372"
    MODEL_ID = "6e13519df2"
    
    print("=" * 80)
    print("Testing Minimal Composable Tools")
    print("=" * 80)
    print()
    
    # Test 1: Find all columns
    print("Test 1: Find all columns")
    print("-" * 80)
    result1 = registry.execute_tool(
        "find_element_types",
        project_id=PROJECT_ID,
        model_id=MODEL_ID,
        element_type="Column",
        limit=50
    )
    if not result1.get("isError"):
        print(result1["content"][0]["text"])
        column_ids = [e["element_id"] for e in result1["data"]["elements"]]
        print(f"\nFound {len(column_ids)} columns")
    else:
        print(f"Error: {result1['content'][0]['text']}")
        return
    
    print()
    print()
    
    # Test 2: Find timber elements (all types)
    print("Test 2: Find all timber elements")
    print("-" * 80)
    result2 = registry.execute_tool(
        "find_material_types",
        project_id=PROJECT_ID,
        model_id=MODEL_ID,
        material="Timber",
        limit=50
    )
    if not result2.get("isError"):
        print(result2["content"][0]["text"])
        timber_ids = [e["element_id"] for e in result2["data"]["elements"]]
        print(f"\nFound {len(timber_ids)} timber elements")
    else:
        print(f"Error: {result2['content'][0]['text']}")
        return
    
    print()
    print()
    
    # Test 3: Combine both - Find timber columns (composition)
    print("Test 3: Find timber columns (combining both tools)")
    print("-" * 80)
    result3 = registry.execute_tool(
        "find_material_types",
        project_id=PROJECT_ID,
        model_id=MODEL_ID,
        material="Timber",
        element_type="Column",  # Combined filter
        limit=50
    )
    if not result3.get("isError"):
        print(result3["content"][0]["text"])
        timber_column_ids = [e["element_id"] for e in result3["data"]["elements"]]
        print(f"\nFound {len(timber_column_ids)} timber columns")
    else:
        print(f"Error: {result3['content'][0]['text']}")
    
    print()
    print()
    
    # Test 4: Alternative composition - use element_ids from first tool
    print("Test 4: Alternative composition - filter columns by timber material")
    print("-" * 80)
    if column_ids:
        result4 = registry.execute_tool(
            "find_material_types",
            project_id=PROJECT_ID,
            model_id=MODEL_ID,
            material="Timber",
            element_ids=column_ids[:20],  # Use IDs from find_element_types
            limit=50
        )
        if not result4.get("isError"):
            print(result4["content"][0]["text"])
            print(f"\nFound {len(result4['data']['elements'])} timber columns (from pre-filtered list)")
        else:
            print(f"Error: {result4['content'][0]['text']}")
    
    print()
    print("=" * 80)
    print("Summary:")
    print(f"  - Columns found: {len(column_ids) if 'column_ids' in locals() else 0}")
    print(f"  - Timber elements found: {len(timber_ids) if 'timber_ids' in locals() else 0}")
    print(f"  - Timber columns (combined): {len(timber_column_ids) if 'timber_column_ids' in locals() else 0}")
    print("=" * 80)


if __name__ == "__main__":
    test_composable_tools()


