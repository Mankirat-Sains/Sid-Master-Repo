"""Extractor for project-level summary facts"""
from typing import Dict, Any, Optional, List
from extractors.base import FactExtractor
from models.fact_result import FactValue, Evidence


class ProjectSummaryExtractor(FactExtractor):
    """Extracts project-level summary facts (storeys, palette, dominant system)"""
    
    @property
    def fact_name(self) -> str:
        return "project_summary"
    
    def applies(self, fact_request: str) -> bool:
        return fact_request == "project_summary" or fact_request.startswith("project_")
    
    def extract(self, element_json: Dict[str, Any]) -> FactValue:
        """This extractor works at project level, not element level"""
        # This is a placeholder - project summary is computed from aggregated element facts
        return FactValue(
            value={},
            confidence=0.0,
            evidence=[]
        )
    
    def compute_project_summary(
        self,
        project_elements: List[Dict[str, Any]],
        element_facts: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compute project-level summary from element facts.
        
        Args:
            project_elements: List of element data
            element_facts: Dict mapping element_id -> extracted facts
        
        Returns:
            Summary dict with storeys, palette, dominant_system, etc.
        """
        summary = {
            "storeys": 0,
            "materials": set(),
            "element_types": set(),
            "systems": set(),
            "total_elements": len(project_elements)
        }
        
        # Collect unique levels
        levels = set()
        for elem_id, facts in element_facts.items():
            level_fact = facts.get("level")
            if level_fact and level_fact.get("value") and level_fact["value"] != "unknown":
                levels.add(level_fact["value"])
            
            # Collect materials
            material_fact = facts.get("material")
            if material_fact and material_fact.get("value") and material_fact["value"] != "unknown":
                summary["materials"].add(material_fact["value"])
            
            # Collect element types
            type_fact = facts.get("element_type")
            if type_fact and type_fact.get("value") and type_fact["value"] != "unknown":
                summary["element_types"].add(type_fact["value"])
            
            # Collect systems
            system_fact = facts.get("system_role")
            if system_fact:
                system_value = system_fact.get("value")
                if isinstance(system_value, list):
                    summary["systems"].update(system_value)
                elif system_value and system_value != "unknown":
                    summary["systems"].add(system_value)
        
        # Estimate storeys from levels
        summary["storeys"] = len(levels) if levels else 0
        
        # Determine dominant material
        material_counts = {}
        for elem_id, facts in element_facts.items():
            material_fact = facts.get("material")
            if material_fact and material_fact.get("value") and material_fact["value"] != "unknown":
                mat = material_fact["value"]
                material_counts[mat] = material_counts.get(mat, 0) + 1
        
        if material_counts:
            summary["dominant_material"] = max(material_counts.items(), key=lambda x: x[1])[0]
        else:
            summary["dominant_material"] = "unknown"
        
        # Convert sets to lists for JSON serialization
        summary["materials"] = list(summary["materials"])
        summary["element_types"] = list(summary["element_types"])
        summary["systems"] = list(summary["systems"])
        
        return summary

