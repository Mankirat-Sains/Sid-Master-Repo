"""
DOCGEN: Planning node for document generation.
Runs Tier2 QueryAnalyzer to produce a structured doc_request and determines if desktop actions are requested.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict

from models.rag_state import RAGState
from config.logging_config import log_query


def _ensure_info_retrieval_path() -> None:
    """Ensure info_retrieval/src is on sys.path for imports."""
    here = Path(__file__).resolve()
    candidates = set()
    if len(here.parents) >= 3:
        candidates.add(here.parents[3])
    if len(here.parents) >= 2:
        candidates.add(here.parents[2])
    if len(here.parents) >= 4:
        candidates.add(here.parents[4])
    candidates.add((here.parent / "../../../info_retrieval/src").resolve())

    for base in candidates:
        ir_src = Path(base) / "info_retrieval" / "src"
        if ir_src.exists() and str(ir_src) not in sys.path:
            sys.path.insert(0, str(ir_src))


def _detect_desktop_request(text: str) -> bool:
    lowered = text.lower()
    return any(kw in lowered for kw in ["word", "docx", "save as", "open file", "apply to file", "update document", "apply edits"])


def node_doc_plan(state: RAGState) -> dict:
    """Produce doc_request using Tier2 QueryAnalyzer and flag desktop actions."""
    log_query.info("DOCGEN: entered node_doc_plan")
    _ensure_info_retrieval_path()
    try:
        from tier2.query_analyzer import QueryAnalyzer
    except Exception as exc:
        log_query.error(f"DOCGEN: QueryAnalyzer import failed: {exc}")
        return {
            "doc_request": {},
            "doc_generation_warnings": [f"QueryAnalyzer unavailable: {exc}"],
            "requires_desktop_action": False,
        }

    analyzer = QueryAnalyzer()
    analysis = analyzer.analyze(state.user_query or "")

    # Allow classifier-provided hints to override analyzer when set
    doc_type = state.doc_type or analysis.get("doc_type")
    section_type = state.section_type or analysis.get("section_type")
    analysis["doc_type"] = doc_type
    analysis["section_type"] = section_type

    needs_desktop = _detect_desktop_request(state.user_query or "")
    desktop_plan: Dict[str, Any] = {}
    if needs_desktop:
        desktop_plan = {
            "action": "open_and_save",
            "reason": "User requested document handling (Word/save).",
        }

    return {
        "doc_request": analysis,
        "doc_type": doc_type,
        "section_type": section_type,
        "requires_desktop_action": needs_desktop,
        "desktop_action_plan": desktop_plan or None,
    }
