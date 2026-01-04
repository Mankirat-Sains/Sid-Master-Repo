#!/usr/bin/env python3
"""
Test Custom Tools
Test your custom tools before adding them to the MCP server
"""

import os
import sys
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Try to import graphql client
try:
    from python_client import GraphQLMCPClient
    from trainexcel.backend.agents.graphql_mcp_tool import get_graphql_tool
except ImportError:
    # Fallback
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "trainexcel" / "backend"))
        from agents.graphql_mcp_tool import get_graphql_tool
    except ImportError:
        print("❌ Could not import GraphQL client. Make sure python_client.py is available.")
        sys.exit(1)

from custom_tools.tool_registry import ToolRegistry
from custom_tools.building_perimeter_tool import BuildingPerimeterTool
from custom_tools.find_beams_tool import FindBeamsTool

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)


def test_tool_registry():
    """Test the tool registry."""
    print("=" * 70)
    print("Testing Custom Tools")
    print("=" * 70)
    
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
    
    # Create tool registry
    registry = ToolRegistry(graphql_client=graphql_tool)
    
    # List available tools
    print("\n📋 Available Tools:")
    for tool_name in registry.list_tools():
        print(f"  - {tool_name}")
    
    # Get tool definitions
    print("\n🔧 Tool Definitions (for LLM):")
    definitions = registry.get_all_tool_definitions()
    for defn in definitions:
        print(f"\n  {defn['function']['name']}:")
        print(f"    Description: {defn['function']['description'][:100]}...")
        print(f"    Parameters: {list(defn['function']['parameters']['properties'].keys())}")
    
    # Test building perimeter tool
    print("\n" + "=" * 70)
    print("Testing: Building Perimeter Tool")
    print("=" * 70)
    
    # Get a project ID (use first available project)
    projects_query = """
    query {
      activeUser {
        projects {
          items {
            id
            name
          }
        }
      }
    }
    """
    
    projects_result = graphql_tool.query(projects_query)
    if projects_result.get("data"):
        projects = projects_result["data"]["activeUser"]["projects"]["items"]
        if projects:
            # Try to find a project with versions
            test_project_id = None
            test_project_name = None
            
            # First, check which projects have versions
            print(f"\n🔍 Checking {len(projects)} projects for versions...")
            for proj in projects:
                # Quick check for versions
                version_check_query = """
                query CheckVersions($projectId: String!) {
                  project(id: $projectId) {
                    id
                    name
                    versions(limit: 1) {
                      items {
                        id
                        referencedObject
                      }
                    }
                  }
                }
                """
                check_result = graphql_tool.query(version_check_query, variables={"projectId": proj["id"]})
                if check_result.get("data", {}).get("project", {}).get("versions", {}).get("items"):
                    test_project_id = proj["id"]
                    test_project_name = proj["name"]
                    print(f"✅ Found project with versions: {test_project_name}")
                    break
            
            if not test_project_id:
                # Use first project anyway, but warn
                test_project_id = projects[0]["id"]
                test_project_name = projects[0]["name"]
                print(f"⚠️ No projects with versions found. Using first project: {test_project_name}")
                print("   (This project may not have any commits/versions yet)")
            
            print(f"\nTesting with project: {test_project_name} ({test_project_id})")
            
            # Test the tool
            # You can also test with a specific model:
            # result = registry.execute_tool(
            #     "get_element_geometry",
            #     project_id="b45612e372",
            #     model_id="6e13519df2"
            # )
            
            result = registry.execute_tool(
                "get_building_perimeter",
                project_id=test_project_id,
                unit="feet"
            )
            
            if result.get("isError"):
                print(f"❌ Error: {result['content'][0]['text']}")
            else:
                print(f"\n✅ Success!")
                print(result['content'][0]['text'])
                
                # Show structured data
                if result.get("data"):
                    print("\n📊 Structured Data:")
                    print(json.dumps(result["data"], indent=2))
        else:
            print("⚠️ No projects found to test with")
    else:
        print("⚠️ Could not query projects")
        if projects_result.get("errors"):
            print(f"   Errors: {projects_result['errors']}")
    
    # Test find beams tool
    print("\n" + "=" * 70)
    print("Testing: Find Beams Tool")
    print("=" * 70)
    
    if projects:
        test_project_id = projects[0]["id"]
        print(f"\nTesting with project: {projects[0]['name']} ({test_project_id})")
        
        # Test finding all beams
        result = registry.execute_tool(
            "find_beams",
            project_id=test_project_id,
            limit=10
        )
        
        if result.get("isError"):
            print(f"❌ Error: {result['content'][0]['text']}")
        else:
            print(f"\n✅ Success!")
            print(result['content'][0]['text'])
    
    print("\n" + "=" * 70)
    print("✅ Tool Testing Complete!")
    print("=" * 70)
    print("\n💡 Next Steps:")
    print("  1. Review the tool outputs above")
    print("  2. Modify tools in custom_tools/ if needed")
    print("  3. Add tools to MCP server (see ADD_TOOLS_TO_MCP.md)")
    print("  4. Test with LLM in test_natural_language.py")


if __name__ == "__main__":
    test_tool_registry()


