"""
Tier 2 planner: combines QueryAnalyzer + TemplateCatalog to produce
an actionable generation plan (outline, voice rules, retrieval filters).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from generation.query_analyzer import QueryAnalyzer, QueryAnalysis
from generation.template_catalog import TemplateCatalog, TemplateDefinition


@dataclass
class GenerationPlan:
    analysis: QueryAnalysis
    template: TemplateDefinition
    retrieval_filters: Dict[str, Optional[str]]


class GenerationPlanner:
    """
    Surface Tier 2 outputs without changing ingestion/retrieval internals.
    """

    def __init__(self, company_id: Optional[str] = None) -> None:
        self.company_id = company_id
        self.analyzer = QueryAnalyzer()
        self.catalog = TemplateCatalog()

    def plan(self, user_request: str) -> GenerationPlan:
        analysis = self.analyzer.analyze(user_request)
        template = self.catalog.match(
            doc_type=analysis.doc_type,
            section_type=analysis.section_type,
            engineering_function=analysis.engineering_function,
        )
        retrieval_filters = {
            "company_id": self.company_id,
            "doc_type": analysis.doc_type,
            "section_type": analysis.section_type,
            "calculation_type": analysis.constraints.calculation_type,
        }
        return GenerationPlan(
            analysis=analysis,
            template=template,
            retrieval_filters=retrieval_filters,
        )
