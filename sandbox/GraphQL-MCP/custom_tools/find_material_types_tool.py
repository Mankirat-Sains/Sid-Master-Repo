#!/usr/bin/env python3
"""
Tool: Find Material Types
Finds elements by material (Timber, Steel, Concrete, etc.) with normalized extraction.
This is a minimal, composable tool that can be combined with other tools.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from custom_tools.base_tool import BaseTool, ToolDefinition
from custom_tools.element_normalizer import ElementNormalizer

logger = logging.getLogger(__name__)


class FindMaterialTypesTool(BaseTool):
    """
    Find elements by material (Timber, Steel, Concrete, etc.).
    
    This tool:
    1. Queries all elements in a project (or filters from provided element IDs)
    2. Normalizes material extraction (handles IFC vs Revit inconsistency)
    3. Filters by requested material
    4. Returns normalized list
    
    Can be combined with find_element_types to filter by both type and material.
    """
    
    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="find_material_types",
            description="""Find elements by material type (Timber, Steel, Concrete, etc.).
            
This tool searches through a project and returns elements matching the specified material.
It handles inconsistent data structures (IFC vs Revit) automatically.

Material types: Timber, Steel, Concrete, Masonry

Use this when users ask about:
- Finding timber elements
- Finding steel elements
- Finding concrete elements
- Material-based queries

This tool can be combined with find_element_types to filter further.
Example: find_element_types(type="Column") then find_material_types(material="Timber", element_ids=[...])
Or use both filters together: find_material_types(material="Timber", element_type="Column")""",
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
                "material": {
                    "type": "string",
                    "description": "Material to find (e.g., 'Timber', 'Steel', 'Concrete'). Case-insensitive.",
                    "required": True
                },
                "element_type": {
                    "type": "string",
                    "description": "Optional: Also filter by element type (e.g., 'Column', 'Beam'). Can be combined with material filter.",
                    "required": False
                },
                "element_ids": {
                    "type": "array",
                    "description": "Optional: Pre-filtered element IDs from another tool (e.g., from find_element_types). If provided, only searches these elements.",
                    "required": False,
                    "items": {"type": "string"}
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
        material: str,
        model_id: Optional[str] = None,
        element_type: Optional[str] = None,
        element_ids: Optional[List[str]] = None,
        limit: int = 1000
    ) -> Dict[str, Any]:
        """Find elements by material."""
        if not self.graphql_client:
            return {
                "isError": True,
                "content": [{"type": "text", "text": "GraphQL client not available"}]
            }
        
        try:
            elements = []
            
            # If element_ids provided, we need to fetch those specific elements
            # Otherwise, get all elements
            if element_ids:
                # Fetch specific elements (for composition with find_element_types)
                elements = self._get_specific_elements(project_id, element_ids)
            else:
                # Get all elements
                version_result = self._get_project_version(project_id, model_id)
                if version_result.get("isError"):
                    return version_result
                
                root_object_id = version_result["root_object_id"]
                objects_result = self._get_all_objects(project_id, root_object_id)
                if objects_result.get("isError"):
                    return objects_result
                
                elements = objects_result["elements"]
            
            # Normalize and filter
            material_upper = material.upper()
            element_type_upper = element_type.upper() if element_type else None
            matching_elements = []
            
            for element in elements:
                normalized = ElementNormalizer.normalize_element(element)
                if not normalized:
                    continue
                
                # Check material match
                normalized_material = normalized["material"]["material"].upper()
                material_raw = normalized["material"]["raw"]
                
                # Check all material fields
                material_matches = (
                    material_upper in normalized_material or
                    material_upper in str(material_raw.get("family", "")).upper() or
                    material_upper in str(material_raw.get("type", "")).upper() or
                    material_upper in str(material_raw.get("name", "")).upper() or
                    material_upper in str(material_raw.get("ifc_material", "")).upper()
                )
                
                if not material_matches:
                    continue
                
                # Also check element type if specified
                if element_type_upper:
                    normalized_type = normalized["element_type"]["type"].upper()
                    source_value = normalized["element_type"]["source_value"].upper()
                    
                    if not (element_type_upper in normalized_type or 
                           element_type_upper in source_value or
                           normalized_type in element_type_upper):
                        continue
                
                matching_elements.append(normalized)
                
                if len(matching_elements) >= limit:
                    break
            
            # Format results
            result_text = f"Found {len(matching_elements)} element(s) with material: {material}\n"
            if element_type:
                result_text += f"Filtered by type: {element_type}\n"
            result_text += "\n"
            
            # Group by material and type
            material_groups = {}
            for elem in matching_elements:
                mat = elem["material"]["material"]
                elem_type = elem["element_type"]["type"]
                key = f"{mat} - {elem_type}"
                if key not in material_groups:
                    material_groups[key] = []
                material_groups[key].append(elem)
            
            for key, elems in material_groups.items():
                result_text += f"{key}: {len(elems)}\n"
            
            result_text += "\nSample elements:\n"
            for i, elem in enumerate(matching_elements[:10], 1):
                result_text += f"{i}. {elem['name']} (ID: {elem['element_id'][:20]}...)\n"
                result_text += f"   Type: {elem['element_type']['type']}\n"
                result_text += f"   Material: {elem['material']['material']} (from {elem['material']['source']}, confidence: {elem['material']['confidence']})\n"
            
            if len(matching_elements) > 10:
                result_text += f"\n... and {len(matching_elements) - 10} more\n"
            
            return {
                "isError": False,
                "content": [{"type": "text", "text": result_text}],
                "data": {
                    "project_id": project_id,
                    "model_id": model_id,
                    "material": material,
                    "element_type": element_type,
                    "count": len(matching_elements),
                    "elements": matching_elements[:limit],
                    "element_ids": [e["element_id"] for e in matching_elements[:limit]]  # For composition
                }
            }
        
        except Exception as e:
            logger.error(f"Find material types tool failed: {e}", exc_info=True)
            return {
                "isError": True,
                "content": [{"type": "text", "text": f"Error finding materials: {str(e)}"}]
            }
    
    def _get_specific_elements(self, project_id: str, element_ids: List[str]) -> List[Dict]:
        """Fetch specific elements by ID (for composition with other tools)."""
        elements = []
        
        # Batch fetch elements (GraphQL allows querying multiple objects)
        # For now, fetch one by one (could be optimized)
        for elem_id in element_ids[:1000]:  # Limit to avoid too many queries
            try:
                query = """
                query GetElement($projectId: String!, $objectId: String!) {
                  project(id: $projectId) {
                    object(id: $objectId) {
                      id
                      speckleType
                      data
                    }
                  }
                }
                """
                result = self.graphql_client.query(
                    query,
                    variables={"projectId": project_id, "objectId": elem_id}
                )
                
                if not result.get("errors"):
                    obj = result.get("data", {}).get("project", {}).get("object")
                    if obj:
                        elements.append({
                            "id": obj.get("id"),
                            "data": obj.get("data"),
                            "speckleType": obj.get("speckleType", "")
                        })
            except Exception as e:
                logger.warning(f"Failed to fetch element {elem_id}: {e}")
                continue
        
        return elements
    
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


