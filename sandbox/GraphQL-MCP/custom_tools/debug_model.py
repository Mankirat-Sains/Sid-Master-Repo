#!/usr/bin/env python3
"""
Debug script to see what's actually in the model
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

print("=" * 70)
print(f"Debugging Model: {MODEL_ID} in Project: {PROJECT_ID}")
print("=" * 70)

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

# Step 1: Get model versions
print("\n1. Getting model versions...")
query1 = """
query GetModelVersion($projectId: String!, $modelId: String!) {
  project(id: $projectId) {
    model(id: $modelId) {
      id
      name
      versions(limit: 5) {
        items {
          id
          referencedObject
          message
        }
      }
    }
  }
}
"""
result1 = graphql_tool.query(query1, variables={"projectId": PROJECT_ID, "modelId": MODEL_ID})
print(f"Result: {json.dumps(result1, indent=2)[:1000]}...")

if result1.get("data", {}).get("project", {}).get("model"):
    model = result1["data"]["project"]["model"]
    versions = model.get("versions", {}).get("items", [])
    
    if versions:
        root_object_id = versions[0].get("referencedObject")
        print(f"\n✅ Found root object ID: {root_object_id}")
        
        # Step 2: Get root object
        print(f"\n2. Getting root object and children...")
        query2 = """
        query GetObjects($projectId: String!, $objectId: String!) {
          project(id: $projectId) {
            object(id: $objectId) {
              id
              speckleType
              data
              children(limit: 100, depth: 3) {
                totalCount
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
        
        object_data = result2.get("data", {}).get("project", {}).get("object", {})
        if object_data:
            total_count = object_data.get("children", {}).get("totalCount", 0)
            children = object_data.get("children", {}).get("objects", [])
            root_data = object_data.get("data")
            
            print(f"\n✅ Root object found:")
            print(f"   ID: {object_data.get('id')}")
            print(f"   Type: {object_data.get('speckleType')}")
            print(f"   Has data: {bool(root_data)}")
            print(f"   Total children: {total_count}")
            print(f"   Children returned: {len(children)}")
            
            # Check a few children
            print(f"\n3. Checking first few children...")
            for i, child in enumerate(children[:5]):
                child_data = child.get("data")
                print(f"\n   Child {i+1}:")
                print(f"     ID: {child.get('id')}")
                print(f"     Type: {child.get('speckleType')}")
                print(f"     Has data: {bool(child_data)}")
                
                if child_data:
                    try:
                        if isinstance(child_data, str):
                            parsed = json.loads(child_data)
                        else:
                            parsed = child_data
                        
                        if isinstance(parsed, dict):
                            print(f"     IFC Type: {parsed.get('ifcType', 'N/A')}")
                            print(f"     Name: {parsed.get('name', 'N/A')}")
                            print(f"     Has referencedObjects: {bool(parsed.get('referencedObjects'))}")
                    except Exception as e:
                        print(f"     Error parsing: {e}")
        else:
            print(f"\n❌ No object data returned")
            print(f"Full response: {json.dumps(result2, indent=2)[:2000]}")
    else:
        print(f"\n❌ No versions found in model")
else:
    print(f"\n❌ Model not found")
    print(f"Full response: {json.dumps(result1, indent=2)[:1000]}")


