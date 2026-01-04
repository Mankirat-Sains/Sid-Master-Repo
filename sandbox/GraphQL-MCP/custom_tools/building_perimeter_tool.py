#!/usr/bin/env python3
"""
Tool: Get Building Perimeter from Beams
Finds all beams in a project and calculates building perimeter dimensions
"""

import json
import logging
from typing import Dict, Any, Optional
from custom_tools.base_tool import BaseTool, ToolDefinition

logger = logging.getLogger(__name__)


class BuildingPerimeterTool(BaseTool):
    """
    Tool to calculate building perimeter from beam geometry.
    
    This tool:
    1. Queries for all beams in a project
    2. Extracts geometry coordinates
    3. Calculates min/max x,y to determine building footprint
    4. Returns width, length, perimeter, and area
    """
    
    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="get_building_perimeter",
            description="""Calculate building perimeter dimensions from beams/members in a project.
            
This tool finds all IFC beams in a project, extracts their geometry coordinates,
and calculates the building footprint (width, length, perimeter, area).

Use this when users ask about:
- Building width, length, or dimensions
- Building perimeter
- Building footprint
- Which project has a width/length greater than X
- Building area or size""",
            parameters={
                "project_id": {
                    "type": "string",
                    "description": "The project ID to analyze",
                    "required": True
                },
                "unit": {
                    "type": "string",
                    "description": "Unit for dimensions (e.g., 'feet', 'meters', 'inches'). Default: 'feet'",
                    "required": False,
                    "default": "feet"
                }
            },
            handler=self.execute
        )
    
    def execute(self, project_id: str, unit: str = "feet") -> Dict[str, Any]:
        """
        Execute the building perimeter calculation.
        
        Args:
            project_id: Project ID to analyze
            unit: Unit for output (feet, meters, etc.)
            
        Returns:
            Dict with building dimensions
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
            
            # Step 2: Get all objects with data
            objects_query = """
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
            
            # Step 3: Extract coordinates from ALL exterior elements (not just beams)
            all_x_coords = []
            all_y_coords = []
            element_count = 0
            elements_processed = []
            
            # Also check root object if it has data
            objects_to_process = list(children)
            root_obj = objects_result.get("data", {}).get("project", {}).get("object", {})
            if root_obj.get("data"):
                objects_to_process.insert(0, {
                    "id": root_obj.get("id"),
                    "data": root_obj.get("data"),
                    "is_root": True
                })
            
            for obj in objects_to_process:
                try:
                    data_str = obj.get("data")
                    if not data_str:
                        continue
                    
                    # Parse JSONObject
                    if isinstance(data_str, str):
                        data = json.loads(data_str)
                    else:
                        data = data_str
                    
                    if not isinstance(data, dict):
                        continue
                    
                    # Get element type from various sources (IFC or Revit)
                    ifc_type = data.get("ifcType", "").upper()
                    category = str(data.get("category", "")).upper()
                    element_name = str(data.get("name", "")).upper()
                    speckle_type = str(obj.get("speckleType", "")).upper()
                    
                    # Include ALL structural/exterior elements (IFC and Revit)
                    # IFC types
                    is_structural_element = any([
                        "BEAM" in ifc_type,
                        "COLUMN" in ifc_type,
                        "WALL" in ifc_type,
                        "SLAB" in ifc_type,
                        "MEMBER" in ifc_type,
                        "PLATE" in ifc_type,
                        "BRACING" in ifc_type,
                        "FRAMING" in ifc_type,
                        # Revit categories
                        "BEAM" in category or "BEAM" in element_name or "BEAM" in speckle_type,
                        "COLUMN" in category or "COLUMN" in element_name or "COLUMN" in speckle_type,
                        "WALL" in category or "WALL" in element_name or "WALL" in speckle_type,
                        "FLOOR" in category or "SLAB" in category or "SLAB" in element_name,
                        "FRAMING" in category or "FRAMING" in element_name,
                        "STRUCTURAL" in category or "STRUCTURAL" in element_name,
                        # Revit element types
                        "REVITELEMENT" in speckle_type and any(kw in element_name for kw in ["beam", "column", "wall", "frame"])
                    ])
                    
                    if not is_structural_element:
                        continue
                    
                    element_count += 1
                    elements_processed.append({
                        "name": data.get("name", "Unnamed"),
                        "type": ifc_type
                    })
                    
                    # Extract geometry from multiple sources
                    # Method 1: IFC - referencedObjects
                    ref_objects = data.get("referencedObjects", {})
                    for ref_id, ref_obj in ref_objects.items():
                        ref_data = ref_obj.get("data", {})
                        coords = ref_data.get("data", [])
                        
                        if coords and isinstance(coords, list) and len(coords) >= 3:
                            # Extract x, y coordinates (every 3rd value: x, y, z, x, y, z, ...)
                            for i in range(0, len(coords), 3):
                                if i + 1 < len(coords):
                                    all_x_coords.append(coords[i])
                                    all_y_coords.append(coords[i + 1])
                    
                    # Method 2: Revit - direct geometry fields
                    if not all_x_coords:
                        # Check basePoint, startPoint, endPoint
                        for point_field in ["basePoint", "startPoint", "endPoint"]:
                            if point_field in data:
                                point = data[point_field]
                                if isinstance(point, (list, tuple)) and len(point) >= 2:
                                    all_x_coords.append(point[0])
                                    all_y_coords.append(point[1] if len(point) > 1 else 0)
                        
                        # Check vertices
                        if "vertices" in data:
                            vertices = data["vertices"]
                            if isinstance(vertices, list):
                                for v in vertices:
                                    if isinstance(v, (list, tuple)) and len(v) >= 2:
                                        all_x_coords.append(v[0])
                                        all_y_coords.append(v[1] if len(v) > 1 else 0)
                                    elif isinstance(v, dict) and "x" in v and "y" in v:
                                        all_x_coords.append(v["x"])
                                        all_y_coords.append(v["y"])
                
                except Exception as e:
                    logger.warning(f"Error processing object {obj.get('id')}: {e}")
                    continue
            
            # Step 4: Calculate dimensions
            if not all_x_coords or not all_y_coords:
                return {
                    "isError": False,
                    "content": [{
                        "type": "text",
                        "text": f"No geometry coordinates found in {element_count} element(s) for project {project_name}. "
                               f"Total children objects: {len(children)}. "
                               f"Elements processed: {[e['name'] for e in elements_processed[:10]]}"
                    }]
                }
            
            min_x = min(all_x_coords)
            max_x = max(all_x_coords)
            min_y = min(all_y_coords)
            max_y = max(all_y_coords)
            
            width = max_x - min_x
            length = max_y - min_y
            perimeter = 2 * (width + length)
            area = width * length
            
            # Convert units if needed (assuming input is in meters)
            unit_conversion = {
                "feet": 3.28084,
                "meters": 1.0,
                "inches": 39.3701,
                "yards": 1.09361
            }
            
            conversion_factor = unit_conversion.get(unit.lower(), 1.0)
            
            result = {
                "project_id": project_id,
                "project_name": project_name,
                "element_count": element_count,
                "elements_processed": elements_processed,
                "coordinates_found": len(all_x_coords),
                "dimensions": {
                    "min_x": min_x * conversion_factor,
                    "max_x": max_x * conversion_factor,
                    "min_y": min_y * conversion_factor,
                    "max_y": max_y * conversion_factor,
                    "width": width * conversion_factor,
                    "length": length * conversion_factor,
                    "perimeter": perimeter * conversion_factor,
                    "area": area * (conversion_factor ** 2)
                },
                "unit": unit
            }
            
            result_text = f"""Building Perimeter Analysis for: {project_name}

Exterior Elements Analyzed: {element_count}
Coordinates Extracted: {len(all_x_coords)}

Element Types Found:
"""
            # Count element types
            from collections import Counter
            type_counts = Counter([e["type"] for e in elements_processed])
            for elem_type, count in type_counts.most_common(10):
                result_text += f"  - {elem_type}: {count}\n"
            
            result_text += f"""
Dimensions ({unit}):
  Width: {result['dimensions']['width']:.2f} {unit}
  Length: {result['dimensions']['length']:.2f} {unit}
  Perimeter: {result['dimensions']['perimeter']:.2f} {unit}
  Area: {result['dimensions']['area']:.2f} {unit}²

Bounds:
  X: {result['dimensions']['min_x']:.2f} to {result['dimensions']['max_x']:.2f} {unit}
  Y: {result['dimensions']['min_y']:.2f} to {result['dimensions']['max_y']:.2f} {unit}
"""
            
            return {
                "isError": False,
                "content": [
                    {
                        "type": "text",
                        "text": result_text
                    }
                ],
                "data": result  # Include structured data for programmatic use
            }
        
        except Exception as e:
            logger.error(f"Building perimeter tool failed: {e}", exc_info=True)
            return {
                "isError": True,
                "content": [{"type": "text", "text": f"Error calculating building perimeter: {str(e)}"}]
            }


