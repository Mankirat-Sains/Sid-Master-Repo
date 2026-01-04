#!/usr/bin/env python3
"""
Test natural language to GraphQL conversion
Shows how the LLM converts natural language questions into GraphQL queries
"""

import os
import json
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Setup logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add paths for imports
# Try to import from current directory first (if running from GraphQL-MCP)
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
    # If that fails, try importing directly from current directory and create wrapper
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
        raise ImportError("Could not import graphql_mcp_tool or python_client. Make sure you're in the right directory.")

# Load environment
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)


def test_natural_language_query(user_query: str, graphql_tool=None, openai_client=None, conversation_history=None):
    """
    Test converting a natural language query to GraphQL.
    
    This demonstrates how the LLM would:
    1. Recognize the need for GraphQL
    2. Introspect the schema
    3. Construct a query
    4. Execute it
    
    Args:
        user_query: The natural language question
        graphql_tool: Pre-initialized GraphQL tool (optional, will create if None)
        openai_client: Pre-initialized OpenAI client (optional, will create if None)
        conversation_history: List of previous messages for context (optional)
    """
    
    # Initialize GraphQL tool if not provided
    if graphql_tool is None:
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
    
    # Initialize OpenAI if not provided
    if openai_client is None:
        openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Get tool definitions
    tools = graphql_tool.get_tool_definitions()
    
    # System prompt explaining GraphQL capabilities
    system_prompt = """You are an intelligent assistant that can query GraphQL APIs for Building Information Models.

When a user asks about data from Building Information Models, you MUST:
1. Call introspect-schema to get a summary of available queries
2. Look at the "available_queries" list and "example_queries" in the schema summary
3. **IMMEDIATELY** construct and execute a GraphQL query using query-graphql
4. Return the actual data to the user

CRITICAL RULES:
- The schema summary will show you available queries like "projects", "streams", etc.
- Use the example queries as a template
- If a query requires arguments (like "project(id: String!)"), you may need to query for a list first
- For "What projects are available?", look for a "projects" or "activeUser.projects" query
- NEVER stop after just introspecting - ALWAYS execute a query
- If the first query fails, look at the error message and try a different query from the available list

QUERYING IFC ELEMENTS (Beams, Columns, etc.) WITH GEOMETRY:
To find building elements and their geometry coordinates:
1. Query path: activeUser.projects.items → project.versions.items → project.object(id: referencedObject) → object.children.objects
2. Request the "data" field for each object (it's a JSONObject string that must be parsed)
3. The "data" field contains:
   - "ifcType": "IfcBeam", "IfcColumn", etc. (use this to filter for beams/members)
   - "displayValue": array of referenced object IDs containing geometry
   - "referencedObjects": object containing geometry data
4. Geometry coordinates are in referencedObjects[objectId].data.data as arrays: [x, y, z, x, y, z, ...]
5. To find building perimeter: Extract all x,y coordinates from beams, find min/max x and min/max y values

CALCULATING BUILDING PERIMETER FROM BEAMS:
When asked about building width, length, or perimeter:
1. Query for all beams/members in the project (filter by ifcType === "IfcBeam" in the data JSONObject)
2. Extract geometry coordinates from each beam's referencedObjects
3. Collect all x and y coordinates (ignore z for 2D footprint)
4. Calculate: min_x, max_x, min_y, max_y
5. Building width = max_x - min_x, Building length = max_y - min_y
6. Report the dimensions and which project has these measurements

Example flow for "Which project has a width greater than 10 feet?":
→ Query projects → Get versions → Get root object → Get children objects
→ Parse data JSONObject for each object, filter for ifcType === "IfcBeam"
→ Extract geometry coordinates from referencedObjects
→ Calculate min/max x,y → Calculate width/length
→ Compare to 10 feet and report results

Example flow:
User: "What projects are available?"
→ You: Call introspect-schema → See "projects" in available_queries
→ You: Call query-graphql with query="{ projects { name id } }"
→ You: Return the project list to user

Do not say "I need to query further" - just DO IT. Execute the query immediately."""
    
    # Build messages with conversation history if provided
    messages = []
    if conversation_history is None:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ]
    else:
        # Use existing conversation history, but ensure system prompt is first
        messages = conversation_history.copy()
        if not messages or messages[0].get("role") != "system":
            messages.insert(0, {"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_query})
    
    print(f"\n{'='*70}")
    print(f"User Query: {user_query}")
    print('='*70)
    
    try:
        # Call LLM with function calling
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=[{"type": "function", "function": tool["function"]} for tool in tools],
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
                
                # Execute tool - handle both MCP tool names and wrapper names
                result = None
                if tool_name in ["graphql_introspect_schema", "introspect-schema"]:
                    schema = graphql_tool.introspect_schema()
                    
                    # Parse and summarize schema for LLM
                    try:
                        from schema_parser import parse_schema_summary, format_schema_for_llm
                        schema_summary = parse_schema_summary(schema)
                        schema_formatted = format_schema_for_llm(schema_summary)
                        result = {
                            "schema_summary": schema_formatted,
                            "available_queries": [q["name"] for q in schema_summary.get("queries", [])],
                            "example_queries": schema_summary.get("query_examples", [])[:5],
                            "full_schema_length": len(schema)
                        }
                        print(f"  ✅ Schema retrieved and parsed ({len(schema)} chars)")
                        print(f"  📋 Found {len(schema_summary.get('queries', []))} available queries")
                    except Exception as e:
                        # Fallback to truncated schema
                        logger.warning(f"Schema parsing failed: {e}, using truncated version")
                        result = {
                            "schema": schema[:5000] + "..." if len(schema) > 5000 else schema,
                            "note": "Schema truncated. Full schema is " + str(len(schema)) + " chars"
                        }
                        print(f"  ✅ Schema retrieved (truncated, {len(schema)} chars total)")
                
                elif tool_name in ["graphql_query", "query-graphql"]:
                    query = tool_args.get("query")
                    variables = tool_args.get("variables")
                    result = graphql_tool.query(query, variables)
                    print(f"  ✅ Query executed")
                    print(f"  Result preview: {json.dumps(result, indent=2)[:500]}...")
                
                else:
                    # Unknown tool
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
            
            # Get response from LLM (might want more tool calls)
            # Keep looping until we get a final answer (not just introspection)
            max_iterations = 5
            iteration = 0
            final_message_obj = None
            query_executed = False
            
            while iteration < max_iterations:
                iteration += 1
                print(f"\n📝 LLM iteration {iteration}...")
                
                final_response = openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    tools=[{"type": "function", "function": tool["function"]} for tool in tools],
                    tool_choice="auto",
                    temperature=0.3
                )
                
                final_message_obj = final_response.choices[0].message
                
                # If LLM wants to make more tool calls, handle them
                if final_message_obj.tool_calls:
                    print(f"\n🔧 LLM wants to make {len(final_message_obj.tool_calls)} more tool call(s):")
                    messages.append(final_message_obj)
                    
                    additional_tool_results = []
                    for tool_call in final_message_obj.tool_calls:
                        tool_name = tool_call.function.name
                        tool_args = json.loads(tool_call.function.arguments)
                        
                        print(f"\n  Tool: {tool_name}")
                        print(f"  Args: {json.dumps(tool_args, indent=2)}")
                        
                        # Execute tool - handle both MCP tool names and wrapper names
                        result = None
                        if tool_name in ["graphql_introspect_schema", "introspect-schema"]:
                            schema = graphql_tool.introspect_schema()
                            
                            # Parse and summarize schema for LLM
                            try:
                                from schema_parser import parse_schema_summary, format_schema_for_llm
                                schema_summary = parse_schema_summary(schema)
                                schema_formatted = format_schema_for_llm(schema_summary)
                                result = {
                                    "schema_summary": schema_formatted,
                                    "available_queries": [q["name"] for q in schema_summary.get("queries", [])],
                                    "example_queries": schema_summary.get("query_examples", [])[:5],
                                    "full_schema_length": len(schema)
                                }
                                print(f"  ✅ Schema retrieved and parsed ({len(schema)} chars)")
                                print(f"  📋 Found {len(schema_summary.get('queries', []))} available queries")
                            except Exception as e:
                                # Fallback to truncated schema
                                logger.warning(f"Schema parsing failed: {e}, using truncated version")
                                result = {
                                    "schema": schema[:5000] + "..." if len(schema) > 5000 else schema,
                                    "note": "Schema truncated. Full schema is " + str(len(schema)) + " chars"
                                }
                                print(f"  ✅ Schema retrieved (truncated, {len(schema)} chars total)")
                        
                        elif tool_name in ["graphql_query", "query-graphql"]:
                            query = tool_args.get("query")
                            variables = tool_args.get("variables")
                            result = graphql_tool.query(query, variables)
                            query_executed = True
                            print(f"  ✅ Query executed!")
                            print(f"  Result: {json.dumps(result, indent=2)[:500]}...")
                        
                        else:
                            # Unknown tool
                            result = {"error": f"Unknown tool: {tool_name}"}
                            print(f"  ⚠️ Unknown tool: {tool_name}")
                        
                        if result is None:
                            result = {"error": "Tool execution failed"}
                        
                        additional_tool_results.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": tool_name,
                            "content": json.dumps(result)
                        })
                    
                    messages.extend(additional_tool_results)
                    # Continue loop to get next response
                    continue
                else:
                    # No more tool calls, we have the final answer
                    break
            
            # Get final message
            if final_message_obj and final_message_obj.content:
                final_message = final_message_obj.content
            else:
                final_message = "LLM did not provide a final response after multiple iterations."
            
            if not query_executed:
                print(f"\n⚠️ WARNING: No GraphQL query was executed. LLM only introspected schema.")
            
            print(f"\n✅ Final Response:")
            print(f"{final_message}")
            
            result = {
                "success": True,
                "response": final_message,
                "tools_used": [tc.function.name for tc in message.tool_calls],
                "conversation_history": messages  # Return updated conversation history
            }
            
            # Add assistant's final response to conversation history
            messages.append({"role": "assistant", "content": final_message})
            result["conversation_history"] = messages
            
            return result
        else:
            # No tool calls
            print(f"\n💬 Direct response (no tools needed):")
            print(f"{message.content}")
            
            # Update conversation history
            if conversation_history is not None:
                messages.append({"role": "assistant", "content": message.content})
            
            return {
                "success": True,
                "response": message.content,
                "tools_used": [],
                "conversation_history": messages
            }
    
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e), "conversation_history": conversation_history or []}


