"""Extractor for level/floor information"""
from typing import Dict, Any, Optional
from extractors.base import FactExtractor
from models.fact_result import FactValue, Evidence


class LevelExtractor(FactExtractor):
    """Extracts level/floor information from Speckle data"""
    
    @property
    def fact_name(self) -> str:
        return "level"
    
    def applies(self, fact_request: str) -> bool:
        return fact_request == "level"
    
    def extract(self, element_json: Dict[str, Any]) -> FactValue:
        """Extract level information"""
        evidence = []
        value = None
        confidence = 0.0
        
        data = element_json.get("data", {})
        
        # Check for level name
        level_name = data.get("level", "") or data.get("levelName", "") or data.get("floor", "")
        if level_name:
            evidence.append(Evidence(
                source="data.level",
                value=level_name,
                path="data.level"
            ))
            value = str(level_name)
            confidence = 0.9
        
        # Check for elevation (can infer level from elevation)
        if not value:
            elevation = data.get("elevation") or data.get("z")
            if elevation is not None:
                evidence.append(Evidence(
                    source="data.elevation",
                    value=elevation,
                    path="data.elevation"
                ))
                # Infer level from elevation (assuming 3m per floor)
                if isinstance(elevation, (int, float)):
                    inferred_level = int(elevation / 3.0) + 1
                    value = f"Level {inferred_level}"
                    confidence = 0.6
        
        # Check for level reference
        if not value:
            level_ref = data.get("levelRef", {})
            if isinstance(level_ref, dict):
                level_id = level_ref.get("referencedId") or level_ref.get("id")
                level_name = level_ref.get("name")
                if level_name:
                    value = str(level_name)
                    confidence = 0.8
                    evidence.append(Evidence(
                        source="data.levelRef.name",
                        value=level_name,
                        path="data.levelRef.name"
                    ))
                elif level_id:
                    value = f"Level (ID: {level_id})"
                    confidence = 0.5
                    evidence.append(Evidence(
                        source="data.levelRef.referencedId",
                        value=level_id,
                        path="data.levelRef.referencedId"
                    ))
        
        if not value:
            value = "unknown"
            confidence = 0.0
        
        return FactValue(
            value=value,
            confidence=confidence,
            evidence=evidence
        )

