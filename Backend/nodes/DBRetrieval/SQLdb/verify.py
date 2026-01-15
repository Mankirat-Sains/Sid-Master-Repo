"""
Verification Node
Lightweight checks with token bounds and simple fallbacks.
"""
import re
import time
from typing import Any, Dict, List

from langchain_core.documents import Document

from models.db_retrieval_state import DBRetrievalState
from config.settings import USE_VERIFIER, MAX_VERIFIER_TOKENS
from config.logging_config import log_enh
from utils.token_counter import count_tokens

PROJECT_RE = re.compile(r"\\d{2}-\\d{2}-\\d{3,4}")


def _doc_text(doc: Any) -> str:
    """Safely extract text content from a Document-like object."""
    if isinstance(doc, Document):
        return doc.page_content or ""
    if isinstance(doc, dict):
        return doc.get("page_content") or doc.get("content") or ""
    return str(doc) if doc is not None else ""


def _check_citations_present(answer: str, citations: List[Dict[str, Any]], retrieved: List[Any]) -> Dict[str, Any]:
    """Check if answer has citations when it should."""
    if not retrieved:
        return {"name": "citations_present", "fails": False}

    if len(answer) < 100:
        return {"name": "citations_present", "fails": False}

    if not citations:
        return {
            "name": "citations_present",
            "fails": True,
            "issues": ["No citations in lengthy answer with retrieved documents"],
        }

    return {"name": "citations_present", "fails": False}


def _check_answer_grounded(answer: str, retrieved: List[Any]) -> Dict[str, Any]:
    """Heuristic grounding check using term overlap."""
    if not retrieved or not answer:
        return {"name": "answer_grounded", "fails": False}

    answer_lower = answer.lower()
    answer_terms = {w for w in answer_lower.split() if len(w) > 4}
    doc_terms = set()
    for doc in retrieved[:5]:
        doc_terms.update({w for w in _doc_text(doc).lower().split() if len(w) > 4})

    if answer_terms:
        overlap_ratio = len(answer_terms & doc_terms) / len(answer_terms)
        if overlap_ratio < 0.2:
            return {
                "name": "answer_grounded",
                "fails": True,
                "issues": [f"Low grounding: {overlap_ratio:.1%} term overlap with docs"],
            }

    return {"name": "answer_grounded", "fails": False}


def _check_no_hallucinations(answer: str, retrieved: List[Any]) -> Dict[str, Any]:
    """Detect common hallucination markers when docs exist."""
    if not answer:
        return {"name": "no_hallucinations", "fails": False}

    hallucination_phrases = [
        "i don't have access to",
        "i cannot access",
        "as an ai",
        "i don't know",
        "i'm not sure",
    ]

    answer_lower = answer.lower()
    found = [p for p in hallucination_phrases if p in answer_lower]

    if found and retrieved:
        return {
            "name": "no_hallucinations",
            "fails": True,
            "issues": [f"Hallucination markers found: {found}"],
        }

    return {"name": "no_hallucinations", "fails": False}


def node_verify(state: DBRetrievalState) -> dict:
    """Verify answer quality with bounded token usage and lightweight checks."""
    t_start = time.time()
    log_enh.info(">>> VERIFY START")

    if not USE_VERIFIER:
        t_elapsed = time.time() - t_start
        log_enh.info(f"Verification disabled - skipping ({t_elapsed:.2f}s)")
        return {"needs_fix": False, "verification_issues": [], "verification_checks": []}

    answer_text = (
        getattr(state, "final_answer", None)
        or getattr(state, "code_answer", None)
        or getattr(state, "coop_answer", None)
        or ""
    )
    citations = (
        getattr(state, "answer_citations", None)
        or getattr(state, "code_citations", None)
        or getattr(state, "coop_citations", None)
        or []
    )
    retrieved_docs = list(getattr(state, "graded_docs", None) or getattr(state, "retrieved_docs", []) or [])

    answer_tokens = count_tokens(answer_text)
    if answer_tokens > MAX_VERIFIER_TOKENS:
        log_enh.warning(
            f"Skipping verification: answer too long ({answer_tokens} tokens > {MAX_VERIFIER_TOKENS})"
        )
        t_elapsed = time.time() - t_start
        log_enh.info(f"<<< VERIFY DONE (skipped due to length) in {t_elapsed:.2f}s")
        return {
            "needs_fix": False,
            "verification_issues": ["answer_too_long_for_verifier"],
            "verification_checks": [],
        }

    checks = [
        _check_citations_present(answer_text, citations, retrieved_docs),
        _check_answer_grounded(answer_text, retrieved_docs),
        _check_no_hallucinations(answer_text, retrieved_docs),
    ]

    needs_fix = any(c.get("fails") for c in checks)
    issues = [issue for c in checks for issue in c.get("issues", [])]

    t_elapsed = time.time() - t_start
    log_enh.info(f"<<< VERIFY DONE in {t_elapsed:.2f}s | needs_fix={needs_fix} | issues={len(issues)}")

    return {
        "needs_fix": needs_fix,
        "verification_issues": issues,
        "verification_checks": checks,
    }


def _verify_route(state: DBRetrievalState) -> str:
    """Route based on whether verification flagged issues."""
    return "fix" if getattr(state, "needs_fix", False) else "ok"
