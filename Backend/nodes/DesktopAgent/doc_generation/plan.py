"""
DOCGEN: Planning node for document generation.
Runs Tier2 QueryAnalyzer to produce a structured doc_request and determines if desktop actions are requested.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple

from models.rag_state import RAGState
from config.logging_config import log_query
from config.settings import SECTION_BY_SECTION_GENERATION, SECTION_BY_SECTION_ALLOWLIST


def _detect_desktop_request(text: str) -> bool:
    lowered = text.lower()
    return any(kw in lowered for kw in ["word", "docx", "save as", "open file", "apply to file", "update document", "apply edits"])


def _should_use_templates(doc_type: Optional[str]) -> bool:
    """Check feature flag + allowlist before hitting Supabase."""
    if not doc_type:
        return False
    if not SECTION_BY_SECTION_GENERATION:
        return False
    if SECTION_BY_SECTION_ALLOWLIST and doc_type.lower() not in SECTION_BY_SECTION_ALLOWLIST:
        return False
    return True


def _resolve_template_sections(company_id: str, doc_type: Optional[str]) -> Tuple[Optional[str], List[Dict[str, Any]], List[str]]:
    """
    Fetch ordered template sections from Supabase when enabled.
    Returns (template_id, sections, warnings).
    """
    if not _should_use_templates(doc_type):
        return None, [], []

    try:
        from templates.template_resolver import resolve_template_sections
    except Exception as exc:  # noqa: BLE001
        log_query.warning("DOCGEN: template resolver unavailable (%s)", exc)
        return None, [], [f"Template resolver unavailable: {exc}"]

    try:
        resolved = resolve_template_sections(company_id=company_id, doc_type=doc_type or "")
    except Exception as exc:  # noqa: BLE001
        log_query.warning("DOCGEN: failed to resolve template sections (%s)", exc)
        return None, [], [f"Template lookup failed: {exc}"]

    if not resolved:
        return None, [], []

    sections = resolved.get("sections") or []
    template_id = resolved.get("template_id")
    # Ensure deterministic ordering
    sections = sorted(sections, key=lambda s: s.get("position_order") or 0)
    return template_id, sections, []


def _normalize_approved_sections(sections: Any) -> List[Dict[str, Any]]:
    """Normalize approved sections list into dicts with text + metadata."""
    normalized: List[Dict[str, Any]] = []
    for sec in sections or []:
        if not isinstance(sec, dict):
            continue
        text = (
            sec.get("text")
            or sec.get("draft_text")
            or sec.get("content")
            or sec.get("body")
            or sec.get("combined_text")
        )
        normalized.append(
            {
                "section_id": sec.get("section_id"),
                "section_type": sec.get("section_type"),
                "position_order": sec.get("position_order"),
                "section_name": sec.get("section_name"),
                "text": text,
                "metadata": sec.get("metadata") or {},
            }
        )
    return normalized


def _build_section_queue(
    template_sections: List[Dict[str, Any]],
    approved_sections: List[Dict[str, Any]],
    section_hint: Optional[str],
) -> Tuple[List[Dict[str, Any]], Optional[str], Optional[str]]:
    """Build an ordered queue with status derived from approved sections."""
    approved_keys = {
        (sec.get("section_id"), (sec.get("section_type") or "").lower()) for sec in approved_sections or [] if isinstance(sec, dict)
    }
    approved_types = {(sec.get("section_type") or "").lower() for sec in approved_sections or [] if isinstance(sec, dict) and sec.get("section_type")}
    queue: List[Dict[str, Any]] = []

    for sec in template_sections:
        if not isinstance(sec, dict):
            continue
        sec_type = (sec.get("section_type") or "").lower() or None
        sec_id = sec.get("section_id")
        status = "approved" if (sec_id, sec_type or "") in approved_keys else "pending"
        if status != "approved" and sec_type and sec_type in approved_types:
            status = "approved"
        queue.append(
            {
                "section_id": sec_id,
                "section_type": sec_type,
                "section_name": sec.get("section_name"),
                "position_order": sec.get("position_order"),
                "status": status,
            }
        )

    if not queue and section_hint:
        queue.append({"section_id": None, "section_type": section_hint, "position_order": 0, "status": "pending"})

    current_id: Optional[str] = None
    current_type: Optional[str] = None
    for sec in queue:
        if sec.get("status") != "approved":
            current_id = sec.get("section_id")
            current_type = sec.get("section_type")
            break

    return queue, current_id, current_type


def build_doc_plan(state: RAGState) -> Dict[str, Any]:
    """Shared planner for docgen flows (subgraph + deep desktop)."""
    try:
        from tier2.query_analyzer import QueryAnalyzer
    except Exception as exc:  # noqa: BLE001
        log_query.error(f"DOCGEN: QueryAnalyzer import failed: {exc}")
        return {
            "doc_request": {},
            "doc_generation_warnings": [f"QueryAnalyzer unavailable: {exc}"],
            "requires_desktop_action": False,
        }

    analyzer = QueryAnalyzer()
    analysis = analyzer.analyze(state.user_query or "")

    doc_type = state.doc_type or analysis.get("doc_type")
    section_type = state.section_type or analysis.get("section_type")
    doc_type_variant = state.doc_type_variant
    if not doc_type_variant and isinstance(state.doc_request, dict):
        doc_type_variant = state.doc_request.get("doc_type_variant")
    if not doc_type_variant:
        doc_type_variant = analysis.get("doc_type_variant")
    company_id = os.getenv("DEMO_COMPANY_ID", "demo_company")

    approved_raw: List[Dict[str, Any]] = getattr(state, "approved_sections", []) or []
    if not approved_raw and isinstance(state.doc_request, dict):
        approved_raw = state.doc_request.get("approved_sections", []) or []
    approved_sections = _normalize_approved_sections(approved_raw)
    template_id, template_sections, template_warnings = _resolve_template_sections(company_id, doc_type)
    section_queue, current_section_id, queue_section_type = _build_section_queue(template_sections, approved_sections, section_type)
    if queue_section_type and not section_type:
        section_type = queue_section_type

    analysis["doc_type"] = doc_type
    analysis["section_type"] = section_type
    if doc_type_variant:
        analysis["doc_type_variant"] = doc_type_variant

    doc_request = {
        **analysis,
        "template_id": template_id,
        "template_sections": template_sections,
        "section_queue": section_queue,
        "approved_sections": approved_sections,
    }

    needs_desktop = _detect_desktop_request(state.user_query or "")
    desktop_plan: Dict[str, Any] = {}
    if needs_desktop:
        desktop_plan = {
            "action": "open_and_save",
            "reason": "User requested document handling (Word/save).",
        }

    warnings = template_warnings
    return {
        "doc_request": doc_request,
        "doc_type": doc_type,
        "doc_type_variant": doc_type_variant,
        "section_type": section_type,
        "template_id": template_id,
        "template_sections": template_sections,
        "section_queue": section_queue,
        "approved_sections": approved_sections,
        "current_section_id": current_section_id,
        "requires_desktop_action": needs_desktop,
        "desktop_action_plan": desktop_plan or None,
        "doc_generation_warnings": warnings,
    }


def node_doc_plan(state: RAGState) -> dict:
    """Produce doc_request using Tier2 QueryAnalyzer and flag desktop actions."""
    log_query.info("DOCGEN: entered node_doc_plan")
    return build_doc_plan(state)
