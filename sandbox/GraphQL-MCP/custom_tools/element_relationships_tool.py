#!/usr/bin/env python3
"""
Tool: Get Element Relationships
Finds connections and relationships between structural elements
"""

import json
import logging
from typing import Dict, Any, Optional, List
from collections import defaultdict
from custom_tools.base_tool import BaseTool, ToolDefinition

logger = logging.getLogger(__name__)


class ElementRelationshipsTool(BaseTool):
    """
    Find connections and relationships between elements.
    
    Identifies:
    - Which beams connect to which columns
    - Load paths (what loads on what)
    - Structural hierarchy
    - Parent-child relationships
    """
    
    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="get_element_relationships",
            description="""Find connections and relationships between structural elements.
            
This tool identifies:
- Which beams connect to which columns
- Load paths (which elements transfer loads to which)
- Structural hierarchy and connections
- Parent-child relationships

Use this when users ask about:
- Which beams connect to a column
- Load tracking (what loads on what)
- Structural connections
- Element relationships""",
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
                "element_id": {
                    "type": "string",
                    "description": "Optional: Specific element ID to find connections for",
                    "required": False
                },
                "element_type": {
                    "type": "string",
                    "description": "Optional: Filter by type (e.g., 'IfcColumn' to find what connects to columns)",
                    "required": False
                }
            },
            handler=self.execute
        )
    
    def execute(
        self,
        project_id: str,
        model_id: Optional[str] = None,
        element_id: Optional[str] = None,
        element_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Find element relationships."""
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
            
            # Extract element data and geometry
            element_data = []
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
                    
                    elem_id = data.get("id") or element.get("id")
                    ifc_type = data.get("ifcType", "").upper()
                    
                    # Filter if specified
                    if element_id and elem_id != element_id:
                        continue
                    if element_type and element_type.upper() not in ifc_type:
                        continue
                    
                    # Extract geometry for connection analysis
                    geom = self._extract_geometry(data)
                    
                    element_data.append({
                        "id": elem_id,
                        "name": data.get("name", "Unnamed"),
                        "ifc_type": data.get("ifcType", ""),
                        "geometry": geom,
                        "data": data
                    })
                except Exception as e:
                    logger.warning(f"Error processing element {element.get('id')}: {e}", exc_info=True)
                    continue
            
            # Find connections based on geometry proximity
            connections = self._find_connections(element_data)
            
            # Build load paths
            load_paths = self._build_load_paths(element_data, connections)
            
            result_text = f"Element Relationships Analysis\n"
            result_text += f"Elements Analyzed: {len(element_data)}\n"
            result_text += f"Connections Found: {len(connections)}\n\n"
            
            if element_id:
                # Show connections for specific element
                elem_connections = [c for c in connections if c["element1_id"] == element_id or c["element2_id"] == element_id]
                if elem_connections:
                    result_text += f"Connections for {element_id}:\n"
                    for conn in elem_connections:
                        other_id = conn["element2_id"] if conn["element1_id"] == element_id else conn["element1_id"]
                        result_text += f"  - {conn['type']}: {other_id}\n"
            
            # Show load paths (columns receiving loads from beams)
            column_loads = [lp for lp in load_paths if "COLUMN" in lp["target_type"].upper()]
            if column_loads:
                result_text += f"\nLoad Paths (Columns receiving loads):\n"
                for lp in column_loads[:10]:
                    result_text += f"  {lp['target_name']} receives loads from:\n"
                    for source in lp["sources"]:
                        result_text += f"    - {source['name']} ({source['type']})\n"
            
            return {
                "isError": False,
                "content": [{"type": "text", "text": result_text}],
                "data": {
                    "connections": connections,
                    "load_paths": load_paths
                }
            }
        
        except Exception as e:
            logger.error(f"Element relationships tool failed: {e}", exc_info=True)
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
    
    def _extract_geometry(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract geometry coordinates."""
        ref_objects = data.get("referencedObjects", {})
        all_coords = []
        
        for ref_obj in ref_objects.values():
            ref_data = ref_obj.get("data", {})
            coords = ref_data.get("data", [])
            if coords and isinstance(coords, list):
                all_coords.extend(coords)
        
        if not all_coords or len(all_coords) < 3:
            return None
        
        x_coords = [all_coords[i] for i in range(0, len(all_coords), 3) if i < len(all_coords)]
        y_coords = [all_coords[i+1] for i in range(0, len(all_coords), 3) if i+1 < len(all_coords)]
        z_coords = [all_coords[i+2] for i in range(0, len(all_coords), 3) if i+2 < len(all_coords)]
        
        if not x_coords:
            return None
        
        return {
            "center": {
                "x": sum(x_coords) / len(x_coords),
                "y": sum(y_coords) / len(y_coords) if y_coords else 0,
                "z": sum(z_coords) / len(z_coords) if z_coords else 0
            },
            "bounds": {
                "min_x": min(x_coords),
                "max_x": max(x_coords),
                "min_y": min(y_coords) if y_coords else 0,
                "max_y": max(y_coords) if y_coords else 0,
                "min_z": min(z_coords) if z_coords else 0,
                "max_z": max(z_coords) if z_coords else 0
            }
        }
    
    def _find_connections(self, elements: List[Dict]) -> List[Dict]:
        """Find connections based on geometry proximity."""
        connections = []
        tolerance = 0.1  # Connection tolerance in units
        
        for i, elem1 in enumerate(elements):
            if not elem1.get("geometry"):
                continue
            
            geom1 = elem1["geometry"]
            type1 = elem1["ifc_type"].upper()
            
            for elem2 in elements[i+1:]:
                if not elem2.get("geometry"):
                    continue
                
                geom2 = elem2["geometry"]
                type2 = elem2["ifc_type"].upper()
                
                # Check if elements are connected (geometrically close)
                if self._are_connected(geom1, geom2, tolerance):
                    # Determine connection type
                    conn_type = self._determine_connection_type(type1, type2)
                    
                    connections.append({
                        "element1_id": elem1["id"],
                        "element1_name": elem1["name"],
                        "element1_type": type1,
                        "element2_id": elem2["id"],
                        "element2_name": elem2["name"],
                        "element2_type": type2,
                        "type": conn_type
                    })
        
        return connections
    
    def _are_connected(self, geom1: Dict, geom2: Dict, tolerance: float) -> bool:
        """Check if two elements are geometrically connected."""
        bounds1 = geom1.get("bounds", {})
        bounds2 = geom2.get("bounds", {})
        
        # Check if bounding boxes overlap or are close
        x_overlap = not (bounds1["max_x"] < bounds2["min_x"] - tolerance or 
                        bounds2["max_x"] < bounds1["min_x"] - tolerance)
        y_overlap = not (bounds1["max_y"] < bounds2["min_y"] - tolerance or 
                        bounds2["max_y"] < bounds1["min_y"] - tolerance)
        z_overlap = not (bounds1["max_z"] < bounds2["min_z"] - tolerance or 
                        bounds2["max_z"] < bounds1["min_z"] - tolerance)
        
        # Elements are connected if they overlap in at least 2 dimensions
        overlaps = sum([x_overlap, y_overlap, z_overlap])
        return overlaps >= 2
    
    def _determine_connection_type(self, type1: str, type2: str) -> str:
        """Determine the type of connection."""
        if "BEAM" in type1 and "COLUMN" in type2:
            return "beam_to_column"
        elif "COLUMN" in type1 and "BEAM" in type2:
            return "beam_to_column"
        elif "BEAM" in type1 and "BEAM" in type2:
            return "beam_to_beam"
        elif "COLUMN" in type1 and "COLUMN" in type2:
            return "column_to_column"
        else:
            return "connected"
    
    def _build_load_paths(self, elements: List[Dict], connections: List[Dict]) -> List[Dict]:
        """Build load paths (which elements transfer loads to which)."""
        load_paths = []
        
        # Group connections by target element
        loads_on = defaultdict(list)
        
        for conn in connections:
            # Beams typically load columns
            if "BEAM" in conn["element1_type"] and "COLUMN" in conn["element2_type"]:
                loads_on[conn["element2_id"]].append({
                    "id": conn["element1_id"],
                    "name": conn["element1_name"],
                    "type": conn["element1_type"]
                })
            elif "BEAM" in conn["element2_type"] and "COLUMN" in conn["element1_type"]:
                loads_on[conn["element1_id"]].append({
                    "id": conn["element2_id"],
                    "name": conn["element2_name"],
                    "type": conn["element2_type"]
                })
        
        # Build load path objects
        for target_id, sources in loads_on.items():
            target_elem = next((e for e in elements if e["id"] == target_id), None)
            if target_elem:
                load_paths.append({
                    "target_id": target_id,
                    "target_name": target_elem["name"],
                    "target_type": target_elem["ifc_type"],
                    "sources": sources
                })
        
        return load_paths


