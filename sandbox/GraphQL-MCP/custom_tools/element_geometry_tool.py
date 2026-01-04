#!/usr/bin/env python3
"""
Tool: Get Element Geometry
Extracts geometry, dimensions, elevations, and spatial relationships from IFC elements
"""

import json
import logging
from typing import Dict, Any, Optional, List
from custom_tools.base_tool import BaseTool, ToolDefinition

logger = logging.getLogger(__name__)


class ElementGeometryTool(BaseTool):
    """
    Extract geometry data from elements.
    
    Returns:
    - Coordinates (x, y, z)
    - Dimensions (length, width, height)
    - Elevations
    - Bounding box
    - Span information (for linear elements)
    """
    
    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="get_element_geometry",
            description="""Extract geometry, dimensions, elevations, and spatial data from IFC elements.
            
This tool extracts:
- Coordinates (x, y, z) from element geometry
- Dimensions (length, width, height, span)
- Elevations (z coordinates)
- Bounding boxes
- Spacing between parallel elements

Use this when users ask about:
- Building dimensions or size
- Member spans
- Elevations
- Spacing between members
- Element positions or coordinates""",
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
                "element_ids": {
                    "type": "array",
                    "description": "Optional: Specific element IDs to analyze. If not provided, analyzes all elements.",
                    "items": {"type": "string"},
                    "required": False
                },
                "element_type": {
                    "type": "string",
                    "description": "Optional: Filter by IFC type (e.g., 'IfcBeam', 'IfcColumn', 'IfcWall')",
                    "required": False
                },
                "level": {
                    "type": "string",
                    "description": "Optional: Filter by level/elevation (e.g., 'Level 1', 'Ground Floor')",
                    "required": False
                }
            },
            handler=self.execute
        )
    
    def execute(
        self,
        project_id: str,
        model_id: Optional[str] = None,
        element_ids: Optional[List[str]] = None,
        element_type: Optional[str] = None,
        level: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract geometry from elements."""
        if not self.graphql_client:
            return {
                "isError": True,
                "content": [{"type": "text", "text": "GraphQL client not available"}]
            }
        
        try:
            # Get project data (same pattern as building_perimeter_tool)
            version_result = self._get_project_version(project_id, model_id)
            if version_result.get("isError"):
                return version_result
            
            root_object_id = version_result["root_object_id"]
            
            # Get all objects
            objects_result = self._get_all_objects(project_id, root_object_id)
            if objects_result.get("isError"):
                return objects_result
            
            elements = objects_result["elements"]
            
            # Extract geometry for each element
            geometry_data = []
            
            for element in elements:
                try:
                    data_str = element.get("data")
                    if not data_str:
                        logger.debug(f"Element {element.get('id')} has no data field")
                        continue
                    
                    # Parse JSONObject - it might be a string or already a dict
                    try:
                        if isinstance(data_str, str):
                            data = json.loads(data_str)
                        else:
                            data = data_str
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse data for element {element.get('id')}: {e}")
                        continue
                    
                    if not isinstance(data, dict):
                        logger.debug(f"Element {element.get('id')} data is not a dict: {type(data)}")
                        continue
                    
                    # Filter by element type if specified
                    # Check both IFC type and Revit category/type
                    ifc_type = data.get("ifcType", "").upper()
                    category = str(data.get("category", "")).upper()
                    element_name = str(data.get("name", "")).upper()
                    speckle_type = str(element.get("speckleType", "")).upper()
                    
                    # Determine element type from various sources
                    detected_type = ifc_type or category or element_name or speckle_type
                    
                    if element_type:
                        # Check if element_type matches any of the type indicators
                        element_type_upper = element_type.upper()
                        if (element_type_upper not in ifc_type and 
                            element_type_upper not in category and
                            element_type_upper not in element_name and
                            element_type_upper not in speckle_type):
                            continue
                    
                    # Filter by element IDs if specified
                    element_id = data.get("id") or element.get("id")
                    if element_ids and element_id not in element_ids:
                        continue
                    
                    # Extract geometry
                    geom = self._extract_geometry(data)
                    if geom:
                        geom["element_id"] = element_id
                        geom["element_name"] = data.get("name", "Unnamed")
                        geom["ifc_type"] = data.get("ifcType", "")
                        geom["category"] = data.get("category", "")
                        geom["speckle_type"] = element.get("speckleType", "")
                        geometry_data.append(geom)
                    else:
                        logger.debug(f"No geometry extracted for element {element_id} ({data.get('name', 'Unnamed')}) - type: {detected_type}")
                
                except Exception as e:
                    logger.warning(f"Error processing element {element.get('id')}: {e}", exc_info=True)
                    continue
            
            # Calculate spacing between parallel elements
            spacing_data = self._calculate_spacing(geometry_data, element_type)
            
            # Calculate building dimensions
            building_dims = self._calculate_building_dimensions(geometry_data)
            
            result_text = f"Geometry Analysis Results\n"
            result_text += f"Elements Analyzed: {len(geometry_data)}\n\n"
            
            if building_dims:
                result_text += f"Building Dimensions:\n"
                result_text += f"  Width (X): {building_dims.get('width', 0):.2f} units\n"
                result_text += f"  Length (Y): {building_dims.get('length', 0):.2f} units\n"
                result_text += f"  Height (Z): {building_dims.get('height', 0):.2f} units\n\n"
            
            if spacing_data:
                result_text += f"Member Spacing Analysis:\n"
                for spacing in spacing_data[:10]:  # Show first 10
                    result_text += f"  {spacing['description']}\n"
                result_text += "\n"
            
            # Show spans for beams
            beam_spans = [g for g in geometry_data if "BEAM" in g.get("ifc_type", "").upper()]
            if beam_spans:
                result_text += f"Beam Spans:\n"
                for beam in beam_spans[:10]:
                    if beam.get("span"):
                        result_text += f"  {beam['element_name']}: {beam['span']:.2f} units\n"
            
            return {
                "isError": False,
                "content": [{"type": "text", "text": result_text}],
                "data": {
                    "elements": geometry_data,
                    "building_dimensions": building_dims,
                    "spacing": spacing_data
                }
            }
        
        except Exception as e:
            logger.error(f"Element geometry tool failed: {e}", exc_info=True)
            return {
                "isError": True,
                "content": [{"type": "text", "text": f"Error: {str(e)}"}]
            }
    
    def _get_project_version(self, project_id: str, model_id: Optional[str] = None):
        """Get project version and root object ID."""
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
                logger.error(f"Project {project_id} not found. Response: {result}")
                return {"isError": True, "content": [{"type": "text", "text": f"Project {project_id} not found"}]}
            
            versions = project_data.get("versions", {}).get("items", [])
        
        if not versions:
            logger.warning(f"No versions found for project {project_id}" + (f" model {model_id}" if model_id else ""))
            return {"isError": True, "content": [{"type": "text", "text": f"No versions found for project {project_id}" + (f" model {model_id}" if model_id else "") + ". Project may not have any commits/versions yet."}]}
        
        root_object_id = versions[0].get("referencedObject")
        if not root_object_id:
            logger.error(f"No referencedObject in version. Version data: {versions[0]}")
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
            logger.error(f"GraphQL errors getting objects: {result['errors']}")
            return {"isError": True, "content": [{"type": "text", "text": str(result["errors"])}]}
        
        object_data = result.get("data", {}).get("project", {}).get("object", {})
        if not object_data:
            logger.error(f"No object data returned. Full response: {result}")
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
        
        # Add children
        elements.extend(children)
        
        logger.info(f"Total elements to process: {len(elements)}")
        
        return {"elements": elements}
    
    def _extract_geometry(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract geometry coordinates from element data (supports both IFC and Revit)."""
        all_coords = []
        
        # Method 1: IFC elements - geometry in referencedObjects
        ref_objects = data.get("referencedObjects", {})
        for ref_id, ref_obj in ref_objects.items():
            ref_data = ref_obj.get("data", {})
            coords = ref_data.get("data", [])
            
            if coords and isinstance(coords, list) and len(coords) >= 3:
                all_coords.extend(coords)
        
        # Method 2: Revit elements - check for direct geometry fields
        if not all_coords:
            # Check for basePoint, startPoint, endPoint
            if "basePoint" in data:
                bp = data["basePoint"]
                if isinstance(bp, (list, tuple)) and len(bp) >= 3:
                    all_coords.extend([bp[0], bp[1], bp[2]])
            
            if "startPoint" in data:
                sp = data["startPoint"]
                if isinstance(sp, (list, tuple)) and len(sp) >= 3:
                    all_coords.extend([sp[0], sp[1], sp[2]])
            
            if "endPoint" in data:
                ep = data["endPoint"]
                if isinstance(ep, (list, tuple)) and len(ep) >= 3:
                    all_coords.extend([ep[0], ep[1], ep[2]])
            
            # Check for vertices array
            if "vertices" in data:
                vertices = data["vertices"]
                if isinstance(vertices, list):
                    for v in vertices:
                        if isinstance(v, (list, tuple)) and len(v) >= 3:
                            all_coords.extend([v[0], v[1], v[2]])
                        elif isinstance(v, dict):
                            # Might be {x, y, z} or {referencedId}
                            if "x" in v and "y" in v and "z" in v:
                                all_coords.extend([v["x"], v["y"], v["z"]])
        
        # Method 3: Check displayValue references (would need to resolve, but check structure)
        if not all_coords and "displayValue" in data:
            display_value = data["displayValue"]
            if isinstance(display_value, list):
                # These are references that would need to be resolved
                # For now, we'll note that geometry exists but needs resolution
                logger.debug("Element has displayValue references (geometry needs resolution)")
        
        if not all_coords:
            return None
        
        # Extract x, y, z coordinates
        x_coords = [all_coords[i] for i in range(0, len(all_coords), 3) if i < len(all_coords)]
        y_coords = [all_coords[i+1] for i in range(0, len(all_coords), 3) if i+1 < len(all_coords)]
        z_coords = [all_coords[i+2] for i in range(0, len(all_coords), 3) if i+2 < len(all_coords)]
        
        if not x_coords or not y_coords or not z_coords:
            return None
        
        # Calculate dimensions
        min_x, max_x = min(x_coords), max(x_coords)
        min_y, max_y = min(y_coords), max(y_coords)
        min_z, max_z = min(z_coords), max(z_coords)
        
        # Calculate span (for linear elements like beams)
        span = ((max_x - min_x)**2 + (max_y - min_y)**2 + (max_z - min_z)**2)**0.5
        
        return {
            "coordinates": {
                "x": {"min": min_x, "max": max_x, "range": max_x - min_x},
                "y": {"min": min_y, "max": max_y, "range": max_y - min_y},
                "z": {"min": min_z, "max": max_z, "range": max_z - min_z},
            },
            "elevation": min_z,  # Typically the base elevation
            "span": span,
            "bounding_box": {
                "width": max_x - min_x,
                "length": max_y - min_y,
                "height": max_z - min_z
            }
        }
    
    def _calculate_spacing(self, geometry_data: List[Dict], element_type: Optional[str] = None) -> List[Dict]:
        """Calculate spacing between parallel elements."""
        # Filter by type if specified
        filtered = [g for g in geometry_data if not element_type or element_type.upper() in g.get("ifc_type", "").upper()]
        
        if len(filtered) < 2:
            return []
        
        spacing_info = []
        
        # Group by similar elevation (same level)
        from collections import defaultdict
        by_elevation = defaultdict(list)
        for geom in filtered:
            elev = round(geom.get("elevation", 0), 2)  # Round to group similar elevations
            by_elevation[elev].append(geom)
        
        # Calculate spacing for elements on same level
        for elevation, elements in by_elevation.items():
            if len(elements) < 2:
                continue
            
            # Sort by x or y coordinate
            elements_sorted = sorted(elements, key=lambda e: e["coordinates"]["x"]["min"])
            
            for i in range(len(elements_sorted) - 1):
                elem1 = elements_sorted[i]
                elem2 = elements_sorted[i + 1]
                
                spacing = elem2["coordinates"]["x"]["min"] - elem1["coordinates"]["x"]["max"]
                
                if spacing > 0:
                    spacing_info.append({
                        "element1": elem1["element_name"],
                        "element2": elem2["element_name"],
                        "spacing": spacing,
                        "elevation": elevation,
                        "description": f"{elem1['element_name']} to {elem2['element_name']}: {spacing:.2f} units at elevation {elevation}"
                    })
        
        return sorted(spacing_info, key=lambda x: x["spacing"])
    
    def _calculate_building_dimensions(self, geometry_data: List[Dict]) -> Optional[Dict]:
        """Calculate overall building dimensions."""
        if not geometry_data:
            return None
        
        all_x = []
        all_y = []
        all_z = []
        
        for geom in geometry_data:
            coords = geom.get("coordinates", {})
            all_x.extend([coords["x"]["min"], coords["x"]["max"]])
            all_y.extend([coords["y"]["min"], coords["y"]["max"]])
            all_z.extend([coords["z"]["min"], coords["z"]["max"]])
        
        if not all_x or not all_y or not all_z:
            return None
        
        return {
            "width": max(all_x) - min(all_x),
            "length": max(all_y) - min(all_y),
            "height": max(all_z) - min(all_z),
            "min_x": min(all_x),
            "max_x": max(all_x),
            "min_y": min(all_y),
            "max_y": max(all_y),
            "min_z": min(all_z),
            "max_z": max(all_z)
        }


