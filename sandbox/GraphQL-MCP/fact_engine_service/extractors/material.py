"""Extractor for material type (timber, steel, concrete, etc.)"""
from typing import Dict, Any, Optional
from extractors.base import FactExtractor
from models.fact_result import FactValue, Evidence


class MaterialExtractor(FactExtractor):
    """Extracts material type from Speckle data"""
    
    @property
    def fact_name(self) -> str:
        return "material"
    
    def applies(self, fact_request: str) -> bool:
        return fact_request == "material"
    
    def coarse_filter_sql(self, filter_op: str, filter_value: Any) -> Optional[str]:
        """Filter by material name in data"""
        if filter_op == "=":
            return f"elem.data->>'material' ILIKE '%{filter_value}%'"
        return None
    
    def extract(self, element_json: Dict[str, Any]) -> FactValue:
        """Extract material type"""
        evidence = []
        value = "unknown"
        confidence = 0.0
        
        data = element_json.get("data", {})
        
        # Check for Revit structural material parameter (most common)
        parameters = data.get("parameters", {})
        if isinstance(parameters, dict):
            # Check STRUCTURAL_MATERIAL_PARAM (Revit standard)
            struct_material = parameters.get("STRUCTURAL_MATERIAL_PARAM", {})
            if isinstance(struct_material, dict):
                material_value = struct_material.get("value")
                if material_value:
                    evidence.append(Evidence(
                        source="data.parameters.STRUCTURAL_MATERIAL_PARAM.value",
                        value=material_value,
                        path="data.parameters.STRUCTURAL_MATERIAL_PARAM.value"
                    ))
                    material_name = str(material_value).lower()
                    
                    # Normalize material types
                    if any(term in material_name for term in ["wood", "timber", "lumber", "glulam", "clt"]):
                        value = "timber"
                        confidence = 0.9
                    elif any(term in material_name for term in ["steel", "metal", "rebar"]):
                        value = "steel"
                        confidence = 0.9
                    elif any(term in material_name for term in ["concrete", "rc", "reinforced"]):
                        value = "concrete"
                        confidence = 0.9
                    elif any(term in material_name for term in ["masonry", "brick", "block"]):
                        value = "masonry"
                        confidence = 0.85
                    elif any(term in material_name for term in ["composite", "steel-concrete"]):
                        value = "composite"
                        confidence = 0.85
        
        # Check for material reference (if not found in parameters)
        if value == "unknown":
            material_ref = data.get("material", {})
            if isinstance(material_ref, dict):
                material_id = material_ref.get("referencedId") or material_ref.get("id")
                if material_id:
                    evidence.append(Evidence(
                        source="data.material.referencedId",
                        value=material_id,
                        path="data.material.referencedId"
                    ))
        
        # Check for material name directly (fallback)
        if value == "unknown":
            material_name = data.get("materialName", "") or data.get("material", "")
            if isinstance(material_name, str) and material_name:
                evidence.append(Evidence(
                    source="data.materialName",
                    value=material_name,
                    path="data.materialName"
                ))
                name_lower = material_name.lower()
                
                # Normalize material types
                if any(term in name_lower for term in ["wood", "timber", "lumber", "glulam", "clt"]):
                    value = "timber"
                    confidence = 0.85
                elif any(term in name_lower for term in ["steel", "metal", "rebar"]):
                    value = "steel"
                    confidence = 0.85
                elif any(term in name_lower for term in ["concrete", "rc", "reinforced"]):
                    value = "concrete"
                    confidence = 0.85
        
        # Check for material properties that indicate type (from parameters)
        if value == "unknown":
            parameters = data.get("parameters", {})
            if isinstance(parameters, dict):
                # Check for material-specific parameters
                param_keys = [k.lower() for k in parameters.keys()]
                if any("wood" in k or "timber" in k or "lumber" in k for k in param_keys):
                    value = "timber"
                    confidence = 0.6
                elif any("steel" in k or "metal" in k for k in param_keys):
                    value = "steel"
                    confidence = 0.6
                elif any("concrete" in k for k in param_keys):
                    value = "concrete"
                    confidence = 0.6
        
        return FactValue(
            value=value,
            confidence=confidence,
            evidence=evidence
        )

