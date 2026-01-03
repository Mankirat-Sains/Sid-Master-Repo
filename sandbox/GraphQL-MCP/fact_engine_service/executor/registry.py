"""Registry for fact extractors"""
from typing import Dict, List, Optional
from extractors.base import FactExtractor
from extractors import (
    ElementTypeExtractor,
    MaterialExtractor,
    SectionExtractor,
    LevelExtractor,
    OrientationExtractor,
    SystemRoleExtractor,
    ProjectSummaryExtractor,
)


class ExtractorRegistry:
    """Registry for managing fact extractors"""
    
    def __init__(self):
        self._extractors: List[FactExtractor] = []
        self._fact_map: Dict[str, FactExtractor] = {}
        self._register_default_extractors()
    
    def _register_default_extractors(self):
        """Register all default extractors"""
        extractors = [
            ElementTypeExtractor(),
            MaterialExtractor(),
            SectionExtractor(),
            LevelExtractor(),
            OrientationExtractor(),
            SystemRoleExtractor(),
            ProjectSummaryExtractor(),
        ]
        
        for extractor in extractors:
            self.register(extractor)
    
    def register(self, extractor: FactExtractor):
        """Register a new extractor"""
        self._extractors.append(extractor)
        self._fact_map[extractor.fact_name] = extractor
        # Also register by fact name for lookup
        if extractor.fact_name not in self._fact_map:
            self._fact_map[extractor.fact_name] = extractor
    
    def get_extractor(self, fact_name: str) -> Optional[FactExtractor]:
        """Get extractor for a fact name"""
        return self._fact_map.get(fact_name)
    
    def get_extractors_for_facts(self, fact_names: List[str]) -> List[FactExtractor]:
        """Get extractors for multiple fact names"""
        extractors = []
        for fact_name in fact_names:
            extractor = self.get_extractor(fact_name)
            if extractor:
                extractors.append(extractor)
        return extractors
    
    def list_available_facts(self) -> List[str]:
        """List all available fact types"""
        return list(self._fact_map.keys())


# Global registry instance
registry = ExtractorRegistry()


