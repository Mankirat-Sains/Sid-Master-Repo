"""Extractor for element orientation (vertical, horizontal, etc.)"""
from typing import Dict, Any, Optional
from extractors.base import FactExtractor
from models.fact_result import FactValue, Evidence
import math


class OrientationExtractor(FactExtractor):
    """Extracts element orientation from Speckle data"""
    
    @property
    def fact_name(self) -> str:
        return "orientation"
    
    def applies(self, fact_request: str) -> bool:
        return fact_request == "orientation"
    
    def extract(self, element_json: Dict[str, Any]) -> FactValue:
        """Extract orientation from geometry or properties"""
        evidence = []
        value = "unknown"
        confidence = 0.0
        
        data = element_json.get("data", {})
        
        # Check for explicit orientation property
        orientation = data.get("orientation", "") or data.get("direction", "")
        if orientation:
            evidence.append(Evidence(
                source="data.orientation",
                value=orientation,
                path="data.orientation"
            ))
            orient_lower = str(orientation).lower()
            if "vertical" in orient_lower or "vert" in orient_lower:
                value = "vertical"
                confidence = 0.9
            elif "horizontal" in orient_lower or "horiz" in orient_lower:
                value = "horizontal"
                confidence = 0.9
            else:
                value = str(orientation)
                confidence = 0.7
        
        # Infer from geometry if available
        if value == "unknown":
            # Check for line/vector that indicates direction
            start = data.get("start", {})
            end = data.get("end", {})
            
            if isinstance(start, dict) and isinstance(end, dict):
                start_z = start.get("z") or start.get("Z") or 0
                end_z = end.get("z") or end.get("Z") or 0
                
                if start_z is not None and end_z is not None:
                    z_diff = abs(end_z - start_z)
                    # If significant Z difference, likely vertical
                    if z_diff > 0.1:  # More than 10cm difference
                        value = "vertical"
                        confidence = 0.8
                        evidence.append(Evidence(
                            source="geometry.z_difference",
                            value=z_diff,
                            path="data.start.z - data.end.z"
                        ))
                    else:
                        value = "horizontal"
                        confidence = 0.8
                        evidence.append(Evidence(
                            source="geometry.z_difference",
                            value=z_diff,
                            path="data.start.z - data.end.z"
                        ))
            
            # Check for normal vector
            normal = data.get("normal", {})
            if isinstance(normal, dict):
                normal_z = normal.get("z") or normal.get("Z")
                if normal_z is not None:
                    if abs(normal_z) > 0.9:  # Mostly vertical
                        value = "vertical"
                        confidence = 0.75
                    elif abs(normal_z) < 0.1:  # Mostly horizontal
                        value = "horizontal"
                        confidence = 0.75
        
        # Infer from element type if still unknown
        if value == "unknown":
            element_type = element_json.get("speckleType", "").lower()
            if "column" in element_type:
                value = "vertical"
                confidence = 0.6
            elif "beam" in element_type or "slab" in element_type:
                value = "horizontal"
                confidence = 0.6
        
        return FactValue(
            value=value,
            confidence=confidence,
            evidence=evidence
        )

