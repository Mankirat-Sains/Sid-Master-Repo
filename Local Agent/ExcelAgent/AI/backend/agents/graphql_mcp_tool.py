#!/usr/bin/env python3
"""
GraphQL MCP Tool Integration
Wraps the MCP GraphQL server to provide GraphQL query capabilities to the orchestrator
"""

import json
import logging
import os
from typing import Dict, Any, Optional, List
from pathlib import Path

# Import the MCP client
try:
    # Try to import from the GraphQL-MCP directory
    import sys
    # Try multiple possible paths
    current_file = Path(__file__)
    possible_paths = [
        current_file.parent.parent.parent.parent.parent / "GraphQL-MCP",  # From trainexcel/backend/agents
        current_file.parent.parent.parent.parent / "GraphQL-MCP",  # Alternative path
        Path(__file__).parent.parent.parent / "GraphQL-MCP",  # From GraphQL-MCP directory itself
        Path.cwd() / "GraphQL-MCP",  # Current working directory
        Path.cwd().parent / "GraphQL-MCP",  # Parent of current directory
    ]
    
    mcp_dir = None
    for path in possible_paths:
        if path.exists() and (path / "python_client.py").exists():
            mcp_dir = path
            break
    
    if mcp_dir:
        sys.path.insert(0, str(mcp_dir))
        from python_client import GraphQLMCPClient
        logger = logging.getLogger(__name__)
        logger.info(f"✅ Found MCP client at: {mcp_dir}")
    else:
        # Fallback: use direct HTTP (for backward compatibility)
        GraphQLMCPClient = None
        logger = logging.getLogger(__name__)
        logger.warning("GraphQL-MCP directory not found, using direct HTTP client")
except ImportError as e:
    GraphQLMCPClient = None
    logger = logging.getLogger(__name__)
    logger.warning(f"Could not import MCP client: {e}, using direct HTTP client")

logger = logging.getLogger(__name__)


