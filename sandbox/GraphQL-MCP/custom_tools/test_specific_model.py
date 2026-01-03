#!/usr/bin/env python3
"""
Test tools with a specific model
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent))

# Try to import graphql client (same pattern as test_tools.py)
try:
    from python_client import GraphQLMCPClient
    from trainexcel.backend.agents.graphql_mcp_tool import get_graphql_tool
except ImportError:
    # Fallback
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "trainexcel" / "backend"))
        from agents.graphql_mcp_tool import get_graphql_tool
    except ImportError:
        # Final fallback: use python_client directly
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

from custom_tools.tool_registry import ToolRegistry

# Load env
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Your specific model
PROJECT_ID = "b45612e372"
MODEL_ID = "6e13519df2"

print("=" * 70)
print(f"Testing Model: {MODEL_ID} in Project: {PROJECT_ID}")
print("=" * 70)

# Setup
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

registry = ToolRegistry(graphql_client=graphql_tool)

# Test 1: Element Geometry
print("\n" + "=" * 70)
print("TEST 1: get_element_geometry")
print("=" * 70)
result = registry.execute_tool(
    "get_element_geometry",
    project_id=PROJECT_ID,
    model_id=MODEL_ID,
    element_type="IfcBeam"
)
if result.get("isError"):
    print(f"❌ Error: {result['content'][0]['text']}")
else:
    print(result['content'][0]['text'])

# Test 2: Element Relationships
print("\n" + "=" * 70)
print("TEST 2: get_element_relationships")
print("=" * 70)
result = registry.execute_tool(
    "get_element_relationships",
    project_id=PROJECT_ID,
    model_id=MODEL_ID,
    element_type="IfcColumn"
)
if result.get("isError"):
    print(f"❌ Error: {result['content'][0]['text']}")
else:
    print(result['content'][0]['text'])

# Test 3: Element Properties
print("\n" + "=" * 70)
print("TEST 3: get_element_properties")
print("=" * 70)
result = registry.execute_tool(
    "get_element_properties",
    project_id=PROJECT_ID,
    model_id=MODEL_ID,
    material_filter="steel"
)
if result.get("isError"):
    print(f"❌ Error: {result['content'][0]['text']}")
else:
    print(result['content'][0]['text'])

print("\n" + "=" * 70)
print("✅ Testing Complete!")
print("=" * 70)


