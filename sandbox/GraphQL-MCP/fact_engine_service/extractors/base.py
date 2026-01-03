"""Base interface for fact extractors"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from models.fact_result import FactValue, Evidence


class FactExtractor(ABC):
    """
    Base class for all fact extractors.
    
    Each extractor answers ONE fact deterministically.
    """
    
    @property
    @abstractmethod
    def fact_name(self) -> str:
        """Name of the fact this extractor produces"""
        pass
    
    @abstractmethod
    def applies(self, fact_request: str) -> bool:
        """
        Check if this extractor applies to the requested fact.
        
        Args:
            fact_request: The fact name being requested
        
        Returns:
            True if this extractor handles this fact
        """
        pass
    
    def coarse_filter_sql(self, filter_op: str, filter_value: Any) -> Optional[str]:
        """
        Optional SQL predicate for candidate filtering (Phase 1).
        
        This should be a fast, coarse filter that reduces the candidate set.
        It does NOT need to be precise - Phase 2 will confirm.
        
        Args:
            filter_op: The filter operator (=, !=, in, etc.)
            filter_value: The value to filter by
        
        Returns:
            SQL WHERE clause fragment, or None if no coarse filter available
        """
        return None
    
    @abstractmethod
    def extract(self, element_json: Dict[str, Any]) -> FactValue:
        """
        Extract the fact from an element's JSON data.
        
        This is the Phase 2 precise extraction.
        
        Args:
            element_json: The element's data JSON from Speckle
        
        Returns:
            FactValue with value, confidence, and evidence
        """
        pass
    
    def extract_from_graphql(self, element_data: Dict[str, Any]) -> FactValue:
        """
        Extract the fact from GraphQL element data.
        
        Default implementation delegates to extract().
        Override if GraphQL data structure differs.
        
        Args:
            element_data: Element data from GraphQL query
        
        Returns:
            FactValue with value, confidence, and evidence
        """
        return self.extract(element_data)


