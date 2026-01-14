"""
DOCGEN: Task classifier node.
Determines whether a query is QA or document generation (section or report) and seeds doc_type/section_type hints.
"""
from __future__ import annotations

import re
from typing import Dict, Tuple, Optional

from models.rag_state import RAGState
from config.logging_config import log_query


SECTION_KEYWORDS: Dict[str, str] = {
    "introduction": "introduction",
    "scope": "scope",
    "overview": "introduction",
    "summary": "conclusions",
    "executive summary": "conclusions",
    "methodology": "methodology",
    "methods": "methodology",
    "findings": "findings",
    "results": "results",
    "recommendations": "recommendations",
    "recommendation": "recommendations",
    "conclusion": "conclusion",
    "limitations": "limitations",
    "checklist": "methodology",
    "table": "results",
    "email": "conclusions",
    "status": "conclusions",
    "memo": "methodology",
}

# Simple vs complex generation cues
_SIMPLE_GENERATION_PATTERNS = [
    "generate a random paragraph",
    "write something creative",
    "make up a story",
]

_COMPLEX_GENERATION_PATTERNS = [
    "report",
    "analysis",
    "summary",
    "project",
    "design",
    "documentation",
    "specification",
    "plan",
    "assessment",
    "using our",
    "from our",
    "based on our",
    "garage",
    "beam",
    "structural",
    "engineering",
    "building",
]


_DOC_VERBS = r"(draft|generate|create|write|prepare|produce|compose)"
_DOCGEN_RULES = [
    {
        "name": "report",
        "pattern": rf"\b{_DOC_VERBS} (a )?(design )?(report|rp|rfp|proposal)\b",
        "task_type": "doc_report",
    },
    {
        "name": "section",
        "pattern": rf"\b{_DOC_VERBS} (the )?(?P<section>\w+ )?section\b",
        "task_type": "doc_section",
        "section_from_group": True,
    },
    {
        "name": "section_named",
        "pattern": rf"\b(methodology|introduction|findings|results|recommendations|conclusion|scope) section\b",
        "task_type": "doc_section",
    },
    {
        "name": "generate_section",
        "pattern": rf"\bgenerate (an? )?(?P<section>\w+ )?(section|methodology|introduction|findings|results|recommendations|conclusion)\b",
        "task_type": "doc_section",
        "section_from_group": True,
    },
    {
        "name": "create_document",
        "pattern": rf"\b(create|compose|prepare) (a )?(report|document)\b",
        "task_type": "doc_section",
    },
    {
        "name": "executive_summary",
        "pattern": rf"\b{_DOC_VERBS} .*?(executive summary|one[- ]page summary|one[- ]pager|summary|overview)\b",
        "task_type": "doc_section",
        "doc_type": "design_report",
        "section_hint": "conclusions",
    },
    {
        "name": "status_email",
        "pattern": rf"\b{_DOC_VERBS} .*?(status update|status email|status report|client email|update email|status note)\b",
        "task_type": "doc_section",
        "doc_type": "status_email",
        "section_hint": "conclusions",
    },
    {
        "name": "memo",
        "pattern": rf"\b{_DOC_VERBS} .*?(technical memo|memo|memorandum)\b",
        "task_type": "doc_section",
        "doc_type": "technical_memo",
    },
    {
        "name": "checklist",
        "pattern": rf"\b{_DOC_VERBS} .*?(checklist|punch ?list|punchlist|bom|bill of materials|bill-of-materials|material take ?-?off|takeoff|table)\b",
        "task_type": "doc_section",
        "doc_type": "bom_table",
        "section_hint": "results",
    },
    {
        "name": "comparison_recommendation",
        "pattern": rf"\b{_DOC_VERBS} .*?(compare|comparison|versus|vs\\.?).*?(recommend|recommendation|preferred|select|choose)\b",
        "task_type": "doc_section",
        "doc_type": "design_report",
        "section_hint": "recommendations",
    },
    {
        "name": "desktop_request",
        "pattern": r"\bopen .*word\b",
        "task_type": "doc_section",
    },
]


def _analyze_with_query_analyzer(text: str) -> Dict[str, str]:
    """
    Best-effort fallback using Tier2 QueryAnalyzer to infer doc_type/section_type.
    Returns empty values if analyzer is unavailable.
    """
    try:
        from tier2.query_analyzer import QueryAnalyzer

        analysis = QueryAnalyzer().analyze(text)
        return {
            "doc_type": analysis.get("doc_type") or "",
            "section_type": analysis.get("section_type") or "",
        }
    except Exception as exc:  # noqa: BLE001
        log_query.warning(f"DOCGEN: QueryAnalyzer fallback unavailable ({exc})")
        return {"doc_type": "", "section_type": ""}


