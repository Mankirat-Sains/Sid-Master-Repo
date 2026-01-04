"""GraphQL client for Speckle data access"""
import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import sys

# Add parent directory to path to import GraphQL MCP client
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))

try:
    from python_client import GraphQLMCPClient
except ImportError:
    # Fallback: direct HTTP GraphQL client
    import httpx
    
    class GraphQLMCPClient:
        """Fallback HTTP GraphQL client"""
        def __init__(self, endpoint: str, headers: Optional[Dict[str, str]] = None, **kwargs):
            self.endpoint = endpoint
            self.headers = headers or {}
            import httpx
            self.client = httpx.Client()
        
        def start(self):
            pass
        
        def stop(self):
            if hasattr(self, 'client'):
                self.client.close()
        
        def query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
            response = self.client.post(
                self.endpoint,
                json={"query": query, "variables": variables or {}},
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()

from config import settings

logger = logging.getLogger(__name__)


class SpeckleGraphQLClient:
    """Client for querying Speckle via GraphQL"""
    
    def __init__(self):
        self.client: Optional[GraphQLMCPClient] = None
        if settings.GRAPHQL_ENDPOINT:
            headers = {}
            if settings.GRAPHQL_AUTH_TOKEN:
                headers["Authorization"] = f"Bearer {settings.GRAPHQL_AUTH_TOKEN}"
            
            self.client = GraphQLMCPClient(
                endpoint=settings.GRAPHQL_ENDPOINT,
                headers=headers,
                allow_mutations=False
            )
            self.client.start()
            logger.info(f"GraphQL client initialized for {settings.GRAPHQL_ENDPOINT}")
    
    def get_projects(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get list of projects"""
        if not self.client:
            return []
        
        query = """
        query GetProjects($limit: Int!) {
            activeUser {
                projects(limit: $limit) {
                    items {
                        id
                        name
                        description
                    }
                }
            }
        }
        """
        
        try:
            result = self.client.query(query, {"limit": limit})
            if "data" in result and "activeUser" in result["data"]:
                user = result["data"]["activeUser"]
                if user and "projects" in user:
                    return user["projects"].get("items", [])
        except Exception as e:
            logger.error(f"Error fetching projects: {e}")
        
        return []
    
    def get_commit_root_and_closure(
        self,
        project_id: str,
        commit_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Step A: Get commit root object and closure map.
        
        Follows canonical pattern: commit → root → closure
        """
        if not self.client:
            return None
        
        # If no commit_id provided, get latest version
        if not commit_id:
            commit_id = self._get_latest_commit_id(project_id)
            if not commit_id:
                return None
        
        # First get the version to find referencedObject
        query = """
        query GetVersion($projectId: String!) {
            project(id: $projectId) {
                models {
                    items {
                        versions(limit: 1) {
                            items {
                                id
                                referencedObject
                            }
                        }
                    }
                }
            }
        }
        """
        
        try:
            result = self.client.query(query, {"projectId": project_id})
            if "data" in result and "project" in result["data"]:
                project = result["data"]["project"]
                # Extract first version's referencedObject
                for model in project.get("models", {}).get("items", []):
                    for version in model.get("versions", {}).get("items", []):
                        obj_id = version.get("referencedObject")
                        if obj_id:
                            # Now query the object itself
                            obj_query = """
                            query GetObject($projectId: String!, $objectId: String!) {
                                project(id: $projectId) {
                                    object(id: $objectId) {
                                        id
                                        data
                                    }
                                }
                            }
                            """
                            obj_result = self.client.query(obj_query, {
                                "projectId": project_id,
                                "objectId": obj_id
                            })
                            
                            if "data" in obj_result and "project" in obj_result["data"]:
                                obj = obj_result["data"]["project"].get("object")
                                if obj:
                                    closure = obj.get("data", {}).get("__closure", {})
                                    return {
                                        "root_id": obj.get("id"),
                                        "root_data": obj.get("data"),
                                        "closure": closure if isinstance(closure, dict) else {}
                                    }
        except Exception as e:
            logger.error(f"Error fetching commit root: {e}")
        
        return None
    
    def get_objects_in_closure(
        self,
        project_id: str,
        closure: Dict[str, Any],
        speckle_type_filter: Optional[str] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Step B: Query elements within closure scope.
        
        Follows canonical pattern: use closure to scope query
        """
        if not self.client:
            return []
        
        # Extract object IDs from closure
        object_ids = list(closure.keys())[:limit]
        
        if not object_ids:
            return []
        
        # Build query filter
        query_filters = []
        if speckle_type_filter:
            query_filters.append({
                "field": "speckleType",
                "value": speckle_type_filter,
                "operator": "="
            })
        
        query = """
        query GetObjectsInClosure($projectId: String!, $objectIds: [String!]!) {
            project(id: $projectId) {
                object(id: $objectIds[0]) {
                    id
                    speckleType
                    data
                }
            }
        }
        """
        
        # For multiple objects, we need to query each or use a batch query
        # This is a simplified version - actual implementation should batch
        objects = []
        try:
            # Query objects in batches
            batch_size = 50
            for i in range(0, len(object_ids), batch_size):
                batch_ids = object_ids[i:i + batch_size]
                
                # Use project.object query for each (or implement batch if available)
                for obj_id in batch_ids:
                    obj_query = """
                    query GetObject($projectId: String!, $objectId: String!) {
                        project(id: $projectId) {
                            object(id: $objectId) {
                                id
                                speckleType
                                data
                            }
                        }
                    }
                    """
                    result = self.client.query(obj_query, {
                        "projectId": project_id,
                        "objectId": obj_id
                    })
                    
                    if "data" in result and "project" in result["data"]:
                        obj = result["data"]["project"].get("object")
                        if obj:
                            # Apply speckleType filter if specified
                            if speckle_type_filter:
                                obj_type = obj.get("speckleType", "")
                                if speckle_type_filter.lower() not in obj_type.lower():
                                    continue
                            objects.append(obj)
        except Exception as e:
            logger.error(f"Error fetching objects in closure: {e}")
        
        return objects
    
    def _get_latest_commit_id(self, project_id: str) -> Optional[str]:
        """Get the latest commit/version ID for a project"""
        if not self.client:
            return None
        
        query = """
        query GetLatestVersion($projectId: String!) {
            project(id: $projectId) {
                models {
                    items {
                        versions(limit: 1) {
                            items {
                                id
                            }
                        }
                    }
                }
            }
        }
        """
        
        try:
            result = self.client.query(query, {"projectId": project_id})
            if "data" in result and "project" in result["data"]:
                project = result["data"]["project"]
                for model in project.get("models", {}).get("items", []):
                    versions = model.get("versions", {}).get("items", [])
                    if versions:
                        return versions[0].get("id")
        except Exception as e:
            logger.error(f"Error getting latest commit: {e}")
        
        return None
    
    def get_latest_root_object_id(self, project_id: str) -> Optional[str]:
        """
        Get the latest version's referencedObject (root object ID).
        This is the entry point for querying children.
        """
        if not self.client:
            return None
        
        query = """
        query GetLatestRootObject($projectId: String!) {
            project(id: $projectId) {
                models {
                    items {
                        versions(limit: 1) {
                            items {
                                referencedObject
                            }
                        }
                    }
                }
            }
        }
        """
        
        try:
            logger.debug(f"Getting root object for project {project_id}")
            result = self.client.query(query, {"projectId": project_id})
            if "errors" in result:
                error_msg = str(result['errors'])
                logger.warning(f"GraphQL errors getting root for project {project_id}: {error_msg[:200]}")
                return None
            
            if "data" in result and "project" in result["data"]:
                project = result["data"]["project"]
                models = project.get("models", {}).get("items", [])
                if not models:
                    logger.debug(f"Project {project_id} has no models")
                    return None
                
                for model in models:
                    versions = model.get("versions", {}).get("items", [])
                    if versions:
                        root_id = versions[0].get("referencedObject")
                        if root_id:
                            return root_id
                
                logger.debug(f"Project {project_id} has no versions")
        except Exception as e:
            logger.warning(f"Error getting root object for project {project_id}: {e}")
        
        return None
    
    def get_filtered_children(
        self,
        project_id: str,
        root_object_id: str,
        speckle_type_filter: Optional[str] = None,
        limit: int = 1000,  # Reduced for testing
        depth: int = 5  # Reduced for testing
    ) -> List[Dict[str, Any]]:
        """
        Get children of root object with filtering by speckleType.
        Currently filters client-side; server-side filtering can be added once basic query works.
        """
        if not self.client:
            return []
        
        logger.debug(f"Getting children for project {project_id}, root {root_object_id}, filter: {speckle_type_filter}")
        
        # Build query - try without filter first to test basic functionality
        # Note: query parameter format may need adjustment based on Speckle's actual implementation
        query = """
        query GetFilteredChildren($projectId: String!, $objectId: String!, $limit: Int!, $depth: Int!) {
            project(id: $projectId) {
                object(id: $objectId) {
                    id
                    children(
                        limit: $limit,
                        depth: $depth
                    ) {
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
        
        variables = {
            "projectId": project_id,
            "objectId": root_object_id,
            "limit": limit,
            "depth": depth
        }
        
        # If filter specified, we'll filter client-side for now
        # TODO: Once basic query works, add server-side filtering
        
        try:
            logger.info(f"GraphQL: Executing query for project {project_id}, root {root_object_id}")
            logger.debug(f"GraphQL: Query variables - limit: {limit}, depth: {depth}, filter: {speckle_type_filter}")
            logger.debug(f"GraphQL: Query structure - fetching children with speckleType and data fields")
            result = self.client.query(query, variables)
            
            if "errors" in result:
                error_msg = str(result['errors'])
                logger.warning(f"GraphQL errors for project {project_id}: {error_msg[:200]}")
                return []
            
            if "data" in result and "project" in result["data"]:
                obj = result["data"]["project"].get("object")
                if not obj:
                    logger.debug(f"No root object found for project {project_id}")
                    return []
                
                children = obj.get("children")
                if not children:
                    logger.debug(f"No children found for project {project_id}")
                    return []
                
                objects = children.get("objects", [])
                total_count = children.get("totalCount", len(objects))  # Use actual count if totalCount not provided
                objects_before_filter = len(objects)
                
                if total_count > len(objects):
                    logger.info(f"Project {project_id}: {total_count} total children, {len(objects)} returned (may need pagination)")
                
                # Log sample Speckle types to help debug filtering
                if objects_before_filter > 0:
                    sample_types = {}
                    for obj_item in objects[:20]:  # Sample first 20
                        obj_type = obj_item.get("speckleType", "NO_TYPE")
                        sample_types[obj_type] = sample_types.get(obj_type, 0) + 1
                    logger.info(f"Project {project_id}: Sample Speckle types (first 20 objects): {dict(list(sample_types.items())[:10])}")
                
                # Filter by speckleType client-side if filter specified
                if speckle_type_filter:
                    filtered_objects = []
                    unmatched_types = {}
                    for obj_item in objects:
                        obj_type = obj_item.get("speckleType", "")
                        if speckle_type_filter.lower() in obj_type.lower():
                            filtered_objects.append(obj_item)
                        else:
                            # Track unmatched types for debugging
                            unmatched_types[obj_type] = unmatched_types.get(obj_type, 0) + 1
                    objects = filtered_objects
                    logger.info(f"Project {project_id}: Filtered to {len(objects)} objects matching '{speckle_type_filter}' (from {objects_before_filter} total objects)")
                    if len(objects) == 0 and objects_before_filter > 0:
                        logger.warning(f"Project {project_id}: No objects matched filter '{speckle_type_filter}'. Sample unmatched types: {dict(list(unmatched_types.items())[:10])}")
                else:
                    logger.info(f"Project {project_id}: Found {len(objects)} objects (no filter applied)")
                
                # Add project context to each object
                for obj_item in objects:
                    obj_item["project_id"] = project_id
                    obj_item["root_id"] = root_object_id
                
                return objects
        except Exception as e:
            logger.warning(f"Error getting filtered children for project {project_id}: {e}")
        
        return []
    
    def discover_candidates_canonical(
        self,
        project_id: str,
        speckle_type_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Scalable candidate discovery:
        1. Get latest root object ID
        2. ONE query with server-side filtering by speckleType
        3. Returns only matching elements (server does the filtering)
        """
        if not self.client:
            return []
        
        # Get root object ID
        root_id = self.get_latest_root_object_id(project_id)
        if not root_id:
            logger.warning(f"Could not get root object for project {project_id}")
            return []
        
        # ONE query with server-side filtering
        objects = self.get_filtered_children(
            project_id=project_id,
            root_object_id=root_id,
            speckle_type_filter=speckle_type_filter,
            limit=10000,
            depth=10
        )
        
        return objects
    
    def close(self):
        """Close the GraphQL client"""
        if self.client:
            self.client.stop()


# Global GraphQL client instance
graphql_client = SpeckleGraphQLClient()

