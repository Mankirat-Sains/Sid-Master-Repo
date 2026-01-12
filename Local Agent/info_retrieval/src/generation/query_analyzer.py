"""
Rule-based query analyzer for Tier 2 (template matching + voice rules).
Returns structured hints for template selection and retrieval filters.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class QueryConstraints:
    code_references: List[str] = field(default_factory=list)
    project_context: Optional[str] = None
    required_sections: List[str] = field(default_factory=list)
    calculation_type: Optional[str] = None


@dataclass
class QueryAnalysis:
    doc_type: str
    section_type: Optional[str]
    engineering_function: Optional[str]
    constraints: QueryConstraints


class QueryAnalyzer:
    """
    Lightweight, deterministic analyzer that infers doc_type, section_type,
    engineering_function, and constraints from a user request string.
    """

    DOC_TYPE_MAP = {
        "method": "method_statement",
        "procedure": "method_statement",
        "design": "design_report",
        "report": "design_report",
        "calc": "calculation_narrative",
        "calculation": "calculation_narrative",
        "analysis": "calculation_narrative",
    }

    SECTION_TYPE_MAP = {
        "assumption": "assumptions",
        "assumptions": "assumptions",
        "scope": "scope",
        "method": "methodology",
        "methodology": "methodology",
        "procedure": "methodology",
        "result": "results",
        "results": "results",
        "conclusion": "conclusion",
        "summary": "executive_summary",
        "limitations": "limitations",
        "reference": "references",
        "code": "references",
    }

    ENGINEERING_FUNCTION_MAP = {
        "justify": "justify_design",
        "support": "justify_design",
        "summarize": "summarize_analysis",
        "summary": "summarize_analysis",
        "pass/fail": "report_pass_fail",
        "compliance": "report_pass_fail",
        "meets code": "report_pass_fail",
        "cite": "cite_codes",
        "code": "cite_codes",
    }

    CALC_TYPE_MAP = {
        "structural": "structural",
        "geotech": "geotechnical",
        "geotechnical": "geotechnical",
        "mechanical": "mechanical",
        "electrical": "electrical",
        "fire": "fire_protection",
        "seismic": "seismic",
    }

    CODE_PATTERN = re.compile(r"\b(ACI|AISC|CSA|ASCE|ASTM|IBC|NBCC)[\w\-:.\d]*", re.IGNORECASE)

    def analyze(self, user_request: str) -> QueryAnalysis:
        text = user_request.lower()
        doc_type = self._infer(self.DOC_TYPE_MAP, text, default="design_report")
        section_type = self._infer(self.SECTION_TYPE_MAP, text)
        engineering_function = self._infer(self.ENGINEERING_FUNCTION_MAP, text)
        calculation_type = self._infer(self.CALC_TYPE_MAP, text)
        constraints = QueryConstraints(
            code_references=self._extract_codes(user_request),
            project_context=self._short_context(user_request),
            required_sections=[],
            calculation_type=calculation_type,
        )
        return QueryAnalysis(
            doc_type=doc_type,
            section_type=section_type,
            engineering_function=engineering_function,
            constraints=constraints,
        )

    def _infer(self, mapping: Dict[str, str], text: str, default: Optional[str] = None) -> Optional[str]:
        for key, value in mapping.items():
            if key in text:
                return value
        return default

    def _extract_codes(self, text: str) -> List[str]:
        return [m.group(0) for m in self.CODE_PATTERN.finditer(text)]

    def _short_context(self, text: str, max_len: int = 180) -> str:
        trimmed = " ".join(text.strip().split())
        return trimmed[:max_len]
