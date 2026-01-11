from __future__ import annotations

import re
from typing import Dict, List, Optional, TypedDict


class AnalysisResult(TypedDict, total=False):
    doc_type: Optional[str]
    section_type: Optional[str]
    engineering_function: Optional[str]
    constraints: Dict[str, object]


class QueryAnalyzer:
    """
    Simple rules-based query analyzer for Tier 2.
    """

    SECTION_KEYWORDS = {
        "introduction": "introduction",
        "methodology": "methodology",
        "results": "results",
        "limitations": "limitations",
        "recommendation": "recommendations",
        "recommendations": "recommendations",
        "conclusion": "conclusion",
    }

    DOC_KEYWORDS = {
        "design report": "design_report",
        "calculation": "calculation_narrative",
    }

    ENGINEERING_FUNCTION = {
        "summarize": "summarize_analysis",
        "justify": "justify_design",
        "pass": "report_pass_fail",
        "fail": "report_pass_fail",
        "code": "cite_codes",
    }

    CALC_TYPES = {
        "structural": "structural",
        "thermal": "thermal",
        "electrical": "electrical",
    }

    CODE_PATTERN = re.compile(r"\b(ACI|AISC|ASCE|CSA|IBC|NBCC)[\w\-:.\d]*", re.IGNORECASE)

    def analyze(self, user_request: str) -> AnalysisResult:
        text = user_request.lower()
        doc_type = self._match_map(text, self.DOC_KEYWORDS)
        section_type = self._match_map(text, self.SECTION_KEYWORDS)
        engineering_function = self._match_map(text, self.ENGINEERING_FUNCTION) or "describe_section"
        constraints: Dict[str, object] = {}

        calc = self._match_map(text, self.CALC_TYPES)
        if calc:
            constraints["calculation_type"] = calc

        codes = self.CODE_PATTERN.findall(user_request)
        if codes:
            constraints["code_references"] = codes

        return AnalysisResult(
            doc_type=doc_type,
            section_type=section_type,
            engineering_function=engineering_function,
            constraints=constraints,
        )

    def _match_map(self, text: str, mapping: Dict[str, str]) -> Optional[str]:
        for key, value in mapping.items():
            if key in text:
                return value
        return None
