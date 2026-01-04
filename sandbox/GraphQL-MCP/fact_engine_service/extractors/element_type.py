"""Extractor for element type (column, beam, wall, slab, etc.)"""
from typing import Dict, Any, Optional
from extractors.base import FactExtractor
from models.fact_result import FactValue, Evidence


class ElementTypeExtractor(FactExtractor):
    """Extracts element type from Speckle data"""
    
    @property
    def fact_name(self) -> str:
        return "element_type"
    
    def applies(self, fact_request: str) -> bool:
        return fact_request == "element_type"
    
    def coarse_filter_sql(self, filter_op: str, filter_value: Any) -> Optional[str]:
        """Filter by Speckle type"""
        if filter_op == "=":
            return f"elem.\"speckleType\" ILIKE '%{filter_value}%'"
        return None
    
    def extract(self, element_json: Dict[str, Any]) -> FactValue:
        """Extract element type"""
        evidence = []
        value = "unknown"
        confidence = 0.0
        
        # Check speckleType first
        speckle_type = element_json.get("speckleType", "")
        if speckle_type:
            evidence.append(Evidence(
                source="speckleType",
                value=speckle_type,
                path="speckleType"
            ))
        
        # Normalize to common types
        type_lower = speckle_type.lower()
        if "column" in type_lower or "pillar" in type_lower:
            value = "column"
            confidence = 0.9
        elif "beam" in type_lower or "girder" in type_lower:
            value = "beam"
            confidence = 0.9
        elif "wall" in type_lower:
            value = "wall"
            confidence = 0.9
        elif "slab" in type_lower or "floor" in type_lower or "deck" in type_lower:
            value = "slab"
            confidence = 0.9
        elif "brace" in type_lower:
            value = "brace"
            confidence = 0.85
        elif "truss" in type_lower:
            value = "truss"
            confidence = 0.85
        elif "plate" in type_lower:
            value = "plate"
            confidence = 0.8
        else:
            # Try to infer from data structure
            if element_json.get("data"):
                data = element_json.get("data", {})
                category = data.get("category", "")
                if category:
                    evidence.append(Evidence(
                        source="data.category",
                        value=category,
                        path="data.category"
                    ))
                    if "column" in category.lower():
                        value = "column"
                        confidence = 0.7
                    elif "beam" in category.lower():
                        value = "beam"
                        confidence = 0.7
        
        if value == "unknown" and speckle_type:
            # Fallback: use first part of speckleType
            parts = speckle_type.split(".")
            if parts:
                value = parts[-1].lower()
                confidence = 0.5
        
        return FactValue(
            value=value,
            confidence=confidence,
            evidence=evidence
        )

