#!/usr/bin/env python3
"""
Tool: Find Element Types
Finds elements by type (Column, Beam, Wall, etc.) with normalized extraction.
This is a minimal, composable tool that can be combined with other tools.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from custom_tools.base_tool import BaseTool, ToolDefinition
from custom_tools.element_normalizer import ElementNormalizer

logger = logging.getLogger(__name__)


class FindElementTypesTool(BaseTool):
    """
    Find elements by type (Column, Beam, Wall, etc.).
    
    This tool:
    1. Queries all elements in a project
    2. Normalizes element types (handles IFC vs Revit inconsistency)
    3. Filters by requested type
    4. Returns normalized list
    
    Can be combined with find_material_types to filter further.
    """
    
    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="find_element_types",
            description="""Find elements by type (Column, Beam, Wall, Slab, etc.).
            
This tool searches through a project and returns elements matching the specified type.
It handles inconsistent data structures (IFC vs Revit) automatically.

Element types: Column, Beam, Wall, Slab, Roof, Bracing, Plate, Member

Use this when users ask about:
- Finding columns
- Finding beams
- Finding walls
- Finding specific element types

This tool can be combined with find_material_types to filter further.
Example: find_element_types(type="Column") then find_material_types(material="Timber")""",
            parameters={
                "project_id": {
                    "type": "string",
                    "description": "Project ID to search",
                    "required": True
                },
                "model_id": {
                    "type": "string",
                    "description": "Optional: Model ID. If not provided, uses latest version.",
                    "required": False
                },
                "element_type": {
                    "type": "string",
                    "description": "Element type to find (e.g., 'Column', 'Beam', 'Wall'). Case-insensitive.",
                    "required": True
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of elements to return. Default: 1000",
                    "required": False,
                    "default": 1000
                }
            },
            handler=self.execute
        )
    
    def execute(
        self,
        project_id: str,
        element_type: str,
        model_id: Optional[str] = None,
        limit: int = 1000
    ) -> Dict[str, Any]:
        """Find elements by type."""
        if not self.graphql_client:
            return {
                "isError": True,
                "content": [{"type": "text", "text": "GraphQL client not available"}]
            }
        
        try:
            # Get project data
            version_result = self._get_project_version(project_id, model_id)
            if version_result.get("isError"):
                return version_result
            
            root_object_id = version_result["root_object_id"]
            
            # Get all objects
            objects_result = self._get_all_objects(project_id, root_object_id)
            if objects_result.get("isError"):
                return objects_result
            
            elements = objects_result["elements"]
            
            # Normalize and filter
            element_type_upper = element_type.upper()
            matching_elements = []
            
            for element in elements:
                normalized = ElementNormalizer.normalize_element(element)
                if not normalized:
                    continue
                
                # Check if type matches
                normalized_type = normalized["element_type"]["type"].upper()
                source_value = normalized["element_type"]["source_value"].upper()
                
                if (element_type_upper in normalized_type or 
                    element_type_upper in source_value or
                    normalized_type in element_type_upper):
                    matching_elements.append(normalized)
                    
                    if len(matching_elements) >= limit:
                        break
            
            # Format results
            result_text = f"Found {len(matching_elements)} {element_type}(s)\n\n"
            
            # Group by normalized type
            type_groups = {}
            for elem in matching_elements:
                norm_type = elem["element_type"]["type"]
                if norm_type not in type_groups:
                    type_groups[norm_type] = []
                type_groups[norm_type].append(elem)
            
            for norm_type, elems in type_groups.items():
                result_text += f"{norm_type}s: {len(elems)}\n"
            
            result_text += "\nSample elements:\n"
            for i, elem in enumerate(matching_elements[:10], 1):
                result_text += f"{i}. {elem['name']} (ID: {elem['element_id'][:20]}...)\n"
                result_text += f"   Type: {elem['element_type']['type']} (from {elem['element_type']['source_type']})\n"
                result_text += f"   Material: {elem['material']['material']}\n"
            
            if len(matching_elements) > 10:
                result_text += f"\n... and {len(matching_elements) - 10} more\n"
            
            return {
                "isError": False,
                "content": [{"type": "text", "text": result_text}],
                "data": {
                    "project_id": project_id,
                    "model_id": model_id,
                    "element_type": element_type,
                    "count": len(matching_elements),
                    "elements": matching_elements[:limit]  # Limit in data too
                }
            }
        
        except Exception as e:
            logger.error(f"Find element types tool failed: {e}", exc_info=True)
            return {
                "isError": True,
                "content": [{"type": "text", "text": f"Error finding elements: {str(e)}"}]
            }
    
    def _get_project_version(self, project_id: str, model_id: Optional[str] = None):
        """Get project version and root object ID."""
        if model_id:
            query = """
            query GetModelVersion($projectId: String!, $modelId: String!) {
              project(id: $projectId) {
                model(id: $modelId) {
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
            }
            """
            result = self.graphql_client.query(query, variables={"projectId": project_id, "modelId": model_id})
            
            if result.get("errors"):
                return {"isError": True, "content": [{"type": "text", "text": f"GraphQL errors: {result['errors']}"}]}
            
            model_data = result.get("data", {}).get("project", {}).get("model")
            if not model_data:
                return {"isError": True, "content": [{"type": "text", "text": f"Model {model_id} not found"}]}
            
            versions = model_data.get("versions", {}).get("items", [])
        else:
            query = """
            query GetVersions($projectId: String!) {
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
            result = self.graphql_client.query(query, variables={"projectId": project_id})
            
            if result.get("errors"):
                return {"isError": True, "content": [{"type": "text", "text": f"GraphQL errors: {result['errors']}"}]}
            
            project_data = result.get("data", {}).get("project")
            if not project_data:
                return {"isError": True, "content": [{"type": "text", "text": f"Project {project_id} not found"}]}
            
            versions = project_data.get("versions", {}).get("items", [])
        
        if not versions:
            return {"isError": True, "content": [{"type": "text", "text": f"No versions found for project {project_id}"}]}
        
        root_object_id = versions[0].get("referencedObject")
        if not root_object_id:
            return {"isError": True, "content": [{"type": "text", "text": "Version found but no referencedObject"}]}
        
        return {"root_object_id": root_object_id}
    
    def _get_all_objects(self, project_id: str, root_object_id: str):
        """Get all objects from project."""
        query = """
        query GetObjects($projectId: String!, $objectId: String!) {
          project(id: $projectId) {
            object(id: $objectId) {
              id
              speckleType
              data
              children(limit: 10000, depth: 10) {
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
        result = self.graphql_client.query(
            query,
            variables={"projectId": project_id, "objectId": root_object_id}
        )
        
        if result.get("errors"):
            return {"isError": True, "content": [{"type": "text", "text": str(result["errors"])}]}
        
        object_data = result.get("data", {}).get("project", {}).get("object", {})
        if not object_data:
            return {"isError": True, "content": [{"type": "text", "text": "No object data returned"}]}
        
        children = object_data.get("children", {}).get("objects", [])
        total_count = object_data.get("children", {}).get("totalCount", 0)
        
        logger.info(f"Found {total_count} total children, got {len(children)} objects")
        
        # Include root object if it has data
        elements = []
        root_data = object_data.get("data")
        if root_data:
            elements.append({
                "id": object_data.get("id"),
                "data": root_data,
                "speckleType": object_data.get("speckleType", "")
            })
        
        elements.extend(children)
        logger.info(f"Total elements to process: {len(elements)}")
        
        return {"elements": elements}