def interactive_mode():
    """Run in interactive mode, allowing continuous questions"""
    print("🧪 Interactive Natural Language to GraphQL Query")
    print("=" * 70)
    print("\nAsk questions about your GraphQL database in plain English!")
    print("Type 'quit', 'exit', or 'q' to stop.\n")
    
    # Initialize clients once (more efficient)
    print("🔧 Initializing GraphQL connection...")
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
        openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        print("✅ Connected!\n")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return
    
    # Conversation history for context across questions
    conversation_history = None
    
    while True:
        try:
            # Get user input
            user_query = input("\n💬 Your question: ").strip()
            
            # Check for exit commands
            if user_query.lower() in ['quit', 'exit', 'q', '']:
                print("\n👋 Goodbye!")
                break
            
            # Process the query
            result = test_natural_language_query(
                user_query,
                graphql_tool=graphql_tool,
                openai_client=openai_client,
                conversation_history=conversation_history
            )
            
            # Update conversation history for next question
            if result.get("conversation_history"):
                conversation_history = result["conversation_history"]
            
            # Show any errors
            if not result.get("success"):
                print(f"\n❌ Error: {result.get('error', 'Unknown error')}")
        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except EOFError:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            logger.exception("Error in interactive mode")


if __name__ == "__main__":
    # Example queries to test
    test_queries = [
        "What projects are available in Speckle?",
        "Show me all streams",
        "What's the latest commit?",
    ]
    
    # Check for interactive mode flag
    if len(sys.argv) > 1 and sys.argv[1] in ['-i', '--interactive', 'interactive']:
        interactive_mode()
    elif len(sys.argv) > 1:
        # Custom query from command line
        query = " ".join(sys.argv[1:])
        print("🧪 Testing Natural Language to GraphQL Conversion")
        print("=" * 70)
        test_natural_language_query(query)
    else:
        # Default: start interactive mode
        interactive_mode()
