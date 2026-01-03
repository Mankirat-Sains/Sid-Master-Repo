"""Speckle-specific helper utilities"""
from typing import Dict, Any, Optional, List


def get_material_from_reference(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract material information from a material reference.
    
    Args:
        data: Element data containing material reference
    
    Returns:
        Material data dict or None
    """
    material_ref = data.get("material", {})
    if isinstance(material_ref, dict):
        # Check for referenced material
        material_id = material_ref.get("referencedId") or material_ref.get("id")
        if material_id:
            return {
                "id": material_id,
                "name": material_ref.get("name", ""),
                "properties": material_ref.get("properties", {})
            }
    
    return None


def get_level_from_reference(data: Dict[str, Any]) -> Optional[str]:
    """
    Extract level name from a level reference.
    
    Args:
        data: Element data containing level reference
    
    Returns:
        Level name or None
    """
    level_ref = data.get("level", {}) or data.get("levelRef", {})
    if isinstance(level_ref, dict):
        return level_ref.get("name") or level_ref.get("levelName")
    
    # Check direct level property
    level = data.get("level") or data.get("levelName")
    if isinstance(level, str):
        return level
    
    return None


def normalize_speckle_type(speckle_type: str) -> str:
    """
    Normalize Speckle type to common element type.
    
    Args:
        speckle_type: Raw Speckle type string
    
    Returns:
        Normalized type (column, beam, wall, slab, etc.)
    """
    type_lower = speckle_type.lower()
    
    if "column" in type_lower or "pillar" in type_lower:
        return "column"
    elif "beam" in type_lower or "girder" in type_lower:
        return "beam"
    elif "wall" in type_lower:
        return "wall"
    elif "slab" in type_lower or "floor" in type_lower:
        return "slab"
    elif "brace" in type_lower:
        return "brace"
    elif "truss" in type_lower:
        return "truss"
    else:
        return "unknown"


def extract_closure_ids(data: Dict[str, Any]) -> List[str]:
    """
    Extract closure IDs from element data.
    
    Args:
        data: Element data
    
    Returns:
        List of closure IDs
    """
    closure = data.get("__closure", {})
    if isinstance(closure, dict):
        return list(closure.keys())
    elif isinstance(closure, list):
        return closure
    return []


def get_project_id_from_element(element: Dict[str, Any]) -> Optional[str]:
    """
    Extract project ID from element data.
    
    Args:
        element: Element dict with root_id or closure
    
    Returns:
        Project ID or None
    """
    # Check for explicit root_id
    root_id = element.get("root_id")
    if root_id:
        return root_id
    
    # Check closure for project reference
    data = element.get("data", {})
    closure = data.get("__closure", {})
    if isinstance(closure, dict):
        # Look for Project type in closure
        for obj_id in closure.keys():
            # Would need to check object type - simplified here
            return obj_id
    
    return None


