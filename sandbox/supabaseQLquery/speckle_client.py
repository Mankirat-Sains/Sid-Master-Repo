"""
SIDIAN - Speckle GraphQL Client
===============================
Handles all communication with the Speckle GraphQL API for BIM data retrieval.

Speckle GraphQL Docs: https://speckle.guide/dev/graphql-api.html
"""

import os
import json
import requests
from typing import Optional, Dict, Any


class SpeckleClient:
    """Client for querying Speckle's GraphQL API."""
    
    def __init__(
        self,
        url: Optional[str] = None,
        token: Optional[str] = None,
        default_stream_id: Optional[str] = None
    ):
        """
        Initialize the Speckle client.
        
        Args:
            url: Speckle server URL (defaults to SPECKLE_URL env var)
            token: Personal access token (defaults to SPECKLE_TOKEN env var)
            default_stream_id: Default stream to query (defaults to SPECKLE_STREAM_ID env var)
        """
        # Default to AWS-hosted Speckle server
        default_url = "http://k8s-speckle-a8a45c467f-1674783884.ca-central-1.elb.amazonaws.com"
        self.url = url or os.getenv("SPECKLE_URL", default_url)
        
        # Clean up URL (remove trailing slash if present)
        self.url = self.url.rstrip('/')
        
        self.token = token or os.getenv("SPECKLE_TOKEN")
        self.default_stream_id = default_stream_id or os.getenv("SPECKLE_STREAM_ID")
        
        if not self.token:
            raise ValueError(
                "Speckle token required. Set SPECKLE_TOKEN env var or pass token parameter."
            )
        
        self.graphql_endpoint = f"{self.url}/graphql"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        # Debug output to verify endpoint
        print(f"🔗 Speckle GraphQL Endpoint: {self.graphql_endpoint}")
    
    def execute_query(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a raw GraphQL query against Speckle.
        
        Args:
            query: GraphQL query string
            variables: Optional variables for the query
            
        Returns:
            JSON response from Speckle API
        """
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        
        try:
            response = requests.post(
                self.graphql_endpoint,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            # Check for GraphQL errors
            if "errors" in result:
                return {
                    "success": False,
                    "errors": result["errors"],
                    "data": result.get("data")
                }
            
            return {
                "success": True,
                "data": result.get("data", {})
            }
            
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e),
                "data": None
            }
    
    # =========================================================================
    # Convenience Methods (Pre-built queries)
    # =========================================================================
    
    def get_user_info(self) -> Dict[str, Any]:
        """Get current authenticated user info."""
        query = """
        query {
            activeUser {
                id
                name
                email
                avatar
            }
        }
        """
        return self.execute_query(query)
    
    def list_streams(self, limit: int = 25) -> Dict[str, Any]:
        """List user's streams/projects."""
        query = """
        query($limit: Int!) {
            activeUser {
                streams(limit: $limit) {
                    totalCount
                    items {
                        id
                        name
                        description
                        updatedAt
                        role
                    }
                }
            }
        }
        """
        return self.execute_query(query, {"limit": limit})
    
    def get_stream_info(self, stream_id: Optional[str] = None) -> Dict[str, Any]:
        """Get detailed info about a stream."""
        sid = stream_id or self.default_stream_id
        if not sid:
            return {"success": False, "error": "No stream_id provided"}
        
        query = """
        query($streamId: String!) {
            stream(id: $streamId) {
                id
                name
                description
                isPublic
                createdAt
                updatedAt
                branches {
                    totalCount
                    items {
                        id
                        name
                        description
                    }
                }
                commits(limit: 5) {
                    totalCount
                    items {
                        id
                        message
                        createdAt
                        authorName
                    }
                }
            }
        }
        """
        return self.execute_query(query, {"streamId": sid})
    
    def get_objects(
        self,
        stream_id: Optional[str] = None,
        limit: int = 50,
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get objects from the latest commit of a stream.
        
        Args:
            stream_id: Stream to query
            limit: Max number of child objects to return
            depth: How deep to traverse the object tree
        """
        sid = stream_id or self.default_stream_id
        if not sid:
            return {"success": False, "error": "No stream_id provided"}
        
        query = """
        query($streamId: String!, $limit: Int!) {
            stream(id: $streamId) {
                branch(name: "main") {
                    commits(limit: 1) {
                        items {
                            id
                            message
                            referencedObject
                        }
                    }
                }
            }
        }
        """
        
        # First get the latest commit's referenced object
        result = self.execute_query(query, {"streamId": sid, "limit": limit})
        
        if not result.get("success"):
            return result
        
        try:
            commits = result["data"]["stream"]["branch"]["commits"]["items"]
            if not commits:
                return {"success": False, "error": "No commits found in stream"}
            
            object_id = commits[0]["referencedObject"]
            
            # Now fetch the actual object tree
            object_query = """
            query($streamId: String!, $objectId: String!) {
                stream(id: $streamId) {
                    object(id: $objectId) {
                        id
                        speckleType
                        totalChildrenCount
                        children(limit: 100, depth: 2) {
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
            return self.execute_query(object_query, {"streamId": sid, "objectId": object_id})
            
        except (KeyError, IndexError) as e:
            return {"success": False, "error": f"Failed to parse response: {e}"}
    
    def search_objects_by_type(
        self,
        speckle_type: str,
        stream_id: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Search for objects by their Speckle type.
        
        Common types:
        - Objects.Structural.Column
        - Objects.Structural.Beam
        - Objects.Structural.Wall
        - Objects.Structural.Slab
        - Objects.BuiltElements.Wall
        - Objects.BuiltElements.Floor
        - Etc.
        """
        sid = stream_id or self.default_stream_id
        if not sid:
            return {"success": False, "error": "No stream_id provided"}
        
        # This query structure depends on your Speckle data structure
        # Adjust based on your actual model
        query = f"""
        query($streamId: String!) {{
            stream(id: $streamId) {{
                branch(name: "main") {{
                    commits(limit: 1) {{
                        items {{
                            referencedObject
                        }}
                    }}
                }}
            }}
        }}
        """
        return self.execute_query(query, {"streamId": sid})


# =============================================================================
# Example Queries for LLM Reference
# =============================================================================

EXAMPLE_QUERIES = {
    "get_all_objects": """
query GetObjects($streamId: String!) {
    stream(id: $streamId) {
        branch(name: "main") {
            commits(limit: 1) {
                items {
                    referencedObject
                }
            }
        }
    }
}
""",
    
    "get_object_children": """
query GetObjectChildren($streamId: String!, $objectId: String!, $limit: Int!) {
    stream(id: $streamId) {
        object(id: $objectId) {
            id
            speckleType
            totalChildrenCount
            children(limit: $limit, depth: 2) {
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
""",
    
    "list_user_streams": """
query ListStreams {
    activeUser {
        streams(limit: 25) {
            items {
                id
                name
                description
                updatedAt
            }
        }
    }
}
""",
    
    "get_stream_branches": """
query GetBranches($streamId: String!) {
    stream(id: $streamId) {
        id
        name
        branches {
            items {
                id
                name
                commits(limit: 5) {
                    items {
                        id
                        message
                        createdAt
                    }
                }
            }
        }
    }
}
"""
}


# Quick test
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    try:
        client = SpeckleClient()
        print("✅ Speckle client initialized")
        
        # Test user info
        result = client.get_user_info()
        if result["success"]:
            print(f"✅ Connected as: {result['data']['activeUser']['name']}")
        else:
            print(f"❌ Error: {result.get('error') or result.get('errors')}")
            
    except ValueError as e:
        print(f"❌ Configuration error: {e}")

