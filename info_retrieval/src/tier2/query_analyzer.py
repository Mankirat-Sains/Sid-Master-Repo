"""
Query Analyzer for Tier 2.
Converts natural language request into structured parameters.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, TypedDict


class StructuredQuery(TypedDict):
    """Structured representation of user request."""

    doc_type: str
    section_type: str
    engineering_function: str
    constraints: Dict[str, Any]


class QueryAnalyzer:
    """
    Analyze user requests into structured parameters.

    MVP: Rules-based keyword matching.
    Later: Can upgrade to LLM-based classification.
    """

    # Document type patterns
    DOC_TYPE_PATTERNS: Dict[str, List[str]] = {
        "design_report": ["design report", "design document", "engineering report"],
        "calculation_narrative": ["calculation", "calc narrative", "calc report", "design calc"],
        "method_statement": ["method statement", "construction method"],
        "technical_memo": ["memo", "technical memorandum"],
    }

    # Section type patterns
    SECTION_PATTERNS: Dict[str, List[str]] = {
        "introduction": ["introduction", "intro", "overview", "background"],
        "assumptions": ["assumptions", "design assumptions", "basis"],
        "methodology": ["methodology", "method", "approach", "procedure"],
        "analysis": ["analysis", "structural analysis", "thermal analysis"],
        "results": ["results", "findings", "output"],
        "conclusions": ["conclusions", "conclusion", "summary"],
        "references": ["references", "bibliography", "codes"],
    }

    # Engineering function patterns
    FUNCTION_PATTERNS: Dict[str, List[str]] = {
        "justify_design": ["justify", "rationale", "why", "reasoning"],
        "summarize_analysis": ["summarize", "summary", "overview"],
        "report_pass_fail": ["pass", "fail", "compliance", "check"],
        "cite_codes": ["cite", "reference", "code", "standard"],
        "describe_section": [],
    }

    # Calculation type patterns
    CALC_TYPE_PATTERNS: Dict[str, List[str]] = {
        "structural": ["structural", "beam", "column", "foundation", "load"],
        "thermal": ["thermal", "heat", "hvac", "temperature", "cooling", "heating"],
        "electrical": ["electrical", "power", "voltage", "circuit"],
        "geotechnical": ["geotechnical", "soil", "foundation", "bearing"],
    }

    def analyze(self, user_request: str) -> StructuredQuery:
        """
        Parse user request into structured query.

        Args:
            user_request: Natural language request

        Returns:
            StructuredQuery with doc_type, section_type, function, constraints
        """
        request_lower = user_request.lower()

        doc_type = self._detect_doc_type(request_lower)
        section_type = self._detect_section_type(request_lower)
        engineering_function = self._detect_function(request_lower)
        constraints = self._extract_constraints(request_lower, user_request)

        return StructuredQuery(
            doc_type=doc_type,
            section_type=section_type,
            engineering_function=engineering_function,
            constraints=constraints,
        )

    def _detect_doc_type(self, text: str) -> str:
        for doc_type, patterns in self.DOC_TYPE_PATTERNS.items():
            if any(pattern in text for pattern in patterns):
                return doc_type
        return "design_report"

    def _detect_section_type(self, text: str) -> str:
        for section_type, patterns in self.SECTION_PATTERNS.items():
            if any(pattern in text for pattern in patterns):
                return section_type
        return "methodology"

    def _detect_function(self, text: str) -> str:
        for function, patterns in self.FUNCTION_PATTERNS.items():
            if any(pattern in text for pattern in patterns):
                return function
        return "describe_section"

    def _extract_constraints(self, text_lower: str, original_text: str) -> Dict[str, Any]:
        constraints: Dict[str, Any] = {}

        for calc_type, patterns in self.CALC_TYPE_PATTERNS.items():
            if any(pattern in text_lower for pattern in patterns):
                constraints["calculation_type"] = calc_type
                break

        code_pattern = r"\b([A-Z]{2,5}\s*\d{2,4}(?:-\d{2})?)\b"
        codes = re.findall(code_pattern, original_text)
        if codes:
            constraints["code_references"] = codes

        element_types = ["beam", "column", "slab", "foundation", "wall", "truss"]
        for element in element_types:
            if element in text_lower:
                constraints["element_type"] = element
                break

        system_types = ["HVAC", "plumbing", "electrical", "fire protection"]
        for system in system_types:
            if system.lower() in text_lower:
                constraints["system_type"] = system
                break

        return constraints