class GraphQLMCPTool:
    """
    Python wrapper for the MCP GraphQL server.
    
    This tool allows the orchestrator to:
    1. Introspect GraphQL schemas
    2. Execute GraphQL queries
    
    The LLM in the orchestrator will use these tools to convert natural language
    queries into GraphQL queries.
    """
    
    def __init__(
        self,
        endpoint: str,
        headers: Optional[Dict[str, str]] = None,
        allow_mutations: bool = False,
        use_mcp: bool = True
    ):
        """
        Initialize the GraphQL MCP tool.
        
        Args:
            endpoint: GraphQL endpoint URL (e.g., "http://localhost:3000/graphql")
            headers: Optional headers dict (will be JSON stringified)
            allow_mutations: Whether to allow mutation operations
            use_mcp: Whether to use MCP server (True) or direct HTTP (False)
        """
        self.endpoint = endpoint
        self.headers = headers or {}
        self.allow_mutations = allow_mutations
        self.use_mcp = use_mcp and GraphQLMCPClient is not None
        
        if self.use_mcp:
            self.mcp_client = GraphQLMCPClient(
                endpoint=endpoint,
                headers=headers,
                allow_mutations=allow_mutations
            )
            logger.info(f"GraphQL MCP Tool initialized (using MCP) for endpoint: {endpoint}")
        else:
            self.mcp_client = None
            logger.info(f"GraphQL MCP Tool initialized (using direct HTTP) for endpoint: {endpoint}")
    
    def introspect_schema(self) -> str:
        """
        Introspect the GraphQL schema.
        
        Returns:
            GraphQL schema as SDL (Schema Definition Language) string
        """
        if self.use_mcp and self.mcp_client:
            try:
                if not self.mcp_client._started:
                    self.mcp_client.start()
                return self.mcp_client.introspect_schema()
            except Exception as e:
                logger.error(f"MCP introspection failed, falling back to HTTP: {e}")
                # Fall through to HTTP fallback
        
        # Fallback to direct HTTP introspection
        import httpx
        
        introspection_query = """
        query IntrospectionQuery {
          __schema {
            queryType { name }
            mutationType { name }
            subscriptionType { name }
            types {
              ...FullType
            }
            directives {
              name
              description
              locations
              args {
                ...InputValue
              }
            }
          }
        }
        
        fragment FullType on __Type {
          kind
          name
          description
          fields(includeDeprecated: true) {
            name
            description
            args {
              ...InputValue
            }
            type {
              ...TypeRef
            }
            isDeprecated
            deprecationReason
          }
          inputFields {
            ...InputValue
          }
          interfaces {
            ...TypeRef
          }
          enumValues(includeDeprecated: true) {
            name
            description
            isDeprecated
            deprecationReason
          }
          possibleTypes {
            ...TypeRef
          }
        }
        
        fragment InputValue on __InputValue {
          name
          description
          type { ...TypeRef }
          defaultValue
        }
        
        fragment TypeRef on __Type {
          kind
          name
          ofType {
            kind
            name
            ofType {
              kind
              name
              ofType {
                kind
                name
                ofType {
                  kind
                  name
                  ofType {
                    kind
                    name
                    ofType {
                      kind
                      name
                      ofType {
                        kind
                        name
                      }
                    }
                  }
                }
              }
            }
          }
        }
        """
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    self.endpoint,
                    json={"query": introspection_query},
                    headers={
                        "Content-Type": "application/json",
                        **self.headers
                    }
                )
                response.raise_for_status()
                data = response.json()
                return json.dumps(data, indent=2)
        except Exception as e:
            logger.error(f"Failed to introspect GraphQL schema: {e}")
            raise
    
    def query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a GraphQL query.
        
        Args:
            query: GraphQL query string
            variables: Optional query variables
        
        Returns:
            GraphQL response as dict
        """
        if self.use_mcp and self.mcp_client:
            try:
                if not self.mcp_client._started:
                    self.mcp_client.start()
                return self.mcp_client.query(query, variables)
            except Exception as e:
                logger.error(f"MCP query failed, falling back to HTTP: {e}")
                # Fall through to HTTP fallback
        
        # Fallback to direct HTTP
        import httpx
        
        try:
            with httpx.Client(timeout=30.0) as client:
                payload = {"query": query}
                if variables:
                    payload["variables"] = variables
                
                response = client.post(
                    self.endpoint,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        **self.headers
                    }
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"GraphQL query failed: {e}")
            raise
    
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Get tool definitions for the orchestrator.
        
        Returns tool schemas that the LLM can use to call these functions.
        """
        # If using MCP, try to get tool definitions from MCP server
        if self.use_mcp and self.mcp_client:
            try:
                if not self.mcp_client._started:
                    self.mcp_client.start()
                return self.mcp_client.get_tool_definitions()
            except Exception as e:
                logger.warning(f"Could not get MCP tool definitions: {e}, using defaults")
        
        # Default tool definitions
        return [
            {
                "type": "function",
                "function": {
                    "name": "graphql_introspect_schema",
                    "description": (
                        "Introspect the GraphQL schema to understand what queries and types are available. "
                        "Call this first before executing queries to understand the API structure. "
                        "This is essential for constructing valid GraphQL queries from natural language."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "graphql_query",
                    "description": (
                        "Execute a GraphQL query against the endpoint. "
                        "Use this after introspecting the schema to fetch data. "
                        "The query should be a valid GraphQL query string. "
                        "You must construct the query based on the schema you learned from introspect_schema."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The GraphQL query string to execute (e.g., '{ projects { name id } }')"
                            },
                            "variables": {
                                "type": "object",
                                "description": "Optional variables for the query (as a JSON object)",
                                "additionalProperties": True
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ]
    
    def stop(self):
        """Stop the MCP client if running"""
        if self.use_mcp and self.mcp_client and self.mcp_client._started:
            self.mcp_client.stop()


# Convenience function for orchestrator
def get_graphql_tool(
    endpoint: str,
    headers: Optional[Dict[str, str]] = None,
    use_mcp: bool = True
) -> GraphQLMCPTool:
    """
    Factory function to create a GraphQL MCP tool instance.
    
    Usage in orchestrator:
        from agents.graphql_mcp_tool import get_graphql_tool
        
        graphql_tool = get_graphql_tool(
            endpoint="http://localhost:3000/graphql",
            headers={"Authorization": "Bearer token"},
            use_mcp=True  # Use MCP server (recommended)
        )
        
        # Add tools to orchestrator
        tools = graphql_tool.get_tool_definitions()
        
        # In your LLM function calling:
        # When user asks "What projects are in Speckle?"
        # 1. LLM calls graphql_introspect_schema() to understand the API
        # 2. LLM constructs query: "{ projects { name id } }"
        # 3. LLM calls graphql_query(query="{ projects { name id } }")
        # 4. Returns results to user
    """
    return GraphQLMCPTool(endpoint=endpoint, headers=headers, use_mcp=use_mcp)


