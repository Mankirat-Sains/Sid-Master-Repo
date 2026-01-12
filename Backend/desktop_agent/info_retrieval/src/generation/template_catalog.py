"""
Template catalog + matcher for Tier 2.
Provides deterministic section outlines and voice rules per doc/section type.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class VoiceRules:
    register: str  # e.g., formal, concise, directive
    tense: str     # e.g., present, past
    pov: str       # e.g., third_person, imperative
    bullets: str   # e.g., dash, numbered


@dataclass
class TemplateSection:
    key: str
    title: str
    required: bool = True
    guidance: Optional[str] = None


@dataclass
class TemplateDefinition:
    doc_type: str
    section_type: Optional[str]
    engineering_function: Optional[str]
    outline: List[TemplateSection]
    voice: VoiceRules
    retrieval_hints: Dict[str, str]


class TemplateCatalog:
    """
    In-memory template definitions. Deterministic and easy to extend.
    """

    def __init__(self) -> None:
        self.templates: List[TemplateDefinition] = [
            TemplateDefinition(
                doc_type="design_report",
                section_type="assumptions",
                engineering_function="justify_design",
                outline=[
                    TemplateSection("intro", "Context", True, "Project context and scope of this section."),
                    TemplateSection("assumptions", "Design Assumptions", True, "List load cases, materials, codes."),
                    TemplateSection("justification", "Rationale", True, "Explain why assumptions are appropriate."),
                    TemplateSection("limits", "Limitations", False, "Note exclusions and caveats."),
                ],
                voice=VoiceRules(register="formal", tense="present", pov="third_person", bullets="dash"),
                retrieval_hints={"tone": "formal", "evidence": "code references"},
            ),
            TemplateDefinition(
                doc_type="calculation_narrative",
                section_type="methodology",
                engineering_function="summarize_analysis",
                outline=[
                    TemplateSection("intro", "Objective", True, "State the calculation objective."),
                    TemplateSection("method", "Methodology", True, "Describe the method or standard used."),
                    TemplateSection("data", "Inputs", True, "Key inputs and sources."),
                    TemplateSection("result", "Results Summary", True, "Summarize computed values."),
                    TemplateSection("checks", "Code/Standard Checks", False, "Compliance checks and governing clauses."),
                ],
                voice=VoiceRules(register="technical", tense="past", pov="third_person", bullets="numbered"),
                retrieval_hints={"tone": "technical", "evidence": "calculations"},
            ),
            TemplateDefinition(
                doc_type="method_statement",
                section_type="methodology",
                engineering_function=None,
                outline=[
                    TemplateSection("scope", "Scope", True),
                    TemplateSection("steps", "Procedure", True, "Stepwise procedure with safety notes."),
                    TemplateSection("qa", "Quality Assurance", False, "Inspections, hold points."),
                    TemplateSection("safety", "Safety", True, "Hazards, PPE, controls."),
                ],
                voice=VoiceRules(register="directive", tense="present", pov="imperative", bullets="numbered"),
                retrieval_hints={"tone": "directive", "evidence": "procedures"},
            ),
            TemplateDefinition(
                doc_type="design_report",
                section_type="results",
                engineering_function="report_pass_fail",
                outline=[
                    TemplateSection("summary", "Results Summary", True, "Pass/fail and governing criteria."),
                    TemplateSection("evidence", "Supporting Evidence", True, "Key calculations and references."),
                    TemplateSection("limitations", "Limitations", False),
                    TemplateSection("actions", "Follow-up Actions", False),
                ],
                voice=VoiceRules(register="concise", tense="present", pov="third_person", bullets="dash"),
                retrieval_hints={"tone": "concise", "evidence": "results"},
            ),
        ]

    def match(
        self,
        doc_type: str,
        section_type: Optional[str],
        engineering_function: Optional[str],
    ) -> TemplateDefinition:
        """
        Best-effort deterministic match:
        1) Exact triple match.
        2) Match on doc_type + section_type.
        3) Match on doc_type only.
        4) Fallback to first template.
        """
        for tmpl in self.templates:
            if (
                tmpl.doc_type == doc_type
                and tmpl.section_type == section_type
                and tmpl.engineering_function == engineering_function
            ):
                return tmpl

        for tmpl in self.templates:
            if tmpl.doc_type == doc_type and tmpl.section_type == section_type:
                return tmpl

        for tmpl in self.templates:
            if tmpl.doc_type == doc_type:
                return tmpl

        return self.templates[0]
