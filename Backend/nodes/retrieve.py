"""
Retrieval Node
Retrieves documents from vector stores based on plan or query
"""
import time
from models.rag_state import RAGState
from config.settings import (
    MAX_SMART_RETRIEVAL_DOCS, MAX_LARGE_RETRIEVAL_DOCS,
    MAX_CODE_RETRIEVAL_DOCS
)
from config.logging_config import log_query
from database.supabase_client import vs_smart, vs_large, vs_code, vs_coop
from database.retrievers import (
    make_hybrid_retriever, make_code_hybrid_retriever, make_coop_hybrid_retriever,
    mmr_rerank_code, mmr_rerank_coop
)
from config.llm_instances import emb
from utils.plan_executor import execute_plan


def _log_docs_summary(docs, logger, prefix: str = "Documents"):
    """Helper to log document retrieval/grading summary"""
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


def _log_retrieved_chunks_detailed(docs, logger):
    """Enhanced logging for retrieved chunks"""
    if not docs:
        print("📦 RETRIEVED CHUNKS: None")
        return

    from collections import defaultdict
    project_chunks = defaultdict(list)
    for d in docs:
        md = d.metadata or {}
        proj = md.get("drawing_number") or md.get("project_key") or "UNKNOWN"
        project_chunks[proj].append(d)

    unique_projects = list(project_chunks.keys())
    print(f"📦 RETRIEVED CHUNKS: {len(docs)} total from {len(unique_projects)} projects: {', '.join(unique_projects[:5])}{'...' if len(unique_projects) > 5 else ''}")


def node_retrieve(state: RAGState) -> dict:
    """Retrieve documents based on plan or direct query"""
    print("🔍 node_retrieve called")  # Diagnostic - always visible
    t_start = time.time()
    try:
        log_query.info(">>> RETRIEVE START")

        if state.query_plan and state.query_plan.get("steps"):
            print("✅ Using plan-based retrieval")  # Diagnostic
            result = execute_plan(state)
            docs = result.get("retrieved_docs", [])
            code_docs = result.get("retrieved_code_docs", [])
            coop_docs = result.get("retrieved_coop_docs", [])
            
            print(f"📊 Plan retrieval: {len(docs)} project docs, {len(code_docs)} code docs, {len(coop_docs)} coop docs")  # Diagnostic
            
            _log_docs_summary(docs, log_query, "Retrieved via plan (project)")
            if code_docs:
                _log_docs_summary(code_docs, log_query, "Retrieved via plan (code)")
            if coop_docs:
                _log_docs_summary(coop_docs, log_query, "Retrieved via plan (coop)")

            _log_retrieved_chunks_detailed(docs, log_query)
            if code_docs:
                _log_retrieved_chunks_detailed(code_docs, log_query)
            if coop_docs:
                _log_retrieved_chunks_detailed(coop_docs, log_query)

            data_sources = state.data_sources or {"project_db": True, "code_db": False}
            project_db_enabled = data_sources.get("project_db", True)
            
            if code_docs and not project_db_enabled and not docs:
                log_query.info(f"📊 CODE-ONLY MODE (plan): Passing {len(code_docs)} code docs through grader pipeline")
                result["retrieved_docs"] = code_docs
                state._code_docs = code_docs

            t_elapsed = time.time() - t_start
            log_query.info(f"<<< RETRIEVE DONE in {t_elapsed:.2f}s")
            return result

        # Fallback to legacy retrieval when no plan is provided
        print("⚠️ Using legacy retrieval path (no plan)")  # Diagnostic
        log_query.info("Using legacy retrieval (no plan)")
        
        data_sources = state.data_sources or {"project_db": True, "code_db": False, "coop_manual": False}
        project_db_enabled = data_sources.get("project_db", True)
        code_db_enabled = data_sources.get("code_db", False)
        coop_db_enabled = data_sources.get("coop_manual", False)
        
        project_docs = []
        code_docs = []
        coop_docs = []
        
        # PROJECT DATABASE RETRIEVAL - Use hybrid retriever instead of direct similarity_search
        if project_db_enabled:
            route = state.data_route if (state.data_route and state.data_route != "code") else "smart"
            
            if route == "smart":
                chunk_limit = MAX_SMART_RETRIEVAL_DOCS
            elif route == "large":
                chunk_limit = MAX_LARGE_RETRIEVAL_DOCS
            else:
                chunk_limit = MAX_SMART_RETRIEVAL_DOCS
                route = "smart"
            
            try:
                print(f"🔍 Legacy retrieval: route={route}, chunk_limit={chunk_limit}")  # Diagnostic
                # Use hybrid retriever instead of direct similarity_search to ensure RPC functions are used
                retriever = make_hybrid_retriever(project=None, sql_filters=None, route=route)
                project_docs = retriever(state.user_query, k=chunk_limit)
                print(f"✅ Legacy retrieval got {len(project_docs)} docs")  # Diagnostic
            except Exception as e:
                print(f"❌ Legacy retrieval failed: {e}")  # Diagnostic
                import traceback
                traceback.print_exc()
                log_query.error(f"❌ Project database retrieve failed ({route}): {e}")
                project_docs = []
        
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
        
        # Combine results
        if code_docs and not project_db_enabled and not coop_db_enabled:
            retrieved = code_docs
            state._code_docs = code_docs
        elif coop_docs and not project_db_enabled and not code_db_enabled:
            retrieved = coop_docs
            state._coop_docs = coop_docs
        else:
            retrieved = project_docs
        
        if not retrieved and not code_docs and not coop_docs:
            log_query.warning("⚠️  No documents retrieved from any enabled database")
            return {"retrieved_docs": [], "retrieved_code_docs": [], "retrieved_coop_docs": []}
        
        log_query.info(f"📊 TOTAL RETRIEVED: {len(project_docs)} project docs, {len(code_docs)} code docs, {len(coop_docs)} coop docs")
        
        _log_retrieved_chunks_detailed(retrieved, log_query)

        t_elapsed = time.time() - t_start
        log_query.info(f"<<< RETRIEVE DONE in {t_elapsed:.2f}s")
        
        result = {"retrieved_docs": retrieved}
        if code_docs and project_db_enabled:
            result["retrieved_code_docs"] = code_docs
        if coop_docs and (project_db_enabled or code_db_enabled):
            result["retrieved_coop_docs"] = coop_docs
        
        return result
    except Exception as e:
        print(f"❌ node_retrieve failed: {e}")  # Diagnostic - always visible
        import traceback
        traceback.print_exc()  # Show full traceback
        log_query.error(f"node_retrieve failed: {e}")
        t_elapsed = time.time() - t_start
        log_query.info(f"<<< RETRIEVE DONE (with error) in {t_elapsed:.2f}s")
        return {"retrieved_docs": []}

