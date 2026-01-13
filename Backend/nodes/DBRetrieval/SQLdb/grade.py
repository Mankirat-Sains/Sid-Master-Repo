"""
Grading Node
Token-aware grading with heuristic fallback.
"""
import time
from typing import List

from langchain_core.documents import Document

from models.db_retrieval_state import DBRetrievalState
from config.settings import (
    MAX_GRADED_DOCS,
    USE_GRADER,
    MAX_DOCS_TO_GRADE,
    MAX_GRADER_TOKENS,
)
from config.logging_config import log_enh
from utils.plan_executor import self_grade
from utils.token_counter import count_tokens


def _log_docs_summary(docs, logger, prefix: str = "Documents"):
    """Helper to log document summary"""
    if not docs:
        logger.info(f"{prefix}: 0 documents")
        return
    projects = set()
    for d in docs:
        md = getattr(d, "metadata", {}) or {}
        proj = md.get("drawing_number") or md.get("project_key")
        if proj:
            projects.add(proj)
    logger.info(f"{prefix}: {len(docs)} docs from {len(projects)} projects")


def _doc_text(doc: Document) -> str:
    """Extract text content from a Document-like object."""
    if isinstance(doc, Document):
        return doc.page_content or ""
    if isinstance(doc, dict):
        return doc.get("page_content") or doc.get("content") or ""
    return str(doc) if doc is not None else ""


def _heuristic_grade(query: str, docs: List[Document]) -> List[Document]:
    """Fast heuristic grading when token limits are exceeded."""
    query_terms = {w for w in (query or "").lower().split() if len(w) > 3}
    scored = []
    for idx, doc in enumerate(docs):
        content_terms = {w for w in _doc_text(doc).lower().split() if len(w) > 3}
        score = (len(query_terms & content_terms) / len(query_terms)) if query_terms else 0.0
        scored.append((score, idx, doc))
    scored.sort(key=lambda t: (-t[0], t[1]))
    top_docs = [doc for _, __, doc in scored[: min(8, len(scored))]]
    return top_docs


def _grade_collection(query: str, docs: List[Document], label: str) -> List[Document]:
    """Grade a collection with token-aware fallback."""
    if not docs:
        log_enh.info(f"No {label} docs to grade")
        return []

    limited = docs[:MAX_DOCS_TO_GRADE]
    total_tokens = sum(count_tokens(_doc_text(d)) for d in limited)

    if not USE_GRADER:
        log_enh.info(
            f"Grading disabled - capping {label} docs to MAX_DOCS_TO_GRADE={MAX_DOCS_TO_GRADE}"
        )
        return limited

    if total_tokens > MAX_GRADER_TOKENS:
        log_enh.info(
            f"Heuristic grading for {label}: {total_tokens} tokens > {MAX_GRADER_TOKENS}"
        )
        return _heuristic_grade(query, limited)

    log_enh.info(
        f"LLM grading {label}: {len(limited)} docs ({total_tokens} tokens, cap={MAX_GRADER_TOKENS})"
    )
    graded = self_grade(query, limited)
    return graded[:MAX_GRADED_DOCS]


def node_grade(state: DBRetrievalState) -> dict:
    """Grade documents - handles project, code, and coop docs separately."""
    t_start = time.time()
    try:
        log_enh.info(">>> GRADE START")

        query = getattr(state, "user_query", "") or ""
        data_sources = getattr(state, "data_sources", None) or {
            "project_db": True,
            "code_db": False,
            "coop_manual": False,
            "speckle_db": False,
        }

        project_db_enabled = data_sources.get("project_db", True)
        code_db_enabled = data_sources.get("code_db", False)
        coop_db_enabled = data_sources.get("coop_manual", False)

        graded_projects = _grade_collection(query, list(getattr(state, "retrieved_docs", []) or []), "project") if project_db_enabled else []
        graded_code = _grade_collection(query, list(getattr(state, "retrieved_code_docs", []) or []), "code") if code_db_enabled else []
        graded_coop = _grade_collection(query, list(getattr(state, "retrieved_coop_docs", []) or []), "coop") if coop_db_enabled else []

        _log_docs_summary(graded_projects, log_enh, "Graded project")
        _log_docs_summary(graded_code, log_enh, "Graded code")
        _log_docs_summary(graded_coop, log_enh, "Graded coop")

        t_elapsed = time.time() - t_start
        log_enh.info(f"<<< GRADE DONE in {t_elapsed:.2f}s")

        result = {"graded_docs": graded_projects}
        if graded_code:
            result["graded_code_docs"] = graded_code
        if graded_coop:
            result["graded_coop_docs"] = graded_coop
        return result

    except Exception as e:
        log_enh.error(f"Grading failed: {e}")
        t_elapsed = time.time() - t_start
        log_enh.info(f"<<< GRADE DONE (with error) in {t_elapsed:.2f}s")
        graded = (getattr(state, "retrieved_docs", []) or [])[:MAX_GRADED_DOCS]
        graded_code = (getattr(state, "retrieved_code_docs", []) or [])[:MAX_GRADED_DOCS]
        graded_coop = (getattr(state, "retrieved_coop_docs", []) or [])[:MAX_GRADED_DOCS]
        result = {"graded_docs": graded}
        if graded_code:
            result["graded_code_docs"] = graded_code
        if graded_coop:
            result["graded_coop_docs"] = graded_coop
        return result
