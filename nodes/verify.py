"""
Verification Node
Verifies answer quality and correctness
"""
import json
import re
import time
from typing import List
from langchain_core.documents import Document
from models.rag_state import RAGState
from config.settings import MAX_SYNTHESIS_DOCS
from config.logging_config import log_enh
from config.llm_instances import llm_verify
from prompts.verify_prompts import VERIFY_PROMPT
from synthesis.synthesizer import synthesize

USE_VERIFIER = False  # Disable verifier for performance

PROJECT_RE = re.compile(r'\d{2}-\d{2}-\d{3,4}')


def _group_docs_by_project(docs: List[Document]):
    """Group documents by project ID"""
    proj_to_docs, order = {}, []
    for d in docs or []:
        md = d.metadata or {}
        p = md.get("drawing_number") or md.get("project_key")
        if not p:
            m = PROJECT_RE.search(d.page_content or "")
            p = m.group(0) if m else None
        if not p:
            continue
        if p not in proj_to_docs:
            proj_to_docs[p] = []
            order.append(p)
        proj_to_docs[p].append(d)
    return proj_to_docs, order


def _make_doc_index(docs: List[Document], max_per_project: int = 1, max_chars: int = 160) -> str:
    """Create a document index for verification"""
    proj_to_docs, order = _group_docs_by_project(docs)
    rows = []
    for p in order:
        d = proj_to_docs[p][0]
        md = d.metadata or {}
        page = md.get("page_id") or md.get("page") or "?"
        date = md.get("date") or md.get("issue_date") or md.get("signed_date") or ""
        snippet = (d.page_content or "").replace("\n", " ")[:max_chars]
        rows.append(f"{p} | page={page} | date={date} | {snippet}")
    return "\n".join(rows)


def _json_from_text(s: str) -> dict | None:
    """Parse JSON from text"""
    try:
        return json.loads(s)
    except Exception:
        return None


