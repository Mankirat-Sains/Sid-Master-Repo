"""Speckle GraphQL client for fetching project data."""
from typing import Dict, Optional, List
import httpx
from src.core.config import settings


class SpeckleClient:
    """Client for querying Speckle GraphQL API."""
    
    def __init__(self):
        """Initialize Speckle client."""
        self.graphql_url = settings.speckle_graphql_url
        self.service_token = settings.speckle_service_token
        self.headers = {
            "Authorization": f"Bearer {self.service_token}",
            "Content-Type": "application/json"
        }
    
    async def execute_query(self, query: str, variables: Optional[Dict] = None) -> Dict:
        """
        Execute a GraphQL query against Speckle API.
        
        Args:
            query: GraphQL query string
            variables: Optional query variables
        
        Returns:
            GraphQL response data
        """
        payload = {
            "query": query,
            "variables": variables or {}
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.graphql_url,
                json=payload,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def get_stream_data(self, stream_id: str) -> Dict:
        """
        Get stream metadata including branches and commits.
        
        Args:
            stream_id: Stream ID
        
        Returns:
            Stream data dictionary
        """
        query = """
            query($streamId: String!) {
                stream(id: $streamId) {
                    id
                    name
                    description
                    createdAt
                    branches {
                        items {
                            name
                            commits {
                                items {
                                    id
                                    message
                                    createdAt
                                    referencedObject
                                }
                            }
                        }
                    }
                }
            }
        """
        
        variables = {"streamId": stream_id}
        result = await self.execute_query(query, variables)
        
        if "errors" in result:
            raise Exception(f"GraphQL errors: {result['errors']}")
        
        return result.get("data", {}).get("stream", {})
    
    async def get_object(self, stream_id: str, object_id: str) -> Dict:
        """
        Get object data from a stream.
        
        Args:
            stream_id: Stream ID
            object_id: Object ID
        
        Returns:
            Object data dictionary
        """
        query = """
            query($streamId: String!, $objectId: String!) {
                stream(id: $streamId) {
                    object(id: $objectId) {
                        id
                        data
                        children {
                            objects {
                                id
                                data
                            }
                        }
                    }
                }
            }
        """
        
        variables = {
            "streamId": stream_id,
            "objectId": object_id
        }
        
        result = await self.execute_query(query, variables)
        
        if "errors" in result:
            raise Exception(f"GraphQL errors: {result['errors']}")
        
        return result.get("data", {}).get("stream", {}).get("object", {})
    
    async def get_comments(self, stream_id: str) -> List[Dict]:
        """
        Get comment threads from a stream.
        
        Args:
            stream_id: Stream ID
        
        Returns:
            List of comment threads
        """
        query = """
            query($streamId: String!) {
                stream(id: $streamId) {
                    commentThreads {
                        items {
                            id
                            rawText
                            createdAt
                            replies {
                                items {
                                    rawText
                                    createdAt
                                }
                            }
                        }
                    }
                }
            }
        """
        
        variables = {"streamId": stream_id}
        result = await self.execute_query(query, variables)
        
        if "errors" in result:
            raise Exception(f"GraphQL errors: {result['errors']}")
        
        threads = result.get("data", {}).get("stream", {}).get("commentThreads", {}).get("items", [])
        return threads
    
    async def build_stream_context(self, stream_id: str, max_recent_commits: int = 5) -> str:
        """
        Build a context string from stream data for AI processing.
        
        Args:
            stream_id: Stream ID
            max_recent_commits: Maximum number of recent commits to include
        
        Returns:
            Formatted context string
        """
        context_parts = []
        
        try:
            # Get stream metadata
            stream_data = await self.get_stream_data(stream_id)
            
            context_parts.append(f"Stream: {stream_data.get('name', 'Unknown')}")
            if stream_data.get('description'):
                context_parts.append(f"Description: {stream_data.get('description')}")
            
            # Get recent commits
            commits = []
            for branch in stream_data.get('branches', {}).get('items', []):
                branch_commits = branch.get('commits', {}).get('items', [])
                commits.extend(branch_commits)
            
            # Sort by creation date and take most recent
            commits.sort(key=lambda x: x.get('createdAt', ''), reverse=True)
            recent_commits = commits[:max_recent_commits]
            
            if recent_commits:
                context_parts.append("\nRecent Commits:")
                for commit in recent_commits:
                    context_parts.append(
                        f"  - {commit.get('message', 'No message')} "
                        f"({commit.get('createdAt', 'Unknown date')})"
                    )
            
            # Get comments
            comments = await self.get_comments(stream_id)
            if comments:
                context_parts.append("\nComments:")
                for thread in comments[:10]:  # Limit to 10 most recent threads
                    context_parts.append(f"  - {thread.get('rawText', '')}")
                    for reply in thread.get('replies', {}).get('items', [])[:3]:
                        context_parts.append(f"    Reply: {reply.get('rawText', '')}")
        
        except Exception as e:
            context_parts.append(f"\n[Error fetching context: {str(e)}]")
        
        return "\n".join(context_parts)

