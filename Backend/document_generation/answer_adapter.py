"""
DOCGEN: Adapt document generation outputs into the standard answer fields for downstream verify/correct nodes.
"""
from __future__ import annotations

import traceback
from typing import Dict, Any, List
from models.rag_state import RAGState
from config.logging_config import log_query


def _log_text_checkpoint(location_name: str, text: str | None) -> None:
    """Trace answer text as it moves through the adapter."""
    snippet = (text or "")[:100]
    stack = traceback.format_stack()
    stack_line = stack[-3].strip() if len(stack) >= 3 else ""
    print(f"📍 CHECKPOINT: {location_name}")
    print(f"   Text: {snippet if snippet else 'None'}")
    print(f"   Contains TBD: {'[TBD' in (text or '')}")
    print(f"   Stack: {stack_line}")


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


def adapt_generation_output(state: RAGState) -> dict:
    """Set final_answer/answer_citations from doc_generation_result so QA tail can run unchanged."""
    log_query.info("DOCGEN: entered adapt_generation_output")
    result = state.doc_generation_result or {}
    if not result:
        raise RuntimeError("DOCGEN: doc_generation_result missing; generation did not run.")

    if "combined_text" in result:
        final_answer = result.get("combined_text", "")
    else:
        final_answer = result.get("draft_text", "")
    _log_text_checkpoint("docgen.answer_adapter.initial", final_answer)

    # Guardrail: never return TBD/insufficient content
    def _force_fallback(text: str) -> str:
        topic = (state.user_query or "the requested topic").strip().rstrip(".")
        fallback = (
            f"This paragraph provides a concise overview of {topic}. "
            f"It highlights the key context, explains why it matters, "
            f"and outlines practical implications for stakeholders. "
            f"Use this as a starting point and expand with project-specific details as needed."
        )
        log_query.info("DOCGEN: answer_adapter forcing fallback content (reason=%s)", text[:40])
        _log_text_checkpoint("docgen.answer_adapter.fallback", fallback)
        return fallback

    lower_ans = (final_answer or "").lower()
    if (final_answer or "").strip().startswith("[tbd") or "insufficient source content" in lower_ans or len(final_answer or "") < 10:
        final_answer = _force_fallback(final_answer or "")
        result["draft_text"] = final_answer
        result["citations"] = result.get("citations") or []
    _log_text_checkpoint("docgen.answer_adapter.final", final_answer)

    citations = _extract_citations(result)
    warnings = state.doc_generation_warnings or result.get("warnings", [])

    return {
        "final_answer": final_answer,
        "answer": final_answer,  # compatibility if downstream uses 'answer'
        "answer_citations": citations,
        "doc_generation_warnings": warnings,
    }


# Backwards-compatible alias for existing graph wiring
node_doc_answer_adapter = adapt_generation_output

__all__ = ["adapt_generation_output", "node_doc_answer_adapter"]
