"""
Plan Execution Utilities
Execute query plans and helper functions for grading/ranking
"""
import re
import time
from typing import List, Dict, Optional
from langchain_core.documents import Document
from models.rag_state import RAGState
from models.memory import SESSION_MEMORY
from config.settings import (
    MAX_RETRIEVAL_DOCS, MAX_SMART_RETRIEVAL_DOCS, MAX_LARGE_RETRIEVAL_DOCS,
    MAX_CODE_RETRIEVAL_DOCS, MAX_GRADED_DOCS
)
from config.logging_config import log_query, log_enh
from config.llm_instances import emb, llm_grader
from prompts.grading_prompts import BATCH_GRADE_PROMPT
from .filters import extract_date_filters_from_query, create_sql_project_filter
from .project_utils import (
    _group_by_project_all, requested_project_count, _infer_n_from_q
)
from database.retrievers import (
    make_hybrid_retriever, make_code_hybrid_retriever, make_coop_hybrid_retriever,
    mmr_rerank_supabase, mmr_rerank_code, mmr_rerank_coop
)
from database.project_metadata import fetch_project_metadata
from database.supabase_client import vs_code, vs_coop

# Dimension matching regex
DIM_Q_RE = re.compile(r'(\d{1,4})(?:\s*(?:\'|\u2019|ft)?)\s*[x×]\s*(\d{1,4})(?:\s*(?:\'|\u2019|ft)?)', re.I)
DIM_DOC_RE = re.compile(r'(\d{1,4})(?:\s*(?:\'|\u2019|ft)?)\s*[x×]\s*(\d{1,4})(?:\s*(?:\'|\u2019|ft)?)', re.I)


def _abs_int(x: str) -> int:
    """Extract integer from string"""
    try:
        return int(re.sub(r'\D', '', x))
    except:
        return 10**9


def _timeit(msg, fn, *a, **kw):
    """Time a function call"""
    t0 = time.time()
    log_enh.info(f">>> {msg} START")
    out = fn(*a, **kw)
    dt = time.time() - t0
    log_enh.info(f"<<< {msg} DONE in {dt:.2f}s")
    return out


def rerank_by_dimension_similarity(q: str, docs: List[Document]) -> List[Document]:
    """Rerank documents by dimension similarity to query"""
    m = DIM_Q_RE.search(q)
    if not m or not docs:
        return docs

    q_w, q_l = _abs_int(m.group(1)), _abs_int(m.group(2))

    def best_err(text: str) -> int:
        best = None
        for a, b in DIM_DOC_RE.findall(text or ""):
            w, l = _abs_int(a), _abs_int(b)
            e1 = abs(w - q_w) + abs(l - q_l)
            e2 = abs(w - q_l) + abs(l - q_w)
            e = min(e1, e2)
            best = e if best is None else min(best, e)
        return best if best is not None else 10**9

    scored = [(best_err(d.page_content[:2000]), i, d) for i, d in enumerate(docs)]
    scored.sort(key=lambda t: (t[0], t[1]))
    return [d for _, __, d in scored]


def self_grade(q: str, docs: List[Document]) -> List[Document]:
    """Grade documents for relevance"""
    if not docs:
        return []
    
    chunks_text = "\n\n".join([f"[{i}] {d.page_content[:500]}" for i, d in enumerate(docs, 1)])
    resp = _timeit("grader llm (batch)", llm_grader.invoke, BATCH_GRADE_PROMPT.format(q=q, chunks=chunks_text)).content.strip().lower()
    resp = llm_grader.invoke(BATCH_GRADE_PROMPT.format(q=q, chunks=chunks_text)).content.strip().lower()
    labels = [line.strip() for line in resp.splitlines() if line.strip()]
    
    keep = [d for d, lab in zip(docs, labels) if lab.startswith("y")]
    return docs[:5] + keep[:MAX_GRADED_DOCS-5]


def pick_top_n_projects(docs: List[Document], n: int, max_docs: int) -> List[Document]:
    """Keep documents from the first N distinct projects"""
    from collections import defaultdict
    proj_to_docs = defaultdict(list)
    proj_order = []
    for d in docs:
        proj = (d.metadata or {}).get("drawing_number") or (d.metadata or {}).get("project_key")
        if not proj: 
            continue
        if proj not in proj_to_docs:
            proj_order.append(proj)
        proj_to_docs[proj].append(d)

    chosen = proj_order[:max(0, n)]
    out = []
    for p in chosen:
        out.extend(proj_to_docs[p])
        if len(out) >= max_docs:
            break
    return out[:max_docs]