def _detect_task_type(text: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """
    Heuristic classifier for doc generation vs QA.
    Returns (task_type, section_type_hint, rule_name, doc_type_hint)
    """
    lowered = text.lower()
    for rule in _DOCGEN_RULES:
        m = re.search(rule["pattern"], lowered)
        if not m:
            continue
        section_hint = rule.get("section_hint")
        if rule.get("section_from_group") and m.groupdict().get("section"):
            section_hint = m.group("section").strip()
        task_type = rule.get("task_type", "doc_section")
        doc_type_hint = rule.get("doc_type")
        if rule["name"] == "report":
            task_type = "doc_report"
        return task_type, section_hint, rule["name"], doc_type_hint
    return None, None, None, None


def _detect_doc_type(text: str) -> str | None:
    lowered = text.lower()
    if "design report" in lowered or "design rpt" in lowered or "drp" in lowered:
        return "design_report"
    if any(x in lowered for x in ["bom", "bill of materials", "bill-of-materials", "material takeoff", "take-off"]):
        return "bom_table"
    if "checklist" in lowered or "punch list" in lowered or "punchlist" in lowered:
        return "checklist"
    if "memo" in lowered or "memorandum" in lowered:
        return "technical_memo"
    if "status update" in lowered or "status email" in lowered or "status report" in lowered or "client email" in lowered:
        return "status_email"
    if "calculation" in lowered:
        return "calculation_narrative"
    return None


def _detect_section(text: str) -> str | None:
    lowered = text.lower()
    for key, value in SECTION_KEYWORDS.items():
        if key in lowered:
            return value
    return None


def _classify_generation_complexity(text: str) -> Tuple[Optional[str], Optional[bool], Optional[bool]]:
    """
    Detect whether the request is a simple generation (no retrieval) or complex (needs retrieval).
    Returns (task_type, needs_retrieval, retrieval_completed).
    """
    lowered = text.lower()
    is_simple = any(pattern in lowered for pattern in _SIMPLE_GENERATION_PATTERNS)
    is_complex = any(pattern in lowered for pattern in _COMPLEX_GENERATION_PATTERNS)

    if is_simple and not is_complex:
        return "simple_generation", False, True
    if is_complex:
        return "complex_generation", True, False
    # Default to retrieval for ambiguous queries
    return None, True, False


def classify_document_task(state: RAGState) -> dict:
    """Classify the user query for document generation vs QA."""
    log_query.info("DOCGEN: entered classify_document_task")
    log_query.info("🎯 DOCGEN CLASSIFYING: '%s'", state.user_query)

    # Track retrieval intent defaults up front
    needs_retrieval = getattr(state, "needs_retrieval", True)
    retrieval_completed = getattr(state, "retrieval_completed", False)

    task_type, section_hint, rule, doc_type_hint = _detect_task_type(state.user_query or "")
    doc_type = state.doc_type or doc_type_hint or _detect_doc_type(state.user_query or "")
    section_type = state.section_type or section_hint or _detect_section(state.user_query or "")

    # Fallback: ask QueryAnalyzer for doc intent if rules missed
    analyzer_doc_type = None
    analyzer_section = None
    if not task_type or not doc_type or not section_type:
        analysis = _analyze_with_query_analyzer(state.user_query or "")
        analyzer_doc_type = analysis.get("doc_type") or None
        analyzer_section = analysis.get("section_type") or None
        doc_type = doc_type or analyzer_doc_type
        section_type = section_type or analyzer_section
        if not task_type and (analyzer_doc_type or analyzer_section):
            task_type = "doc_section"
            rule = rule or "query_analyzer"

    # Simple vs complex generation cues (used to determine retrieval needs)
    gen_task_type, classified_needs_retrieval, classified_retrieval_completed = _classify_generation_complexity(
        state.user_query or ""
    )
    if classified_needs_retrieval is not None:
        needs_retrieval = classified_needs_retrieval
    if classified_retrieval_completed is not None:
        retrieval_completed = classified_retrieval_completed

    # If caller already hinted task_type, respect it
    task_type = task_type or state.task_type or "qa"

    doc_intent = (
        task_type in {"doc_section", "doc_report"}
        or bool(doc_type)
        or bool(analyzer_doc_type)
        or bool(rule)
        or bool(gen_task_type)
    )
    if doc_intent and task_type == "qa":
        task_type = gen_task_type or "doc_section"

    if doc_intent:
        workflow = "docgen"
        desktop_policy = "required"
        log_query.info(f"DOCGEN: classifier routed to {task_type} (rule={rule or 'heuristic'})")
    else:
        workflow = "qa"
        desktop_policy = "never"
        log_query.info("DOCGEN: classifier defaulted to QA")

    log_query.info(
        "✅ DOCGEN CLASSIFIED: task_type=%s | workflow=%s | needs_retrieval=%s | retrieval_completed=%s",
        task_type,
        workflow,
        needs_retrieval if doc_intent else True,
        retrieval_completed if doc_intent else False,
    )

    return {
        "task_type": task_type,
        "doc_type": doc_type,
        "section_type": section_type,
        "workflow": workflow,
        "desktop_policy": desktop_policy,
        "needs_retrieval": needs_retrieval if doc_intent else True,
        "retrieval_completed": retrieval_completed if doc_intent else False,
        "generation_task_type": gen_task_type or task_type,
        "classified": True,
    }


# Backwards-compatible alias for existing graph wiring
node_doc_task_classifier = classify_document_task

__all__ = ["classify_document_task", "node_doc_task_classifier"]
