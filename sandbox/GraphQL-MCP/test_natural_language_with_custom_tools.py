#!/usr/bin/env python3
"""
Test Natural Language Queries with Custom Tools
This version includes both GraphQL tools AND custom tools
"""

import os
import json
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add paths for imports
current_dir = Path(__file__).parent
if (current_dir / "python_client.py").exists():
    sys.path.insert(0, str(current_dir))
    logger.info(f"✅ Found python_client.py in current directory")

# Also add trainexcel backend path
sys.path.insert(0, str(Path(__file__).parent.parent / "trainexcel" / "backend"))

# Try to import graphql_mcp_tool, with fallback
try:
    from agents.graphql_mcp_tool import get_graphql_tool
except ImportError:
    try:
        from python_client import GraphQLMCPClient
        
        class GraphQLMCPToolWrapper:
            """Wrapper to match GraphQLMCPTool interface"""
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

# Import custom tools
from custom_tools.tool_registry import ToolRegistry

# Load environment
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)


def test_natural_language_with_custom_tools(user_query: str):
    """
    Test natural language query with both GraphQL and custom tools.
    """
    
    # Initialize GraphQL tool
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
    
    # Initialize custom tool registry
    tool_registry = ToolRegistry(graphql_client=graphql_tool)
    
    # Initialize OpenAI
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Get ALL tools (GraphQL + Custom)
    graphql_tools = graphql_tool.get_tool_definitions()
    custom_tools = tool_registry.get_all_tool_definitions()
    all_tools = graphql_tools + custom_tools
    
    print(f"\n📋 Available Tools:")
    print(f"  GraphQL Tools: {len(graphql_tools)}")
    print(f"  Custom Tools: {len(custom_tools)}")
    print(f"  Total: {len(all_tools)}")
    for tool in custom_tools:
        print(f"    - {tool['function']['name']}: {tool['function']['description'][:60]}...")
    
    # System prompt
    system_prompt = """You are an intelligent assistant that can query GraphQL APIs and use specialized tools.

AVAILABLE TOOLS:
1. GraphQL Tools (introspect-schema, query-graphql) - For raw GraphQL queries
2. Custom Tools - Higher-level tools for specific tasks:
   - get_building_perimeter: Calculate building dimensions from beams
   - find_beams: Find beams/members in a project
   - get_element_geometry: Extract geometry, dimensions, spans, elevations, spacing
   - get_element_relationships: Find connections and load paths between elements
   - get_element_properties: Extract material, type, and properties for calculations

WHEN TO USE WHICH TOOL:
- Use custom tools when they match the user's question (e.g., "building perimeter" → get_building_perimeter)
- Use GraphQL tools for general queries or when custom tools don't fit
- Custom tools are faster and more reliable for their specific use cases

CRITICAL RULES:
- If a custom tool matches the question, USE IT instead of constructing GraphQL queries
- Custom tools handle complex data processing automatically
- Always execute tools - don't just introspect"""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_query}
    ]
    
    print(f"\n{'='*70}")
    print(f"User Query: {user_query}")
    print('='*70)
    
    try:
        # Call LLM with function calling
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=[{"type": "function", "function": tool["function"]} for tool in all_tools],
            tool_choice="auto",
            temperature=0.3
        )
        
        message = response.choices[0].message
        
        # Handle tool calls
        if message.tool_calls:
            print(f"\n🔧 LLM decided to use {len(message.tool_calls)} tool(s):")
            
            tool_results = []
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                
                print(f"\n  Tool: {tool_name}")
                print(f"  Args: {json.dumps(tool_args, indent=2)}")
                
                # Execute tool - check if it's a custom tool or GraphQL tool
                result = None
                
                if tool_name in ["get_building_perimeter", "find_beams", "get_element_geometry", 
                                 "get_element_relationships", "get_element_properties"]:
                    # Custom tool
                    print(f"  ✅ Using custom tool: {tool_name}")
                    result = tool_registry.execute_tool(tool_name, **tool_args)
                    print(f"  ✅ Custom tool executed")
                    if result.get("content"):
                        print(f"  Result preview: {result['content'][0]['text'][:200]}...")
                
                elif tool_name in ["graphql_introspect_schema", "introspect-schema"]:
                    # GraphQL introspection
                    schema = graphql_tool.introspect_schema()
                    try:
                        from schema_parser import parse_schema_summary, format_schema_for_llm
                        schema_summary = parse_schema_summary(schema)
                        schema_formatted = format_schema_for_llm(schema_summary)
                        result = {
                            "schema_summary": schema_formatted,
                            "available_queries": [q["name"] for q in schema_summary.get("queries", [])],
                            "example_queries": schema_summary.get("query_examples", [])[:5],
                        }
                        print(f"  ✅ Schema retrieved and parsed")
                    except Exception as e:
                        result = {"schema": schema[:5000] + "..." if len(schema) > 5000 else schema}
                        print(f"  ✅ Schema retrieved (truncated)")
                
                elif tool_name in ["graphql_query", "query-graphql"]:
                    # GraphQL query
                    query = tool_args.get("query")
                    variables = tool_args.get("variables")
                    result = graphql_tool.query(query, variables)
                    print(f"  ✅ GraphQL query executed")
                
                else:
                    result = {"error": f"Unknown tool: {tool_name}"}
                    print(f"  ⚠️ Unknown tool: {tool_name}")
                
                if result is None:
                    result = {"error": "Tool execution failed"}
                
                tool_results.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": tool_name,
                    "content": json.dumps(result)
                })
            
            # Add tool results and get response
            messages.append(message)
            messages.extend(tool_results)
            
            # Get final response
            final_response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=[{"type": "function", "function": tool["function"]} for tool in all_tools],
                tool_choice="auto",
                temperature=0.3
            )
            
            final_message = final_response.choices[0].message
            
            if final_message.content:
                print(f"\n✅ Final Response:")
                print(f"{final_message.content}")
                return {
                    "success": True,
                    "response": final_message.content,
                    "tools_used": [tc.function.name for tc in message.tool_calls]
                }
            else:
                return {
                    "success": False,
                    "error": "No response from LLM"
                }
        else:
            # No tool calls
            print(f"\n💬 Direct response (no tools needed):")
            print(f"{message.content}")
            return {
                "success": True,
                "response": message.content,
                "tools_used": []
            }
    
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


