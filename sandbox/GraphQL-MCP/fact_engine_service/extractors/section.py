"""Extractor for section properties (W14x34, 6x6, etc.)"""
from typing import Dict, Any, Optional
from extractors.base import FactExtractor
from models.fact_result import FactValue, Evidence


class SectionExtractor(FactExtractor):
    """Extracts section properties from Speckle data"""
    
    @property
    def fact_name(self) -> str:
        return "section"
    
    def applies(self, fact_request: str) -> bool:
        return fact_request == "section"
    
    def extract(self, element_json: Dict[str, Any]) -> FactValue:
        """Extract section information"""
        evidence = []
        value = None
        confidence = 0.0
        
        data = element_json.get("data", {})
        
        # Check for Revit section parameters first (most common)
        parameters = data.get("parameters", {})
        if isinstance(parameters, dict):
            # Check for section-related parameters (Revit standard)
            section_params = [
                "STRUCTURAL_SECTION_COMMON_NAME",
                "STRUCTURAL_SECTION_NAME",
                "STRUCTURAL_SECTION_NAME_KEY",
                "SECTION_NAME",
                "PROFILE_NAME"
            ]
            
            for param_key in section_params:
                param = parameters.get(param_key, {})
                if isinstance(param, dict):
                    section_value = param.get("value")
                    if section_value:
                        evidence.append(Evidence(
                            source=f"data.parameters.{param_key}.value",
                            value=section_value,
                            path=f"data.parameters.{param_key}.value"
                        ))
                        value = str(section_value)
                        confidence = 0.9
                        break
        
        # Check for section name/property (fallback)
        if not value:
            section_name = data.get("sectionName", "") or data.get("section", "") or data.get("profile", "")
            if section_name:
                evidence.append(Evidence(
                    source="data.sectionName",
                    value=section_name,
                    path="data.sectionName"
                ))
                value = str(section_name)
                confidence = 0.85
        
        # Check for section properties
        if not value:
            properties = data.get("properties", {})
            if isinstance(properties, dict):
                # Steel sections
                if "shape" in properties:
                    shape = properties.get("shape")
                    if shape:
                        value = str(shape)
                        confidence = 0.85
                        evidence.append(Evidence(
                            source="data.properties.shape",
                            value=shape,
                            path="data.properties.shape"
                        ))
                
                # Timber sections
                if not value and "width" in properties and "height" in properties:
                    width = properties.get("width")
                    height = properties.get("height")
                    if width and height:
                        value = f"{width}x{height}"
                        confidence = 0.8
                        evidence.append(Evidence(
                            source="data.properties.width/height",
                            value=f"{width}x{height}",
                            path="data.properties"
                        ))
        
        # Check for profile reference
        if not value:
            profile = data.get("profile", {})
            if isinstance(profile, dict):
                profile_name = profile.get("name") or profile.get("profileName")
                if profile_name:
                    value = str(profile_name)
                    confidence = 0.75
                    evidence.append(Evidence(
                        source="data.profile.name",
                        value=profile_name,
                        path="data.profile.name"
                    ))
        
        if not value:
            value = "unknown"
            confidence = 0.0
        
        return FactValue(
            value=value,
            confidence=confidence,
            evidence=evidence
        )

