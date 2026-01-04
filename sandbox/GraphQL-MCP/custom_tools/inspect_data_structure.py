#!/usr/bin/env python3
"""
Inspect the actual data structure to see what we can extract
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from python_client import GraphQLMCPClient
    from trainexcel.backend.agents.graphql_mcp_tool import get_graphql_tool
except ImportError:
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "trainexcel" / "backend"))
        from agents.graphql_mcp_tool import get_graphql_tool
    except ImportError:
        from python_client import GraphQLMCPClient
        
        class GraphQLMCPToolWrapper:
            def __init__(self, endpoint, headers=None, use_mcp=True):
                self.mcp_client = GraphQLMCPClient(endpoint=endpoint, headers=headers or {}, allow_mutations=False)
                self._started = False
            
            def query(self, query, variables=None):
                if not self._started:
                    self.mcp_client.start()
                    self._started = True
                return self.mcp_client.query(query, variables)
        
        def get_graphql_tool(endpoint, headers=None, use_mcp=True):
            return GraphQLMCPToolWrapper(endpoint=endpoint, headers=headers, use_mcp=use_mcp)

env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

PROJECT_ID = "b45612e372"
MODEL_ID = "6e13519df2"

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

# Get model version
query1 = """
query GetModelVersion($projectId: String!, $modelId: String!) {
  project(id: $projectId) {
    model(id: $modelId) {
      versions(limit: 1) {
        items {
          referencedObject
        }
      }
    }
  }
}
"""
result1 = graphql_tool.query(query1, variables={"projectId": PROJECT_ID, "modelId": MODEL_ID})
root_object_id = result1["data"]["project"]["model"]["versions"]["items"][0]["referencedObject"]

# Get objects with full data
query2 = """
query GetObjects($projectId: String!, $objectId: String!) {
  project(id: $projectId) {
    object(id: $objectId) {
      id
      speckleType
      children(limit: 50, depth: 3) {
        objects {
          id
          speckleType
          data
        }
      }
    }
  }
}
"""
result2 = graphql_tool.query(query2, variables={"projectId": PROJECT_ID, "objectId": root_object_id})

children = result2.get("data", {}).get("project", {}).get("object", {}).get("children", {}).get("objects", [])

print("=" * 70)
print("Inspecting Data Structure")
print("=" * 70)

# Look for structural elements
structural_keywords = ["beam", "column", "wall", "slab", "member", "frame", "bracing"]

for i, child in enumerate(children[:20]):
    data_str = child.get("data")
    if not data_str:
        continue
    
    try:
        if isinstance(data_str, str):
            data = json.loads(data_str)
        else:
            data = data_str
        
        if not isinstance(data, dict):
            continue
        
        # Check if it's a structural element
        name = str(data.get("name", "")).lower()
        category = str(data.get("category", "")).lower()
        type_name = str(data.get("type", "")).lower()
        speckle_type = str(child.get("speckleType", "")).lower()
        
        is_structural = any(kw in name or kw in category or kw in type_name or kw in speckle_type 
                          for kw in structural_keywords)
        
        if is_structural:
            print(f"\n{'='*70}")
            print(f"Structural Element {i+1}: {child.get('id')}")
            print(f"{'='*70}")
            print(f"Speckle Type: {child.get('speckleType')}")
            print(f"\nData Keys: {list(data.keys())[:20]}")
            
            # Check for geometry
            if "basePoint" in data:
                print(f"  basePoint: {data['basePoint']}")
            if "startPoint" in data:
                print(f"  startPoint: {data['startPoint']}")
            if "endPoint" in data:
                print(f"  endPoint: {data['endPoint']}")
            if "vertices" in data:
                print(f"  vertices: {len(data.get('vertices', []))} points")
            if "displayValue" in data:
                print(f"  displayValue: {type(data.get('displayValue'))}")
            if "geometry" in data:
                print(f"  geometry: {type(data.get('geometry'))}")
            if "properties" in data:
                props = data.get("properties", {})
                print(f"  properties keys: {list(props.keys())[:10]}")
            
            # Check for IFC data nested
            if "ifcType" in data:
                print(f"  ✅ IFC Type: {data['ifcType']}")
            if "applicationId" in data:
                print(f"  applicationId: {data['applicationId']}")
            
            # Show full structure (truncated)
            print(f"\n  Full data structure (first 500 chars):")
            print(f"  {json.dumps(data, indent=2)[:500]}...")