def interactive_mode():
    """Run in interactive mode with custom tools."""
    print("🧪 Interactive Natural Language Query with Custom Tools")
    print("=" * 70)
    print("\nAsk questions - the LLM can use both GraphQL and custom tools!")
    print("Type 'quit', 'exit', or 'q' to stop.\n")
    
    # Initialize once
    graphql_endpoint = os.getenv(
        "GRAPHQL_ENDPOINT",
        "http://k8s-speckle-a8a45c467f-1674783884.ca-central-1.elb.amazonaws.com/graphql"
    )
    auth_token = os.getenv("GRAPHQL_AUTH_TOKEN")
    
    headers = {}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    try:
        graphql_tool = get_graphql_tool(
            endpoint=graphql_endpoint,
            headers=headers if headers else None,
            use_mcp=True
        )
        tool_registry = ToolRegistry(graphql_client=graphql_tool)
        print("✅ Connected!\n")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return
    
    conversation_history = None
    
    while True:
        try:
            user_query = input("\n💬 Your question: ").strip()
            
            if user_query.lower() in ['quit', 'exit', 'q', '']:
                print("\n👋 Goodbye!")
                break
            
            result = test_natural_language_with_custom_tools(user_query)
            
            if not result.get("success"):
                print(f"\n❌ Error: {result.get('error', 'Unknown error')}")
        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        test_natural_language_with_custom_tools(query)
    else:
        interactive_mode()


