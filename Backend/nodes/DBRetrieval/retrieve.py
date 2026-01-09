"""
Retrieval Node
Retrieves documents from vector stores based on plan or query
"""
import time
from models.rag_state import RAGState
from langchain_core.documents import Document
from config.settings import (
    MAX_SMART_RETRIEVAL_DOCS, MAX_LARGE_RETRIEVAL_DOCS,
    MAX_CODE_RETRIEVAL_DOCS
)
from config.logging_config import log_query
from utils.filters import extract_date_filters_from_query, create_sql_project_filter
from database.supabase_client import vs_smart, vs_large, vs_code, vs_coop
from database.retrievers import (
    make_hybrid_retriever, make_code_hybrid_retriever, make_coop_hybrid_retriever,
    mmr_rerank_code, mmr_rerank_coop
)
from config.llm_instances import emb
from database.speckle_retriever import get_speckle_mapping, list_projects_with_speckle_models
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
        
        # Get data_sources from state (set by router) - include speckle_db in fallback
        data_sources = state.data_sources or {"project_db": True, "code_db": False, "coop_manual": False, "speckle_db": False}
        project_db_enabled = data_sources.get("project_db", True)
        code_db_enabled = data_sources.get("code_db", False)
        coop_db_enabled = data_sources.get("coop_manual", False)
        speckle_db_enabled = data_sources.get("speckle_db", False)
        q_lower = (state.user_query or "").lower()
        smart_filters = extract_date_filters_from_query(
            state.user_query,
            project_filter=getattr(state, "project_filter", None),
            follow_up_context=None
        )
        sql_filters = create_sql_project_filter(smart_filters)
        state.active_filters = smart_filters
        speckle_requested = speckle_db_enabled or smart_filters.get("has_speckle") or ("speckle" in q_lower) or ("3d model" in q_lower) or ("3d design" in q_lower)
        
        project_docs = []
        code_docs = []
        coop_docs = []
        speckle_docs = []
        
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
                retriever = make_hybrid_retriever(project=None, sql_filters=sql_filters, route=route)
                project_docs = retriever(state.user_query, k=chunk_limit)
                print(f"✅ Legacy retrieval got {len(project_docs)} docs")  # Diagnostic
            except Exception as e:
                print(f"❌ Legacy retrieval failed: {e}")  # Diagnostic
                import traceback
                traceback.print_exc()
                log_query.error(f"❌ Project database retrieve failed ({route}): {e}")
                project_docs = []

            if speckle_requested:
                mapping_keys = {p.get("project_key") for p in list_projects_with_speckle_models()}
                if mapping_keys:
                    project_docs = [
                        d for d in project_docs
                        if ((d.metadata or {}).get("drawing_number") in mapping_keys)
                        or ((d.metadata or {}).get("project_key") in mapping_keys)
                    ]
                if getattr(state, "project_filter", None):
                    mapping = get_speckle_mapping(state.project_filter)
                    if mapping:
                        content = (
                            f"Speckle model found for Project {state.project_filter}: "
                            f"projectId={mapping.get('projectId')}, modelId={mapping.get('modelId')}"
                        )
                        if mapping.get("commitId"):
                            content += f", commitId={mapping.get('commitId')}"
                    else:
                        content = f"No Speckle model found for Project {state.project_filter} under current mapping/token."
                    speckle_docs.append(Document(
                        page_content=content,
                        metadata={
                            "drawing_number": state.project_filter,
                            "project_key": state.project_filter,
                            "title": "Speckle model mapping"
                        }
                    ))
                else:
                    all_mapped = list_projects_with_speckle_models()
                    if all_mapped:
                        lines = []
                        for entry in all_mapped:
                            line = (
                                f"Project {entry.get('project_key')} → projectId={entry.get('projectId')}, "
                                f"modelId={entry.get('modelId')}"
                            )
                            if entry.get("commitId"):
                                line += f", commitId={entry.get('commitId')}"
                            lines.append(line)
                        speckle_docs.append(Document(
                            page_content="Speckle models available:\n" + "\n".join(lines),
                            metadata={
                                "drawing_number": "SPECKLE",
                                "project_key": "SPECKLE",
                                "title": "Speckle projects with models"
                            }
                        ))
                    else:
                        speckle_docs.append(Document(
                            page_content="No Speckle models available under current mapping/token.",
                            metadata={
                                "drawing_number": "SPECKLE",
                                "project_key": "SPECKLE",
                                "title": "Speckle projects with models"
                            }
                        ))
        
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
            retrieved = project_docs + speckle_docs
        
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