def node_verify(state: RAGState) -> dict:
    """Verify answer quality and fix if needed"""
    t_start = time.time()
    log_enh.info(">>> VERIFY START")

    if not USE_VERIFIER:
        t_elapsed = time.time() - t_start
        log_enh.info(f"Verification disabled - skipping")
        log_enh.info(f"<<< VERIFY DONE (skipped) in {t_elapsed:.2f}s")
        return {"needs_fix": False}

    try:
        doc_index = _make_doc_index(state.graded_docs)
        raw = llm_verify.invoke(VERIFY_PROMPT.format(
            q=state.user_query, a=state.final_answer or "", doc_index=doc_index or "(no docs)"
        )).content

        parsed = _json_from_text(raw) or {}
        needs_fix = bool(parsed.get("needs_fix"))
        selected = [str(p).strip() for p in (parsed.get("projects") or []) if str(p).strip()]

        if not needs_fix:
            t_elapsed = time.time() - t_start
            log_enh.info(f"<<< VERIFY DONE (no fix needed) in {t_elapsed:.2f}s")
            return {"needs_fix": False}

        proj_to_docs, _ = _group_docs_by_project(state.graded_docs)
        unknown = [pid for pid in selected if pid not in proj_to_docs]
        updates = {"needs_fix": bool(unknown)}

        forced_docs = [d for pid in selected for d in proj_to_docs.get(pid, [])]
        if forced_docs:
            pre_fetched_metadata = getattr(state, '_project_metadata', None)
            code_docs = getattr(state, '_code_docs', [])
            if code_docs:
                code_docs = code_docs[:MAX_SYNTHESIS_DOCS]
            
            data_sources = state.data_sources or {"project_db": True, "code_db": False, "coop_manual": False}
            project_db_enabled = data_sources.get("project_db", True)
            code_db_enabled = data_sources.get("code_db", False)
            coop_db_enabled = data_sources.get("coop_manual", False)
            
            coop_docs = getattr(state, '_coop_docs', [])
            if coop_docs:
                coop_docs = coop_docs[:MAX_SYNTHESIS_DOCS]
            
            enabled_count = sum([project_db_enabled, code_db_enabled, coop_db_enabled])
            
            if enabled_count > 1 and (code_docs or coop_docs):
                if project_db_enabled and forced_docs:
                    project_ans, project_cites = synthesize(
                        state.user_query, forced_docs, state.session_id, 
                        project_metadata=pre_fetched_metadata,
                        code_docs=None,
                        use_code_prompt=False,
                        coop_docs=None,
                        use_coop_prompt=False,
                        active_filters=getattr(state, 'active_filters', None)
                    )
                    updates.update({
                        "final_answer": project_ans,
                        "answer_citations": project_cites,
                        "graded_docs": forced_docs
                    })
                
                if code_db_enabled and code_docs:
                    code_ans, code_cites = synthesize(
                        state.user_query, [], state.session_id, 
                        project_metadata=None,
                        code_docs=code_docs,
                        use_code_prompt=True,
                        coop_docs=None,
                        use_coop_prompt=False,
                        active_filters=getattr(state, 'active_filters', None)
                    )
                    updates.update({
                        "code_answer": code_ans,
                        "code_citations": code_cites
                    })
                
                if coop_db_enabled and coop_docs:
                    coop_ans, coop_cites = synthesize(
                        state.user_query, [], state.session_id, 
                        project_metadata=None,
                        code_docs=None,
                        use_code_prompt=False,
                        coop_docs=coop_docs,
                        use_coop_prompt=True,
                        active_filters=getattr(state, 'active_filters', None)
                    )
                    updates.update({
                        "coop_answer": coop_ans,
                        "coop_citations": coop_cites
                    })
            elif code_docs and not project_db_enabled and not coop_db_enabled:
                code_ans, code_cites = synthesize(
                    state.user_query, [], state.session_id, 
                    project_metadata=None,
                    code_docs=code_docs,
                    use_code_prompt=True,
                    coop_docs=None,
                    use_coop_prompt=False,
                    active_filters=getattr(state, 'active_filters', None)
                )
                updates.update({
                    "code_answer": code_ans,
                    "code_citations": code_cites,
                    "graded_docs": []
                })
            elif coop_docs and not project_db_enabled and not code_db_enabled:
                coop_ans, coop_cites = synthesize(
                    state.user_query, [], state.session_id, 
                    project_metadata=None,
                    code_docs=None,
                    use_code_prompt=False,
                    coop_docs=coop_docs,
                    use_coop_prompt=True,
                    active_filters=getattr(state, 'active_filters', None)
                )
                updates.update({
                    "coop_answer": coop_ans,
                    "coop_citations": coop_cites,
                    "graded_docs": []
                })
            else:
                ans, cites = synthesize(
                    state.user_query, forced_docs, state.session_id, 
                    project_metadata=pre_fetched_metadata,
                    code_docs=code_docs if code_docs else None,
                    use_code_prompt=False,
                    coop_docs=coop_docs if coop_docs else None,
                    use_coop_prompt=False,
                    active_filters=getattr(state, 'active_filters', None)
                )
                updates.update({
                    "final_answer": ans,
                    "answer_citations": cites,
                    "graded_docs": forced_docs
                })

        t_elapsed = time.time() - t_start
        log_enh.info(f"<<< VERIFY DONE (fix={'needed' if unknown else 'applied'}) in {t_elapsed:.2f}s")
        return updates

    except Exception as e:
        log_enh.error(f"LLM verifier failed: {e}")
        t_elapsed = time.time() - t_start
        log_enh.info(f"<<< VERIFY DONE (with error) in {t_elapsed:.2f}s")
        return {"needs_fix": False}


def _verify_route(state: RAGState) -> str:
    """Route based on whether verification flagged issues"""
    return "fix" if getattr(state, "needs_fix", False) else "ok"

