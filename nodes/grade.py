"""
Grading Node
Grades documents for relevance to the query
"""
import time
from models.rag_state import RAGState
from config.settings import MAX_GRADED_DOCS
from config.logging_config import log_enh
from utils.plan_executor import self_grade

USE_GRADER = False  # Disable grader for performance


def _log_docs_summary(docs, logger, prefix: str = "Documents"):
    """Helper to log document summary"""
    if not docs:
        logger.info(f"{prefix}: 0 documents")
        return
    projects = set()
    for d in docs:
        md = d.metadata or {}
        proj = md.get("drawing_number") or md.get("project_key")
        if proj:
            projects.add(proj)
    logger.info(f"{prefix}: {len(docs)} docs from {len(projects)} projects")


def node_grade(state: RAGState) -> dict:
    """Grade documents - handles both project docs and code docs separately"""
    t_start = time.time()
    try:
        log_enh.info(">>> GRADE START")
        
        data_sources = state.data_sources or {"project_db": True, "code_db": False, "coop_manual": False}
        project_db_enabled = data_sources.get("project_db", True)
        code_db_enabled = data_sources.get("code_db", False)
        coop_db_enabled = data_sources.get("coop_manual", False)
        
        log_enh.info(f"USE_GRADER={USE_GRADER}, Project docs: {len(state.retrieved_docs or [])}, Code docs: {len(state.retrieved_code_docs or [])}, Coop docs: {len(state.retrieved_coop_docs or [])}")

        # Grade project docs
        if not USE_GRADER:
            graded = (state.retrieved_docs or [])[:MAX_GRADED_DOCS]
            log_enh.info(f"Grading disabled - capping project docs to MAX_GRADED_DOCS={MAX_GRADED_DOCS}")
            _log_docs_summary(graded, log_enh, "Graded (capped)")
        else:
            log_enh.info("Running self_grade on project docs...")
            graded = self_grade(state.user_query, state.retrieved_docs)
            _log_docs_summary(graded, log_enh, "Graded (filtered)")

        # Grade code docs separately
        graded_code = []
        if code_db_enabled and state.retrieved_code_docs:
            if not USE_GRADER:
                graded_code = (state.retrieved_code_docs or [])[:MAX_GRADED_DOCS]
                log_enh.info(f"Grading disabled - capping code docs to MAX_GRADED_DOCS={MAX_GRADED_DOCS}")
            else:
                log_enh.info("Running self_grade on code docs...")
                graded_code = self_grade(state.user_query, state.retrieved_code_docs)

        # Grade coop docs separately
        graded_coop = []
        if coop_db_enabled and state.retrieved_coop_docs:
            if not USE_GRADER:
                graded_coop = (state.retrieved_coop_docs or [])[:MAX_GRADED_DOCS]
                log_enh.info(f"Grading disabled - capping coop docs to MAX_GRADED_DOCS={MAX_GRADED_DOCS}")
            else:
                log_enh.info("Running self_grade on coop docs...")
                graded_coop = self_grade(state.user_query, state.retrieved_coop_docs)

        t_elapsed = time.time() - t_start
        log_enh.info(f"<<< GRADE DONE in {t_elapsed:.2f}s")
        
        result = {"graded_docs": graded}
        if graded_code:
            result["graded_code_docs"] = graded_code
        if graded_coop:
            result["graded_coop_docs"] = graded_coop
        
        return result
    except Exception as e:
        log_enh.error(f"Grading failed: {e}")
        t_elapsed = time.time() - t_start
        log_enh.info(f"<<< GRADE DONE (with error) in {t_elapsed:.2f}s")
        graded = (state.retrieved_docs or [])[:MAX_GRADED_DOCS]
        graded_code = (state.retrieved_code_docs or [])[:MAX_GRADED_DOCS] if state.retrieved_code_docs else []
        graded_coop = (state.retrieved_coop_docs or [])[:MAX_GRADED_DOCS] if state.retrieved_coop_docs else []
        result = {"graded_docs": graded}
        if graded_code:
            result["graded_code_docs"] = graded_code
        if graded_coop:
            result["graded_coop_docs"] = graded_coop
        return result

