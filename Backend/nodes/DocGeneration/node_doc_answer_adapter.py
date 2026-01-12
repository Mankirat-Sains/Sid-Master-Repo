"""
DOCGEN: Adapt document generation outputs into the standard answer fields for downstream verify/correct nodes.
"""
from __future__ import annotations

from typing import Dict, Any, List
from models.rag_state import RAGState
from config.logging_config import log_query


def _extract_citations(result: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not result:
        return []
    if "citations" in result:
        return result.get("citations") or []
    if "sections" in result:
        cites: List[Dict[str, Any]] = []
        for section in result.get("sections", []):
            cites.extend(section.get("citations") or [])
        return cites
    return []


def node_doc_answer_adapter(state: RAGState) -> dict:
    """Set final_answer/answer_citations from doc_generation_result so QA tail can run unchanged."""
    log_query.info("DOCGEN: entered node_doc_answer_adapter")
    result = state.doc_generation_result or {}
    if not result:
        raise RuntimeError("DOCGEN: doc_generation_result missing; generation did not run.")

    if "combined_text" in result:
        final_answer = result.get("combined_text", "")
    else:
        final_answer = result.get("draft_text", "")

    citations = _extract_citations(result)
    warnings = state.doc_generation_warnings or result.get("warnings", [])

    return {
        "final_answer": final_answer,
        "answer": final_answer,  # compatibility if downstream uses 'answer'
        "answer_citations": citations,
        "doc_generation_warnings": warnings,
    }
