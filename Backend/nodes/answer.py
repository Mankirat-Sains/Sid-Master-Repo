"""
Answer Synthesis Node
Synthesizes final answers from graded documents
"""
from concurrent.futures import ThreadPoolExecutor
from langchain_core.documents import Document
from models.rag_state import RAGState
from config.settings import MAX_SYNTHESIS_DOCS
from config.logging_config import log_query, log_syn
from utils.plan_executor import (
    requested_project_count, pick_top_n_projects, rerank_by_dimension_similarity
)
from synthesis.synthesizer import synthesize


def node_answer(state: RAGState) -> dict:
    """Synthesize an answer with guardrails"""
    try:
        docs = list(state.graded_docs or [])

        # Lock the number of distinct projects if the user asked for N
        n = requested_project_count(state.user_query)
        if n:
            docs = pick_top_n_projects(docs, n=n, max_docs=MAX_SYNTHESIS_DOCS)

        if state.db_result and state.data_route in ("db", "hybrid"):
            docs.append(Document(
                page_content=f"[DB]\n{state.db_result}",
                metadata={"drawing_number": "DB", "page_id": "-"}
            ))

        # Check which databases are enabled
        data_sources = state.data_sources or {"project_db": True, "code_db": False, "coop_manual": False}
        project_db_enabled = data_sources.get("project_db", True)
        code_db_enabled = data_sources.get("code_db", False)
        coop_db_enabled = data_sources.get("coop_manual", False)
        
        # Get code docs from state
        code_docs = list(state.graded_code_docs or [])
        if not code_docs:
            code_docs = list(state.retrieved_code_docs or [])
        if not code_docs:
            code_docs = getattr(state, '_code_docs', [])
        
        # Get coop docs from state
        coop_docs = list(state.graded_coop_docs or [])
        if not coop_docs:
            coop_docs = list(state.retrieved_coop_docs or [])
        if not coop_docs:
            coop_docs = getattr(state, '_coop_docs', [])
        
        if code_docs:
            code_docs = code_docs[:MAX_SYNTHESIS_DOCS]
            log_query.info(f"🔍 Found {len(code_docs)} code docs for synthesis")
        
        if coop_docs:
            coop_docs = coop_docs[:MAX_SYNTHESIS_DOCS]
            log_query.info(f"🔍 Found {len(coop_docs)} coop docs for synthesis")
        
        # Handle code-only mode
        if not code_docs and code_db_enabled and not project_db_enabled and not coop_db_enabled and docs:
            code_docs = docs[:MAX_SYNTHESIS_DOCS]
            docs = []
            log_query.info(f"🔍 CODE-ONLY MODE: Using graded_docs ({len(code_docs)} docs) as code_docs")
        
        # Handle coop-only mode
        if not coop_docs and coop_db_enabled and not project_db_enabled and not code_db_enabled and docs:
            coop_docs = docs[:MAX_SYNTHESIS_DOCS]
            docs = []
            log_query.info(f"🔍 COOP-ONLY MODE: Using graded_docs ({len(coop_docs)} docs) as coop_docs")
        
        # Count how many databases are enabled
        enabled_count = sum([project_db_enabled, code_db_enabled, coop_db_enabled])
        
        # Synthesize separately if multiple databases are enabled
        if enabled_count > 1 and (code_docs or coop_docs):
            log_query.info(f"🔍 MULTI-DB MODE: Synthesizing separately in parallel - {len(docs)} project docs, {len(code_docs)} code docs, {len(coop_docs)} coop docs")
            
            pre_fetched_metadata = getattr(state, '_project_metadata', None)
            
            def synthesize_project():
                if not project_db_enabled or not docs:
                    return None, []
                log_query.info("Starting project synthesis...")
                project_ans, project_cites = synthesize(
                    state.user_query, 
                    docs, 
                    state.session_id, 
                    project_metadata=pre_fetched_metadata,
                    code_docs=None,
                    use_code_prompt=False,
                    coop_docs=None,
                    use_coop_prompt=False,
                    active_filters=getattr(state, 'active_filters', None)
                )
                return project_ans, project_cites
            
            def synthesize_code():
                if not code_db_enabled or not code_docs:
                    return None, []
                log_query.info("Starting code synthesis...")
                code_ans, code_cites = synthesize(
                    state.user_query, 
                    [], 
                    state.session_id, 
                    project_metadata=None,
                    code_docs=code_docs,
                    use_code_prompt=True,
                    coop_docs=None,
                    use_coop_prompt=False,
                    active_filters=getattr(state, 'active_filters', None)
                )
                return code_ans, code_cites
            
            def synthesize_coop():
                if not coop_db_enabled or not coop_docs:
                    return None, []
                log_query.info("Starting coop synthesis...")
                coop_ans, coop_cites = synthesize(
                    state.user_query, 
                    [], 
                    state.session_id, 
                    project_metadata=None,
                    code_docs=None,
                    use_code_prompt=False,
                    coop_docs=coop_docs,
                    use_coop_prompt=True,
                    active_filters=getattr(state, 'active_filters', None)
                )
                return coop_ans, coop_cites
            
            # Run synthesis tasks in parallel
            futures = {}
            with ThreadPoolExecutor(max_workers=3) as executor:
                if project_db_enabled and docs:
                    futures['project'] = executor.submit(synthesize_project)
                if code_db_enabled and code_docs:
                    futures['code'] = executor.submit(synthesize_code)
                if coop_db_enabled and coop_docs:
                    futures['coop'] = executor.submit(synthesize_coop)
                
                project_ans, project_cites = futures['project'].result() if 'project' in futures else (None, [])
                code_ans, code_cites = futures['code'].result() if 'code' in futures else (None, [])
                coop_ans, coop_cites = futures['coop'].result() if 'coop' in futures else (None, [])
            
            reranked = rerank_by_dimension_similarity(state.user_query, state.graded_docs) if project_db_enabled else []
            
            result = {"graded_docs": reranked}
            if project_ans:
                result["final_answer"] = project_ans
                result["answer_citations"] = project_cites
            if code_ans:
                result["code_answer"] = code_ans
                result["code_citations"] = code_cites
            if coop_ans:
                result["coop_answer"] = coop_ans
                result["coop_citations"] = coop_cites
            
            return result
        else:
            # Single answer mode (backward compatible)
            pre_fetched_metadata = getattr(state, '_project_metadata', None)
            
            # Handle single database modes
            if code_docs and not project_db_enabled and not coop_db_enabled:
                ans, cites = synthesize(state.user_query, [], state.session_id, 
                                      project_metadata=None,
                                      code_docs=code_docs,
                                      use_code_prompt=True,
                                      coop_docs=None,
                                      use_coop_prompt=False,
                                      active_filters=getattr(state, 'active_filters', None))
                return {"code_answer": ans, "code_citations": cites, "graded_docs": []}
            elif coop_docs and not project_db_enabled and not code_db_enabled:
                ans, cites = synthesize(state.user_query, [], state.session_id, 
                                      project_metadata=None,
                                      code_docs=None,
                                      use_code_prompt=False,
                                      coop_docs=coop_docs,
                                      use_coop_prompt=True,
                                      active_filters=getattr(state, 'active_filters', None))
                return {"coop_answer": ans, "coop_citations": cites, "graded_docs": []}
            else:
                ans, cites = synthesize(state.user_query, docs, state.session_id, 
                                       project_metadata=pre_fetched_metadata,
                                       code_docs=code_docs if code_docs else None,
                                       use_code_prompt=False,
                                       coop_docs=coop_docs if coop_docs else None,
                                       use_coop_prompt=False,
                                       active_filters=getattr(state, 'active_filters', None))
                reranked = rerank_by_dimension_similarity(state.user_query, state.graded_docs)
                
                return {"final_answer": ans, "answer_citations": cites, "graded_docs": reranked}
    except Exception as e:
        log_syn.error(f"Answer synthesis failed: {e}")
        return {"final_answer": "Error synthesizing answer", "answer_citations": []}

