"""
DOCGEN: Task classifier node.
Determines whether a query is QA or document generation (section or report) and seeds doc_type/section_type hints.
"""
from __future__ import annotations

import re
from typing import Dict
from models.rag_state import RAGState
from config.logging_config import log_query


SECTION_KEYWORDS: Dict[str, str] = {
    "introduction": "introduction",
    "scope": "scope",
    "methodology": "methodology",
    "methods": "methodology",
    "findings": "findings",
    "results": "results",
    "recommendations": "recommendations",
    "conclusion": "conclusion",
    "limitations": "limitations",
}


_DOCGEN_RULES = [
    ("report", r"\b(draft|generate|create|write|prepare) (a )?(design )?(report|rp|rfp|proposal)\b"),
    ("section", r"\b(draft|generate|create|write|prepare) (the )?(?P<section>\w+ )?section\b"),
    ("section_named", r"\b(methodology|introduction|findings|results|recommendations|conclusion|scope) section\b"),
    ("desktop_request", r"\bopen .*word\b"),
]


def _detect_task_type(text: str) -> tuple[str | None, str | None, str | None]:
    """
    Heuristic classifier for doc generation vs QA.
    Returns (task_type, section_type_hint, rule_name)
    """
    lowered = text.lower()
    for rule_name, pattern in _DOCGEN_RULES:
        m = re.search(pattern, lowered)
        if not m:
            continue
        section_hint = None
        if m.groupdict().get("section"):
            section_hint = m.group("section").strip()
        if rule_name == "report":
            return "doc_report", section_hint, rule_name
        return "doc_section", section_hint, rule_name
    return None, None, None


def _detect_doc_type(text: str) -> str | None:
    lowered = text.lower()
    if "design report" in lowered or "design rpt" in lowered or "drp" in lowered:
        return "design_report"
    if "calculation" in lowered:
        return "calculation_narrative"
    return None


def _detect_section(text: str) -> str | None:
    lowered = text.lower()
    for key, value in SECTION_KEYWORDS.items():
        if key in lowered:
            return value
    return None


def node_doc_task_classifier(state: RAGState) -> dict:
    """Classify the user query for doc generation vs QA."""
    log_query.info("DOCGEN: entered node_doc_task_classifier")
    task_type, section_hint, rule = _detect_task_type(state.user_query or "")
    doc_type = state.doc_type or _detect_doc_type(state.user_query or "")
    section_type = state.section_type or section_hint or _detect_section(state.user_query or "")
    if task_type:
        log_query.info(f"DOCGEN: classifier routed to {task_type} (rule={rule})")
        workflow = "docgen"
        desktop_policy = "required"
    else:
        log_query.info("DOCGEN: classifier defaulted to QA")
        workflow = "qa"
        desktop_policy = "never"
    return {
        "task_type": task_type or state.task_type or "qa",
        "doc_type": doc_type,
        "section_type": section_type,
        "workflow": workflow,
        "desktop_policy": desktop_policy,
    }
