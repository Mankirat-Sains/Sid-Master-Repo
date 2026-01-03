#!/usr/bin/env python3
"""
Tool: Get Element Properties
Extracts material, type, and properties from IFC elements for calculations
"""

import json
import logging
from typing import Dict, Any, Optional, List
from custom_tools.base_tool import BaseTool, ToolDefinition

logger = logging.getLogger(__name__)


class ElementPropertiesTool(BaseTool):
    """
    Extract material, type, and properties from elements.
    
    Returns:
    - Material type and properties
    - Member type and cross-section
    - Properties needed for calculations (volume, weight, etc.)
    """
    
    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="get_element_properties",
            description="""Extract material, type, and properties from IFC elements.
            
This tool extracts:
- Material type (steel, wood, concrete, etc.)
- Member type and cross-section properties
- Material properties for calculations
- Dimensions and quantities

Use this when users ask about:
- Material types
- Volume calculations
- Weight calculations
- Member properties
- Cross-section information""",
            parameters={
                "project_id": {
                    "type": "string",
                    "description": "Project ID",
                    "required": True
                },
                "model_id": {
                    "type": "string",
                    "description": "Optional: Model ID. If not provided, uses latest version from project.",
                    "required": False
                },
                "material_filter": {
                    "type": "string",
                    "description": "Optional: Filter by material (e.g., 'steel', 'wood')",
                    "required": False
                },
                "element_type": {
                    "type": "string",
                    "description": "Optional: Filter by IFC type (e.g., 'IfcBeam', 'IfcColumn')",
                    "required": False
                }
            },
            handler=self.execute
        )
    
    def execute(
        self,
        project_id: str,
        model_id: Optional[str] = None,
        material_filter: Optional[str] = None,
        element_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract element properties."""
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
            
            # Extract properties
            properties_data = []
            material_summary = {}
            
            for element in elements:
                try:
                    data_str = element.get("data")
                    if not data_str:
                        logger.debug(f"Element {element.get('id')} has no data field")
                        continue
                    
                    # Parse JSONObject
                    try:
                        if isinstance(data_str, str):
                            data = json.loads(data_str)
                        else:
                            data = data_str
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse data for element {element.get('id')}: {e}")
                        continue
                    
                    if not isinstance(data, dict):
                        logger.debug(f"Element {element.get('id')} data is not a dict")
                        continue
                    
                    ifc_type = data.get("ifcType", "").upper()
                    
                    # Filter by type
                    if element_type and element_type.upper() not in ifc_type:
                        continue
                    
                    # Extract properties
                    props = self._extract_properties(data)
                    if props:
                        # Filter by material
                        if material_filter and material_filter.lower() not in props.get("material", "").lower():
                            continue
                        
                        props["element_id"] = data.get("id") or element.get("id")
                        props["element_name"] = data.get("name", "Unnamed")
                        props["ifc_type"] = data.get("ifcType", "")
                        properties_data.append(props)
                        
                        # Track material summary
                        material = props.get("material", "Unknown")
                        if material not in material_summary:
                            material_summary[material] = {"count": 0, "types": set()}
                        material_summary[material]["count"] += 1
                        material_summary[material]["types"].add(ifc_type)
                
                except Exception as e:
                    logger.warning(f"Error processing element {element.get('id')}: {e}", exc_info=True)
                    continue
            
            # Calculate volumes if we have geometry
            volumes = self._calculate_volumes(properties_data, project_id, root_object_id)
            
            result_text = f"Element Properties Analysis\n"
            result_text += f"Elements Analyzed: {len(properties_data)}\n\n"
            
            if material_summary:
                result_text += f"Material Summary:\n"
                for material, info in material_summary.items():
                    result_text += f"  {material}: {info['count']} elements\n"
                result_text += "\n"
            
            if volumes:
                result_text += f"Volume Calculations:\n"
                for vol in volumes[:10]:
                    result_text += f"  {vol['name']}: {vol['volume']:.2f} cubic units\n"
            
            return {
                "isError": False,
                "content": [{"type": "text", "text": result_text}],
                "data": {
                    "properties": properties_data,
                    "material_summary": {k: {"count": v["count"], "types": list(v["types"])} 
                                        for k, v in material_summary.items()},
                    "volumes": volumes
                }
            }
        
        except Exception as e:
            logger.error(f"Element properties tool failed: {e}", exc_info=True)
            return {
                "isError": True,
                "content": [{"type": "text", "text": f"Error: {str(e)}"}]
            }
    
    def _get_project_version(self, project_id: str, model_id: Optional[str] = None):
        """Get project version."""
        if model_id:
            # Query specific model
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
                      message
                    }
                  }
                }
              }
            }
            """
            result = self.graphql_client.query(query, variables={"projectId": project_id, "modelId": model_id})
            
            if result.get("errors"):
                logger.error(f"GraphQL errors: {result['errors']}")
                return {"isError": True, "content": [{"type": "text", "text": f"GraphQL errors: {result['errors']}"}]}
            
            model_data = result.get("data", {}).get("project", {}).get("model")
            if not model_data:
                logger.error(f"Model {model_id} not found in project {project_id}")
                return {"isError": True, "content": [{"type": "text", "text": f"Model {model_id} not found in project {project_id}"}]}
            
            versions = model_data.get("versions", {}).get("items", [])
        else:
            # Query project versions (original behavior)
            query = """
            query GetVersions($projectId: String!) {
              project(id: $projectId) {
                id
                name
                versions(limit: 10) {
                  items {
                    id
                    referencedObject
                    message
                  }
                }
              }
            }
            """
            result = self.graphql_client.query(query, variables={"projectId": project_id})
            
            if result.get("errors"):
                logger.error(f"GraphQL errors: {result['errors']}")
                return {"isError": True, "content": [{"type": "text", "text": f"GraphQL errors: {result['errors']}"}]}
            
            project_data = result.get("data", {}).get("project")
            if not project_data:
                logger.error(f"Project {project_id} not found")
                return {"isError": True, "content": [{"type": "text", "text": f"Project {project_id} not found"}]}
            
            versions = project_data.get("versions", {}).get("items", [])
        
        if not versions:
            logger.warning(f"No versions found for project {project_id}" + (f" model {model_id}" if model_id else ""))
            return {"isError": True, "content": [{"type": "text", "text": f"No versions found for project {project_id}" + (f" model {model_id}" if model_id else "")}]}
        
        root_object_id = versions[0].get("referencedObject")
        if not root_object_id:
            return {"isError": True, "content": [{"type": "text", "text": "Version found but no referencedObject"}]}
        
        return {"root_object_id": root_object_id}
    
    def _get_all_objects(self, project_id: str, root_object_id: str):
        """Get all objects."""
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
            logger.error(f"GraphQL errors getting objects: {result['errors']}")
            return {"isError": True, "content": [{"type": "text", "text": str(result["errors"])}]}
        
        object_data = result.get("data", {}).get("project", {}).get("object", {})
        if not object_data:
            logger.error(f"No object data returned")
            return {"isError": True, "content": [{"type": "text", "text": "No object data returned"}]}
        
        children = object_data.get("children", {}).get("objects", [])
        total_count = object_data.get("children", {}).get("totalCount", 0)
        
        logger.info(f"Found {total_count} total children, got {len(children)} objects")
        
        # Also include root object if it has data
        elements = []
        root_data = object_data.get("data")
        if root_data:
            elements.append({
                "id": object_data.get("id"),
                "data": root_data,
                "is_root": True
            })
        
        elements.extend(children)
        logger.info(f"Total elements to process: {len(elements)}")
        
        return {"elements": elements}
    
    def _extract_properties(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract material and properties from element data."""
        props = data.get("properties", {})
        
        # Extract material
        material = None
        attrs = props.get("Attributes", {})
        if attrs.get("Material"):
            material = attrs["Material"]
        
        # Try Property Sets
        if not material:
            prop_sets = props.get("Property Sets", {})
            for pset_data in prop_sets.values():
                if isinstance(pset_data, dict) and pset_data.get("Material"):
                    material = pset_data["Material"]
                    break
        
        # Extract quantities
        quantities = props.get("Quantities", {})
        length = None
        area = None
        volume = None
        
        for qty_set in quantities.values():
            if isinstance(qty_set, dict):
                if qty_set.get("Length"):
                    length = qty_set["Length"].get("value") if isinstance(qty_set["Length"], dict) else qty_set["Length"]
                if qty_set.get("Area"):
                    area = qty_set["Area"].get("value") if isinstance(qty_set["Area"], dict) else qty_set["Area"]
                if qty_set.get("Volume"):
                    volume = qty_set["Volume"].get("value") if isinstance(qty_set["Volume"], dict) else qty_set["Volume"]
        
        return {
            "material": material or "Unknown",
            "length": length,
            "area": area,
            "volume": volume,
            "properties": props
        }
    
    def _calculate_volumes(self, properties_data: List[Dict], project_id: str, root_object_id: str) -> List[Dict]:
        """Calculate volumes from geometry if not already provided."""
        # This would need geometry data - simplified for now
        volumes = []
        
        for props in properties_data:
            # If volume already exists, use it
            if props.get("volume"):
                volumes.append({
                    "name": props["element_name"],
                    "volume": props["volume"],
                    "material": props["material"]
                })
            # Otherwise would need to calculate from geometry
            # (Would need to call geometry tool or extract here)
        
        return volumes