def execute_plan(state: RAGState) -> dict:
    """Execute the query plan steps"""
    steps = (state.query_plan or {}).get("steps", [])
    if not steps:
        return {}

    working: List[Document] = []
    selected_projects: List[str] = []

    log_query.info(f"🔧 EXECUTE_PLAN: Starting with {len(steps)} steps")

    for step_idx, s in enumerate(steps, 1):
        op = (s.get("op") or "").upper()
        args = s.get("args") or {}
        log_query.info(f"🔧 EXECUTING STEP {step_idx}: op='{op}', args={args}")

        if op == "RETRIEVE":
            qlist = args.get("queries") or [state.user_query]
            k = int(args.get("k", MAX_RETRIEVAL_DOCS))
            
            # Get data_sources from state (set by router) - include speckle_db in fallback
            data_sources = state.data_sources or {"project_db": True, "code_db": False, "coop_manual": False, "speckle_db": False}
            project_db_enabled = data_sources.get("project_db", True)
            code_db_enabled = data_sources.get("code_db", False)
            coop_db_enabled = data_sources.get("coop_manual", False)
            speckle_db_enabled = data_sources.get("speckle_db", False)
            
            project_docs = []
            code_docs = []
            coop_docs = []
            
            # PROJECT DATABASE RETRIEVAL
            if project_db_enabled:
                if hasattr(state, 'data_route') and state.data_route:
                    route = state.data_route
                    if route == "smart":
                        k = min(k, MAX_SMART_RETRIEVAL_DOCS)
                    elif route == "large":
                        k = min(k, MAX_LARGE_RETRIEVAL_DOCS)
                    else:
                        k = min(k, MAX_SMART_RETRIEVAL_DOCS)
                        route = "smart"
                else:
                    route = "smart"
                    k = min(k, MAX_SMART_RETRIEVAL_DOCS)

                prior = SESSION_MEMORY.get(state.session_id, {})
                prev_query = prior.get("last_query")
                
                smart_filters = extract_date_filters_from_query(
                    state.user_query, 
                    project_filter=state.project_filter,
                    follow_up_context=prev_query
                )
                sql_filters = create_sql_project_filter(smart_filters)
                state.active_filters = smart_filters

                route = state.data_route if (hasattr(state, 'data_route') and state.data_route) else "smart"
                retr = make_hybrid_retriever(state.project_filter, sql_filters, route)
                project_docs = retr(state.user_query, k=k)
                
                if project_docs:
                    query_emb = emb.embed_query(state.user_query)
                    project_docs = mmr_rerank_supabase(project_docs, query_emb, lambda_=0.7, k=len(project_docs))
            
            # CODE DATABASE RETRIEVAL
            if code_db_enabled:
                try:
                    if vs_code is not None:
                        code_retriever = make_code_hybrid_retriever()
                        code_docs = code_retriever(state.user_query, k=MAX_CODE_RETRIEVAL_DOCS)
                        if code_docs:
                            query_emb = emb.embed_query(state.user_query)
                            code_docs = mmr_rerank_code(code_docs, query_emb, lambda_=0.9, k=len(code_docs))
                except Exception as e:
                    log_query.error(f"❌ Code database retrieve failed: {e}")
                    code_docs = []
            
            # COOP DATABASE RETRIEVAL
            if coop_db_enabled:
                try:
                    if vs_coop is not None:
                        coop_retriever = make_coop_hybrid_retriever()
                        coop_docs = coop_retriever(state.user_query, k=MAX_CODE_RETRIEVAL_DOCS)
                        if coop_docs:
                            query_emb = emb.embed_query(state.user_query)
                            coop_docs = mmr_rerank_coop(coop_docs, query_emb, lambda_=0.9, k=len(coop_docs))
                except Exception as e:
                    log_query.error(f"❌ Coop database retrieve failed: {e}")
                    coop_docs = []
            
            working = project_docs
            if code_docs:
                state._code_docs = code_docs
            if coop_docs:
                state._coop_docs = coop_docs

        elif op == "LIMIT_PROJECTS":
            n = args.get("n")
            if isinstance(n, str) and n.lower() == "infer":
                n = _infer_n_from_q(state.user_query, default_n=5)
            n = int(n or 5)
            
            selected_projects = []
            seen_projects = set()
            
            for doc in working:
                md = doc.metadata or {}
                project = md.get("drawing_number") or md.get("project_key")
                if project and project not in seen_projects:
                    selected_projects.append(project)
                    seen_projects.add(project)
                    if n != -1 and len(selected_projects) >= n:
                        break
            
            if n == -1:
                log_query.info(f"🔍 UNLIMITED QUERY: Using all {len(selected_projects)} available projects")
            else:
                log_query.info(f"🎯 LIMIT_PROJECTS: Selected {len(selected_projects)} projects: {selected_projects}")
            
            working = [d for d in working if
                      (d.metadata or {}).get("drawing_number") in selected_projects or
                      (d.metadata or {}).get("project_key") in selected_projects]
            
            if selected_projects:
                project_metadata = fetch_project_metadata(selected_projects)
                state._project_metadata = project_metadata
            else:
                state._project_metadata = {}

        elif op == "EXTRACT":
            state.query_plan["extract_target"] = args.get("target", "")

    execution_intelligence = {
        "operations_performed": [step.get("op", "") for step in steps],
        "selected_projects": selected_projects or state.selected_projects or [],
        "extract_targets": [step.get("args", {}).get("target", "") for step in steps if step.get("op") == "EXTRACT"],
        "doc_processing_flow": {
            "final_doc_count": len(working),
            "selected_project_count": len(selected_projects) if selected_projects else 0,
        },
        "data_sources_used": {
            "project_db": state.data_sources.get("project_db", True) if state.data_sources else True,
            "code_db": state.data_sources.get("code_db", False) if state.data_sources else False,
            "coop_manual": state.data_sources.get("coop_manual", False) if state.data_sources else False
        },
        "scope_refinement": "project_limited" if selected_projects else "open_scope",
        "timestamp": time.time()
    }
    
    state._execution_intelligence = execution_intelligence

    code_docs = getattr(state, '_code_docs', [])
    coop_docs = getattr(state, '_coop_docs', [])
    
    result = {
        "selected_projects": selected_projects or state.selected_projects or [],
        "retrieved_docs": (working or [])[:MAX_GRADED_DOCS],
        "active_filters": getattr(state, 'active_filters', None)
    }
    
    if code_docs:
        result["retrieved_code_docs"] = code_docs[:MAX_GRADED_DOCS]
    if coop_docs:
        result["retrieved_coop_docs"] = coop_docs[:MAX_GRADED_DOCS]
    
    return result

