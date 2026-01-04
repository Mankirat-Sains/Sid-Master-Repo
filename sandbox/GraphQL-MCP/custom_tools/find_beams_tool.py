#!/usr/bin/env python3
"""
Tool: Find Beams by Type/Material
Finds all beams in a project filtered by IFC type and/or material
"""

import json
import logging
from typing import Dict, Any, Optional, List
from custom_tools.base_tool import BaseTool, ToolDefinition

logger = logging.getLogger(__name__)


class FindBeamsTool(BaseTool):
    """
    Tool to find beams/members in a project.
    
    This tool:
    1. Queries for all objects in a project
    2. Filters for beams/members
    3. Optionally filters by material (e.g., "steel", "wood")
    4. Returns list of beams with their properties
    """
    
    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="find_beams",
            description="""Find all beams/members in a project, optionally filtered by material or type.
            
This tool searches through a project's IFC elements and returns all beams/members,
with optional filtering by material (e.g., "steel", "wood", "concrete").

Use this when users ask about:
- Finding all beams in a project
- Finding steel beams
- Finding wood members
- Listing structural elements
- Beam properties or materials""",
            parameters={
                "project_id": {
                    "type": "string",
                    "description": "The project ID to search",
                    "required": True
                },
                "material_filter": {
                    "type": "string",
                    "description": "Optional: Filter by material (e.g., 'steel', 'wood', 'concrete'). Case-insensitive partial match.",
                    "required": False
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of beams to return. Default: 100",
                    "required": False,
                    "default": 100
                }
            },
            handler=self.execute
        )
    
    def execute(
        self,
        project_id: str,
        material_filter: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Execute the find beams tool.
        
        Args:
            project_id: Project ID to search
            material_filter: Optional material filter (e.g., "steel")
            limit: Maximum results to return
            
        Returns:
            Dict with list of beams
        """
        if not self.graphql_client:
            return {
                "isError": True,
                "content": [{"type": "text", "text": "GraphQL client not available"}]
            }
        
        try:
            # Step 1: Get project versions
            version_query = """
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
            
            version_result = self.graphql_client.query(
                version_query,
                variables={"projectId": project_id}
            )
            
            if version_result.get("errors"):
                return {
                    "isError": True,
                    "content": [{"type": "text", "text": f"Error getting versions: {version_result['errors']}"}]
                }
            
            project_data = version_result.get("data", {}).get("project")
            if not project_data:
                return {
                    "isError": True,
                    "content": [{"type": "text", "text": f"Project {project_id} not found"}]
                }
            
            project_name = project_data.get("name", "Unknown")
            versions = project_data.get("versions", {}).get("items", [])
            
            if not versions:
                return {
                    "isError": True,
                    "content": [{"type": "text", "text": f"No versions found for project {project_id}"}]
                }
            
            root_object_id = versions[0].get("referencedObject")
            if not root_object_id:
                return {
                    "isError": True,
                    "content": [{"type": "text", "text": "No root object found in version"}]
                }
            
            # Step 2: Get all objects
            objects_query = """
            query GetObjects($projectId: String!, $objectId: String!) {
              project(id: $projectId) {
                object(id: $objectId) {
                  children(limit: 10000, depth: 5) {
                    objects {
                      id
                      data
                    }
                  }
                }
              }
            }
            """
            
            objects_result = self.graphql_client.query(
                objects_query,
                variables={"projectId": project_id, "objectId": root_object_id}
            )
            
            if objects_result.get("errors"):
                return {
                    "isError": True,
                    "content": [{"type": "text", "text": f"Error getting objects: {objects_result['errors']}"}]
                }
            
            objects_data = objects_result.get("data", {}).get("project", {}).get("object", {})
            children = objects_data.get("children", {}).get("objects", [])
            
            # Step 3: Filter for beams
            beams = []
            material_filter_lower = material_filter.lower() if material_filter else None
            
            for obj in children:
                try:
                    data_str = obj.get("data")
                    if not data_str:
                        continue
                    
                    # Parse JSONObject
                    if isinstance(data_str, str):
                        data = json.loads(data_str)
                    else:
                        data = data_str
                    
                    # Check if it's a beam
                    ifc_type = data.get("ifcType", "").upper()
                    if "BEAM" not in ifc_type and "MEMBER" not in ifc_type:
                        continue
                    
                    # Extract material
                    material = self._extract_material(data)
                    
                    # Apply material filter if specified
                    if material_filter_lower:
                        if not material or material_filter_lower not in material.lower():
                            continue
                    
                    beam_info = {
                        "id": obj.get("id"),
                        "object_id": data.get("id"),
                        "name": data.get("name", "Unnamed"),
                        "ifc_type": data.get("ifcType", ""),
                        "application_id": data.get("applicationId"),
                        "material": material
                    }
                    
                    beams.append(beam_info)
                    
                    if len(beams) >= limit:
                        break
                
                except Exception as e:
                    logger.warning(f"Error processing object {obj.get('id')}: {e}")
                    continue
            
            # Format results
            result_text = f"Found {len(beams)} beam(s) in project: {project_name}\n"
            if material_filter:
                result_text += f"Filtered by material: {material_filter}\n"
            result_text += "\n"
            
            for i, beam in enumerate(beams, 1):
                result_text += f"{i}. {beam['name']}\n"
                result_text += f"   ID: {beam['object_id']}\n"
                result_text += f"   IFC Type: {beam['ifc_type']}\n"
                if beam['material']:
                    result_text += f"   Material: {beam['material']}\n"
                result_text += "\n"
            
            return {
                "isError": False,
                "content": [{"type": "text", "text": result_text}],
                "data": {
                    "project_id": project_id,
                    "project_name": project_name,
                    "beam_count": len(beams),
                    "material_filter": material_filter,
                    "beams": beams
                }
            }
        
        except Exception as e:
            logger.error(f"Find beams tool failed: {e}", exc_info=True)
            return {
                "isError": True,
                "content": [{"type": "text", "text": f"Error finding beams: {str(e)}"}]
            }
    
    def _extract_material(self, data: Dict[str, Any]) -> Optional[str]:
        """Extract material from IFC element data."""
        props = data.get("properties", {})
        
        # Try Attributes first
        attrs = props.get("Attributes", {})
        if attrs.get("Material"):
            return attrs["Material"]
        
        # Try Property Sets
        prop_sets = props.get("Property Sets", {})
        for pset_name, pset_data in prop_sets.items():
            if isinstance(pset_data, dict) and pset_data.get("Material"):
                return pset_data["Material"]
        
        # Check name field
        name = data.get("name", "")
        if "steel" in name.lower() or "wood" in name.lower():
            return name
        
        return None


