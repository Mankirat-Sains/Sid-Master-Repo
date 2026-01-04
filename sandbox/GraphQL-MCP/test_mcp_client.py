#!/usr/bin/env python3
"""
Test script for GraphQL MCP Client
Tests the Python MCP client integration
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from python_client import GraphQLMCPClient, create_graphql_client

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
    logger.info(f"Loaded environment from {env_path}")


def test_mcp_client():
    """Test the GraphQL MCP client"""
    
    # Get endpoint from environment or use default
    endpoint = os.getenv("GRAPHQL_ENDPOINT", "http://localhost:4000/graphql")
    headers = {}
    
    # If you have an auth token, add it here
    auth_token = os.getenv("GRAPHQL_AUTH_TOKEN")
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    logger.info(f"Testing GraphQL MCP client with endpoint: {endpoint}")
    
    try:
        # Create client
        client = create_graphql_client(
            endpoint=endpoint,
            headers=headers if headers else None,
            allow_mutations=False
        )
        
        # Test 1: Start client and introspect schema
        logger.info("\n" + "="*60)
        logger.info("TEST 1: Starting MCP client and introspecting schema")
        logger.info("="*60)
        
        client.start()
        
        try:
            schema = client.introspect_schema()
            logger.info("✅ Schema introspection successful!")
            logger.info(f"Schema preview (first 500 chars):\n{schema[:500]}...")
        except Exception as e:
            logger.error(f"❌ Schema introspection failed: {e}")
            logger.info("This might mean:")
            logger.info("  1. The GraphQL endpoint is not running")
            logger.info("  2. The endpoint URL is incorrect")
            logger.info("  3. Authentication is required")
            logger.info("  4. The MCP server failed to start")
            return
        
        # Test 2: List available tools
        logger.info("\n" + "="*60)
        logger.info("TEST 2: Listing available MCP tools")
        logger.info("="*60)
        
        try:
            tools = client.get_tool_definitions()
            logger.info(f"✅ Found {len(tools)} tools:")
            for tool in tools:
                func = tool.get("function", {})
                logger.info(f"  - {func.get('name')}: {func.get('description', '')[:80]}...")
        except Exception as e:
            logger.error(f"❌ Failed to list tools: {e}")
        
        # Test 3: Execute a simple query
        logger.info("\n" + "="*60)
        logger.info("TEST 3: Executing sample GraphQL query")
        logger.info("="*60)
        
        # Try a simple query (adjust based on your GraphQL schema)
        sample_query = """
        query {
          __typename
        }
        """
        
        try:
            result = client.query(sample_query)
            logger.info("✅ Query execution successful!")
            logger.info(f"Result: {result}")
        except Exception as e:
            logger.error(f"❌ Query execution failed: {e}")
            logger.info("This might mean:")
            logger.info("  1. The query syntax is incorrect for your schema")
            logger.info("  2. Authentication is required")
            logger.info("  3. The endpoint doesn't support this query")
        
        # Test 4: Test with context manager
        logger.info("\n" + "="*60)
        logger.info("TEST 4: Testing context manager")
        logger.info("="*60)
        
        try:
            with create_graphql_client(endpoint=endpoint, headers=headers if headers else None) as ctx_client:
                schema = ctx_client.introspect_schema()
                logger.info("✅ Context manager works!")
        except Exception as e:
            logger.error(f"❌ Context manager test failed: {e}")
        
        # Cleanup
        client.stop()
        
        logger.info("\n" + "="*60)
        logger.info("✅ All tests completed!")
        logger.info("="*60)
        logger.info("\nNext steps:")
        logger.info("1. Integrate the tool into your orchestrator")
        logger.info("2. Add the tool definitions to your LLM function calling")
        logger.info("3. Test with natural language queries")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_mcp_client()


