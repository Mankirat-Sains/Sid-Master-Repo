#!/usr/bin/env python3
"""
Element Normalizer
Handles inconsistent data structures from IFC vs Revit elements.
Provides normalized extraction of element type, material, and properties.
"""

import json
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class ElementNormalizer:
    """
    Normalizes element data from different sources (IFC, Revit, etc.)
    to provide consistent access to element type, material, and properties.
    
    Uses recursive search through JSONObject structure to find type and material
    information regardless of where it's stored in the nested JSON.
    """
    
    @staticmethod
    def _recursive_search_for_fields(obj: Any, field_names: List[str], max_depth: int = 10, 
                                     current_depth: int = 0, path: str = "") -> List[tuple]:
        """
        Recursively search through JSON structure for fields matching field_names.
        
        Args:
            obj: The JSON object to search (dict, list, or primitive)
            field_names: List of field names to search for (case-insensitive)
            max_depth: Maximum recursion depth
            current_depth: Current recursion depth
            path: Current path in the JSON structure
            
        Returns:
            List of tuples: (path, value) for each matching field found
        """
        if current_depth >= max_depth:
            return []
        
        results = []
        
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                key_lower = str(key).lower()
                
                # Check if this key matches any field name we're looking for
                for field_name in field_names:
                    if field_name.lower() in key_lower or key_lower in field_name.lower():
                        if value and not isinstance(value, (dict, list)):
                            results.append((current_path, str(value)))
                
                # Recursively search nested structures
                if isinstance(value, (dict, list)):
                    results.extend(ElementNormalizer._recursive_search_for_fields(
                        value, field_names, max_depth, current_depth + 1, current_path
                    ))
        
        elif isinstance(obj, list):
            for idx, item in enumerate(obj):
                current_path = f"{path}[{idx}]" if path else f"[{idx}]"
                if isinstance(item, (dict, list)):
                    results.extend(ElementNormalizer._recursive_search_for_fields(
                        item, field_names, max_depth, current_depth + 1, current_path
                    ))
        
        return results
    
    @staticmethod
    def _is_actual_element(speckle_type: str, data: Dict[str, Any]) -> bool:
        """
        Determine if this is an actual element (not a category group, material definition, etc.).
        
        Prioritizes speckleType to identify actual elements.
        Filters out category groups and material definitions.
        """
        if not speckle_type:
            return False
        
        speckle_type_upper = str(speckle_type).upper()
        
        # Actual element types (BuiltElements, etc.)
        element_indicators = [
            "OBJECTS.BUILTELEMENTS",
            "OBJECTS.GEOMETRY",
            "OBJECTS.STRUCTURAL",
            "OBJECTS.IFC",
            "OBJECTS.DATA.DATAOBJECT"  # IFC objects
        ]
        
        # Non-element types to filter out
        non_element_indicators = [
            "CATEGORY",
            "MATERIAL",
            "DEFINITION",
            "GROUP",
            "COLLECTION"
        ]
        
        # Check if it's a non-element type
        for indicator in non_element_indicators:
            if indicator in speckle_type_upper:
                return False
        
        # Check if it's an actual element type
        for indicator in element_indicators:
            if indicator in speckle_type_upper:
                return True
        
        # Fallback: if speckleType exists and doesn't look like a category/group, assume it's an element
        # But be more conservative - check if it has element-like structure
        if data.get("id") or data.get("applicationId") or data.get("elementId"):
            return True
        
        return False
    
    @staticmethod
    def extract_element_type(element: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract normalized element type from inconsistent data structures.
        
        Uses recursive search to find type information anywhere in the JSONObject.
        Prioritizes speckleType to filter out non-element objects (category groups, etc.).
        
        Returns normalized dict with:
        - type: Normalized type name (e.g., "Column", "Beam", "Wall")
        - source_type: Original type field found
        - source_value: Original value
        - is_structural: Whether element is structural
        """
        speckle_type = str(element.get("speckleType", "")).upper()
        
        # First, check if this is an actual element (not a category group, etc.)
        if not ElementNormalizer._is_actual_element(speckle_type, data):
            return {
                "type": "Unknown",
                "source_type": "filtered_out",
                "source_value": "",
                "is_structural": False,
                "raw": {"speckleType": speckle_type}
            }
        
        # Search for type-related fields recursively
        type_field_names = ["ifcType", "type", "category", "family", "Type", "Family", "OmniClass Title"]
        type_search_results = ElementNormalizer._recursive_search_for_fields(data, type_field_names)
        
        # Also check direct paths (for performance)
        direct_type_fields = {
            "ifcType": data.get("ifcType", ""),
            "type": data.get("type", ""),
            "category": data.get("category", ""),
            "family": data.get("family", ""),
            "name": data.get("name", ""),
        }
        
        # Check parameters
        parameters = data.get("parameters", {})
        if isinstance(parameters, dict):
            direct_type_fields["parameters.Type"] = parameters.get("Type", "")
            direct_type_fields["parameters.Family"] = parameters.get("Family", "")
        
        # Build priority-ordered candidates
        type_candidates = []
        
        # Priority 1: speckleType (most reliable for element identification)
        if speckle_type:
            # Extract element type from speckleType (e.g., "Objects.BuiltElements.Column" -> "Column")
            speckle_parts = speckle_type.split(".")
            if len(speckle_parts) > 0:
                last_part = speckle_parts[-1]
                # Remove common prefixes
                if "COLUMN" in last_part:
                    type_candidates.append(("speckleType", "Column", "high"))
                elif "BEAM" in last_part:
                    type_candidates.append(("speckleType", "Beam", "high"))
                elif "WALL" in last_part:
                    type_candidates.append(("speckleType", "Wall", "high"))
                elif "SLAB" in last_part or "FLOOR" in last_part:
                    type_candidates.append(("speckleType", "Slab", "high"))
                elif "BRACE" in last_part:
                    type_candidates.append(("speckleType", "Bracing", "high"))
        
        # Priority 2: ifcType (specific for IFC)
        if direct_type_fields.get("ifcType"):
            type_candidates.append(("ifcType", direct_type_fields["ifcType"], "high"))
        
        # Priority 3: Recursive search results (found anywhere in JSON)
        for path, value in type_search_results:
            if value and value.strip():
                # Skip if already found via direct path
                if path not in ["ifcType", "type", "category", "family"]:
                    type_candidates.append((path, value, "medium"))
        
        # Priority 4: Direct fields (category, family, type)
        if direct_type_fields.get("category"):
            type_candidates.append(("category", direct_type_fields["category"], "medium"))
        if direct_type_fields.get("family"):
            type_candidates.append(("family", direct_type_fields["family"], "medium"))
        if direct_type_fields.get("type"):
            type_candidates.append(("type", direct_type_fields["type"], "medium"))
        
        # Priority 5: Parameters
        if direct_type_fields.get("parameters.Type"):
            type_candidates.append(("parameters.Type", direct_type_fields["parameters.Type"], "medium"))
        if direct_type_fields.get("parameters.Family"):
            type_candidates.append(("parameters.Family", direct_type_fields["parameters.Family"], "medium"))
        
        # Priority 6: name (fallback)
        if direct_type_fields.get("name"):
            type_candidates.append(("name", direct_type_fields["name"], "low"))
        
        # Determine normalized type from best candidate
        normalized_type = None
        source_type = None
        source_value = None
        
        if type_candidates:
            source_type, source_value, _ = type_candidates[0]
            normalized_type = ElementNormalizer._normalize_type_name(source_value)
        
        # Determine if structural
        all_type_values = [v for _, v, _ in type_candidates] + [speckle_type]
        is_structural = ElementNormalizer._is_structural(
            direct_type_fields.get("ifcType", ""),
            direct_type_fields.get("category", ""),
            direct_type_fields.get("family", ""),
            direct_type_fields.get("name", ""),
            speckle_type,
            direct_type_fields.get("parameters.Type", "")
        )
        
        return {
            "type": normalized_type or "Unknown",
            "source_type": source_type or "unknown",
            "source_value": source_value or "",
            "is_structural": is_structural,
            "raw": {
                "ifcType": direct_type_fields.get("ifcType", ""),
                "category": direct_type_fields.get("category", ""),
                "family": direct_type_fields.get("family", ""),
                "name": direct_type_fields.get("name", ""),
                "speckleType": speckle_type,
                "parameters": {
                    "Type": direct_type_fields.get("parameters.Type", ""),
                    "Family": direct_type_fields.get("parameters.Family", "")
                }
            }
        }
    
    @staticmethod
    def extract_material(element: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract normalized material from inconsistent data structures.
        
        Uses recursive search to find material information anywhere in the JSONObject.
        Checks IFC properties, Revit parameters, family/type names, and string parsing.
        
        Returns normalized dict with:
        - material: Normalized material name (e.g., "Timber", "Steel", "Concrete")
        - source: Where material was found
        - confidence: How confident we are (high/medium/low)
        """
        # Search for material-related fields recursively
        material_field_names = [
            "Material", "Structural Material", "material", "structuralMaterial",
            "Material Name", "MaterialType", "Assembly Description"
        ]
        material_search_results = ElementNormalizer._recursive_search_for_fields(data, material_field_names)
        
        # Also check direct paths (for performance)
        # IFC-style extraction
        props = data.get("properties", {})
        ifc_material = None
        
        # Try Attributes first
        if isinstance(props, dict):
            attrs = props.get("Attributes", {})
            if isinstance(attrs, dict) and attrs.get("Material"):
                ifc_material = attrs["Material"]
            
            # Try Property Sets
            if not ifc_material:
                prop_sets = props.get("Property Sets", {})
                if isinstance(prop_sets, dict):
                    for pset_data in prop_sets.values():
                        if isinstance(pset_data, dict) and pset_data.get("Material"):
                            ifc_material = pset_data["Material"]
                            break
        
        # Revit-style extraction
        family = data.get("family", "")
        type_field = data.get("type", "")
        name = data.get("name", "")
        
        # Check parameters section
        parameters = data.get("parameters", {})
        param_material = None
        if isinstance(parameters, dict):
            param_material = parameters.get("Material", "")
            if not param_material:
                param_material = parameters.get("Structural Material", "")
            if not param_material:
                # Sometimes material is in Assembly Description
                assembly_desc = parameters.get("Assembly Description", "")
                if assembly_desc:
                    param_material = assembly_desc
        
        # Build priority-ordered candidates
        material_candidates = []
        
        # Priority 1: Explicit material fields from recursive search (highest confidence)
        for path, value in material_search_results:
            if value and value.strip():
                # Skip if it's a path we already checked directly
                if "parameters.Material" not in path and "properties.Attributes.Material" not in path:
                    material_candidates.append((path, value, "high"))
        
        # Priority 2: IFC material (from properties)
        if ifc_material:
            material_candidates.append(("ifc_properties", ifc_material, "high"))
        
        # Priority 3: Parameters.Material or Parameters.Structural Material
        if param_material:
            material_candidates.append(("parameters.Material", param_material, "high"))
        
        # Priority 4: Family name (often contains material, e.g., "Timber-Column")
        if family:
            parsed = ElementNormalizer._parse_material_from_string(family)
            if parsed:
                material_candidates.append(("family", parsed, "medium"))
            # Also check if family itself is a material indicator
            family_normalized = ElementNormalizer._normalize_material_name(family)
            if family_normalized != "Unknown" and family_normalized != family:
                material_candidates.append(("family", family_normalized, "medium"))
        
        # Priority 5: Type field (e.g., "6x8 (P.T.) SPF. #2 OR BETTER" -> "Timber")
        if type_field:
            parsed = ElementNormalizer._parse_material_from_string(type_field)
            if parsed:
                material_candidates.append(("type", parsed, "medium"))
            # Also check if type itself contains material info
            type_normalized = ElementNormalizer._normalize_material_name(type_field)
            if type_normalized != "Unknown" and type_normalized != type_field:
                material_candidates.append(("type", type_normalized, "medium"))
        
        # Priority 6: Name field (lower confidence)
        if name:
            parsed = ElementNormalizer._parse_material_from_string(name)
            if parsed:
                material_candidates.append(("name", parsed, "low"))
        
        # Get best candidate (first one with highest confidence)
        material = None
        source = None
        confidence = "low"
        
        if material_candidates:
            source, material, confidence = material_candidates[0]
        
        # Normalize material name
        normalized_material = ElementNormalizer._normalize_material_name(material) if material else "Unknown"
        
        return {
            "material": normalized_material,
            "source": source or "unknown",
            "confidence": confidence,
            "raw": {
                "ifc_material": ifc_material,
                "family": family,
                "type": type_field,
                "name": name,
                "parameters": {
                    "Material": param_material,
                    "Assembly Description": parameters.get("Assembly Description", "") if isinstance(parameters, dict) else ""
                },
                "recursive_search_results": material_search_results
            }
        }
    
    @staticmethod
    def _normalize_type_name(type_str: str) -> Optional[str]:
        """Normalize type string to common element type names."""
        if not type_str:
            return None
        
        type_upper = str(type_str).upper()
        
        # Column types
        if any(kw in type_upper for kw in ["COLUMN", "POST", "PILAR"]):
            return "Column"
        
        # Beam types
        if any(kw in type_upper for kw in ["BEAM", "GIRDER", "JOIST", "RAFTER"]):
            return "Beam"
        
        # Wall types
        if any(kw in type_upper for kw in ["WALL", "PARTITION"]):
            return "Wall"
        
        # Slab/Floor types
        if any(kw in type_upper for kw in ["SLAB", "FLOOR", "DECK"]):
            return "Slab"
        
        # Roof types
        if any(kw in type_upper for kw in ["ROOF", "CEILING"]):
            return "Roof"
        
        # Bracing
        if any(kw in type_upper for kw in ["BRACE", "BRACING"]):
            return "Bracing"
        
        # Plate
        if any(kw in type_upper for kw in ["PLATE", "PANEL"]):
            return "Plate"
        
        # Member (generic structural)
        if any(kw in type_upper for kw in ["MEMBER", "STRUCTURAL"]):
            return "Member"
        
        # Return original if no match
        return type_str
    
    @staticmethod
    def _normalize_material_name(material_str: str) -> str:
        """Normalize material string to common material names."""
        if not material_str:
            return "Unknown"
        
        material_lower = str(material_str).lower()
        
        # Timber/Wood
        if any(kw in material_lower for kw in ["timber", "wood", "lumber", "spf", "pine", "fir", "cedar", "oak"]):
            return "Timber"
        
        # Steel
        if any(kw in material_lower for kw in ["steel", "metal", "iron", "w-shape", "i-beam"]):
            return "Steel"
        
        # Concrete
        if any(kw in material_lower for kw in ["concrete", "rebar", "reinforced"]):
            return "Concrete"
        
        # Masonry
        if any(kw in material_lower for kw in ["brick", "masonry", "block", "cmu"]):
            return "Masonry"
        
        # Return original if no match
        return material_str
    
    @staticmethod
    def _parse_material_from_string(text: str) -> Optional[str]:
        """Extract material keyword from string (e.g., 'Timber-Column' -> 'Timber')."""
        if not text:
            return None
        
        text_lower = text.lower()
        
        # Check for material keywords
        materials = ["timber", "wood", "steel", "concrete", "masonry", "brick", "metal"]
        for material in materials:
            if material in text_lower:
                return material
        
        return None
    
    @staticmethod
    def _is_structural(ifc_type: str, category: str, family: str, name: str, 
                       speckle_type: str, param_type: str) -> bool:
        """Determine if element is structural."""
        all_fields = " ".join([
            str(ifc_type).upper(),
            str(category).upper(),
            str(family).upper(),
            str(name).upper(),
            str(speckle_type).upper(),
            str(param_type).upper()
        ])
        
        structural_keywords = [
            "STRUCTURAL", "COLUMN", "BEAM", "BRACE", "FRAMING",
            "MEMBER", "WALL", "SLAB", "FLOOR", "FOUNDATION"
        ]
        
        return any(kw in all_fields for kw in structural_keywords)
    
    @staticmethod
    def normalize_element(element: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize a complete element, extracting type, material, and basic info.
        
        Args:
            element: Element dict with 'id', 'data', 'speckleType' fields
            
        Returns:
            Normalized element dict
        """
        try:
            # Parse data field
            data_str = element.get("data")
            if not data_str:
                return None
            
            if isinstance(data_str, str):
                try:
                    data = json.loads(data_str)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse data for element {element.get('id')}")
                    return None
            else:
                data = data_str
            
            if not isinstance(data, dict):
                return None
            
            # Extract normalized type and material
            type_info = ElementNormalizer.extract_element_type(element, data)
            material_info = ElementNormalizer.extract_material(element, data)
            
            return {
                "id": element.get("id"),
                "element_id": data.get("id") or element.get("id"),
                "name": data.get("name", "Unnamed"),
                "element_type": type_info,
                "material": material_info,
                "speckle_type": element.get("speckleType", ""),
                "application_id": data.get("applicationId", ""),
            }
        
        except Exception as e:
            logger.warning(f"Error normalizing element {element.get('id')}: {e}")
            return None


