"""
Retrieval Node
Retrieves documents from vector stores based on plan or query
"""
import time
from models.db_retrieval_state import DBRetrievalState
from config.settings import (
    MAX_SMART_RETRIEVAL_DOCS, MAX_LARGE_RETRIEVAL_DOCS,
    MAX_CODE_RETRIEVAL_DOCS
)
from config.logging_config import log_query
from nodes.DBRetrieval.KGdb.supabase_client import vs_smart, vs_large, vs_code, vs_coop
from nodes.DBRetrieval.KGdb.retrievers import (
    make_hybrid_retriever, make_code_hybrid_retriever, make_coop_hybrid_retriever,
    mmr_rerank_code, mmr_rerank_coop,
    extract_code_filenames_from_docs, get_all_available_code_filenames
)
from config.llm_instances import emb
from utils.plan_executor import execute_plan
try:
    from langgraph.types import interrupt
    from langgraph.errors import GraphInterrupt
except ImportError:
    # Fallback for older versions
    try:
        from langgraph.pregel import interrupt
        from langgraph.errors import GraphInterrupt
    except ImportError:
        # If neither works, we'll handle it
        interrupt = None
        GraphInterrupt = Exception


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


def node_retrieve(state: DBRetrievalState) -> dict:
    """Retrieve documents based on plan or direct query"""
    print("🔍 node_retrieve called")  # Diagnostic - always visible
    needs_retrieval = getattr(state, "needs_retrieval", True)
    retrieval_done = getattr(state, "retrieval_completed", False)
    print(f"   - needs_retrieval: {needs_retrieval}")
    print(f"   - retrieval_completed: {retrieval_done}")
    if retrieval_done:
        print("⏭️  SKIPPING RETRIEVAL: already completed")
        return {"retrieval_completed": True, "needs_retrieval": False}
    if needs_retrieval is False:
        print("⏭️  SKIPPING RETRIEVAL: not needed for this task")
        return {"retrieval_completed": True, "needs_retrieval": False}

    t_start = time.time()
    try:
        log_query.info(">>> RETRIEVE START")

        if state.query_plan and state.query_plan.get("steps"):
            print("✅ Using plan-based retrieval")  # Diagnostic
            
            # Check if we have approved filenames from previous rejection (resume path)
            approved_filenames = state.approved_code_filenames
            filename_filter = approved_filenames if approved_filenames else None
            
            # Note: execute_plan doesn't support filename filtering yet, so we'll handle it after
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
            code_db_enabled = data_sources.get("code_db", False)
            
            # CRITICAL: Store code_docs in result BEFORE interrupt so they're available on resume
            if code_docs:
                result["retrieved_code_docs"] = code_docs
                result["retrieved_code_filenames"] = extract_code_filenames_from_docs(code_docs)
            
            # Handle code verification for plan-based retrieval
            # Skip if already verified (resume path - when resuming, state will have code_verification_response set)
            if code_docs and code_db_enabled and state.code_verification_response is None:
                # Extract unique filenames from retrieved code docs
                retrieved_filenames = extract_code_filenames_from_docs(code_docs)
                
                if retrieved_filenames:
                    log_query.info(f"🔍 Code verification (plan): Retrieved {len(code_docs)} chunks from {len(retrieved_filenames)} codes")
                    
                    # Interrupt for human verification
                    verification_response = interrupt({
                        "type": "code_verification",
                        "question": f"I'm going to reference information from these building codes:",
                        "codes": retrieved_filenames,
                        "code_count": len(retrieved_filenames),
                        "chunk_count": len(code_docs)
                    })
                    
                    # Handle response (this code runs AFTER resume)
                    if verification_response == "approved" or verification_response is True:
                        log_query.info("✅ Code verification: APPROVED")
                        result["code_verification_response"] = "approved"
                        result["approved_code_filenames"] = retrieved_filenames
                    elif verification_response == "rejected" or verification_response is False:
                        log_query.info("❌ Code verification: REJECTED - fetching all available codes")
                        all_codes = get_all_available_code_filenames()
                        
                        # Interrupt again to let user select codes
                        selected_codes = interrupt({
                            "type": "code_selection",
                            "question": "Please select which building codes you'd like me to reference:",
                            "available_codes": all_codes,
                            "previously_retrieved": retrieved_filenames
                        })
                        
                        if isinstance(selected_codes, list) and selected_codes:
                            log_query.info(f"✅ User selected {len(selected_codes)} codes: {selected_codes}")
                            log_query.info(f"📋 Selected codes for retrieval: {', '.join(selected_codes[:5])}{'...' if len(selected_codes) > 5 else ''}")
                            # Re-retrieve with selected codes
                            code_retriever_filtered = make_code_hybrid_retriever(filename_filter=selected_codes)
                            code_docs = code_retriever_filtered(state.user_query, k=MAX_CODE_RETRIEVAL_DOCS)
                            
                            # Log which codes actually contributed documents
                            if code_docs:
                                actual_codes = extract_code_filenames_from_docs(code_docs)
                                log_query.info(f"📊 Retrieved {len(code_docs)} chunks from {len(actual_codes)} codes: {', '.join(actual_codes[:5])}{'...' if len(actual_codes) > 5 else ''}")
                            else:
                                log_query.warning(f"⚠️  No documents retrieved with selected codes: {selected_codes}")
                            if code_docs:
                                query_emb = emb.embed_query(state.user_query)
                                code_docs = mmr_rerank_code(code_docs, query_emb, lambda_=0.9, k=len(code_docs))
                            
                            result["retrieved_code_docs"] = code_docs
                            result["code_verification_response"] = "approved"
                            result["retrieved_code_filenames"] = selected_codes
                            result["approved_code_filenames"] = selected_codes
                            result["all_available_code_filenames"] = all_codes
                        else:
                            log_query.warning("⚠️  No codes selected by user")
                            result["retrieved_code_docs"] = []
                            result["code_verification_response"] = "rejected"
                            result["all_available_code_filenames"] = all_codes
            elif code_docs and code_db_enabled and state.code_verification_response == "approved":
                # Resume path: code already verified, use existing code_docs from result
                log_query.info("✅ Code verification: Already approved (resume path)")
                result["code_verification_response"] = "approved"
                result["approved_code_filenames"] = state.approved_code_filenames or result.get("retrieved_code_filenames", [])
            
            if code_docs and not project_db_enabled and not docs:
                log_query.info(f"📊 CODE-ONLY MODE (plan): Passing {len(code_docs)} code docs through grader pipeline")
                result["retrieved_docs"] = code_docs
                state._code_docs = code_docs

            t_elapsed = time.time() - t_start
            log_query.info(f"<<< RETRIEVE DONE in {t_elapsed:.2f}s")
            return {
                **result,
                "retrieval_completed": True,
                "needs_retrieval": False,
            }

        # Fallback to legacy retrieval when no plan is provided
        print("⚠️ Using legacy retrieval path (no plan)")  # Diagnostic
        log_query.info("Using legacy retrieval (no plan)")
        
        # Get data_sources from state (set by router) - include speckle_db in fallback
        data_sources = state.data_sources or {"project_db": True, "code_db": False, "coop_manual": False, "speckle_db": False}
        project_db_enabled = data_sources.get("project_db", True)
        code_db_enabled = data_sources.get("code_db", False)
        coop_db_enabled = data_sources.get("coop_manual", False)
        speckle_db_enabled = data_sources.get("speckle_db", False)
        
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
            # CRITICAL: When resuming from interrupt, node restarts from beginning
            # Check if we've already verified - if so, skip retrieval and return existing state
            if state.code_verification_response == "approved" and state.retrieved_code_docs:
                log_query.info("✅ Code already verified - using existing retrieved_code_docs from state")
                # Return existing verified code docs (state persists between resumes)
                return {
                    "retrieved_code_docs": state.retrieved_code_docs,
                    "code_verification_response": "approved",
                    "retrieved_code_filenames": state.retrieved_code_filenames or [],
                    "approved_code_filenames": state.approved_code_filenames or [],
                    "retrieval_completed": True,
                    "needs_retrieval": False,
                }
            
            # Check if we have approved filenames from previous rejection (resume path)
            approved_filenames = state.approved_code_filenames
            filename_filter = approved_filenames if approved_filenames else None
            
            try:
                if vs_code is not None:
                    code_retriever = make_code_hybrid_retriever(filename_filter=filename_filter)
                    code_docs = code_retriever(state.user_query, k=MAX_CODE_RETRIEVAL_DOCS)
                    if code_docs:
                        query_emb = emb.embed_query(state.user_query)
                        code_docs = mmr_rerank_code(code_docs, query_emb, lambda_=0.9, k=len(code_docs))
                    
                    # If we have code docs and haven't verified yet, interrupt for human approval
                    # Skip if already verified (resume path - when resuming, state will have code_verification_response set)
                    if code_docs and state.code_verification_response is None:
                        # Extract unique filenames from retrieved code docs
                        retrieved_filenames = extract_code_filenames_from_docs(code_docs)
                        
                        if retrieved_filenames:
                            log_query.info(f"🔍 Code verification: Retrieved {len(code_docs)} chunks from {len(retrieved_filenames)} codes")
                            log_query.info(f"📋 Codes to verify: {retrieved_filenames}")
                            
                            # Set pending flag before interrupt
                            # Interrupt for human verification
                            verification_response = interrupt({
                                "type": "code_verification",
                                "question": f"I'm going to reference information from these building codes:",
                                "codes": retrieved_filenames,
                                "code_count": len(retrieved_filenames),
                                "chunk_count": len(code_docs)
                            })
                            
                            # Handle response (approved/rejected)
                            # verification_response will be the value passed to Command(resume=...)
                            if verification_response == "approved" or verification_response is True:
                                log_query.info("✅ Code verification: APPROVED")
                                return {
                                    "retrieved_code_docs": code_docs,
                                    "code_verification_response": "approved",
                                    "retrieved_code_filenames": retrieved_filenames,
                                    "approved_code_filenames": retrieved_filenames,
                                    "retrieval_completed": True,
                                    "needs_retrieval": False,
                                }
                            elif verification_response == "rejected" or verification_response is False:
                                log_query.info("❌ Code verification: REJECTED - fetching all available codes")
                                # Get all available codes for user selection
                                all_codes = get_all_available_code_filenames()
                                log_query.info(f"📚 Found {len(all_codes)} total available codes")
                                
                                # Interrupt again to let user select codes
                                selected_codes = interrupt({
                                    "type": "code_selection",
                                    "question": "Please select which building codes you'd like me to reference:",
                                    "available_codes": all_codes,
                                    "previously_retrieved": retrieved_filenames
                                })
                                
                                # selected_codes should be a list of filenames
                                if isinstance(selected_codes, list) and selected_codes:
                                    log_query.info(f"✅ User selected {len(selected_codes)} codes: {selected_codes}")
                                    # Re-retrieve with selected codes
                                    code_retriever_filtered = make_code_hybrid_retriever(filename_filter=selected_codes)
                                    code_docs = code_retriever_filtered(state.user_query, k=MAX_CODE_RETRIEVAL_DOCS)
                                    if code_docs:
                                        query_emb = emb.embed_query(state.user_query)
                                        code_docs = mmr_rerank_code(code_docs, query_emb, lambda_=0.9, k=len(code_docs))
                                    
                                    return {
                                        "retrieved_code_docs": code_docs,
                                        "code_verification_response": "approved",
                                        "retrieved_code_filenames": selected_codes,
                                        "approved_code_filenames": selected_codes,
                                        "all_available_code_filenames": all_codes,
                                        "retrieval_completed": True,
                                        "needs_retrieval": False,
                                    }
                                else:
                                    log_query.warning("⚠️  No codes selected by user, proceeding with empty code docs")
                                    return {
                                        "retrieved_code_docs": [],
                                        "code_verification_response": "rejected",
                                        "retrieved_code_filenames": [],
                                        "all_available_code_filenames": all_codes,
                                        "retrieval_completed": True,
                                        "needs_retrieval": False,
                                    }
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
            return {
                "retrieved_docs": [],
                "retrieved_code_docs": [],
                "retrieved_coop_docs": [],
                "retrieval_completed": True,
                "needs_retrieval": False,
            }
        
        log_query.info(f"📊 TOTAL RETRIEVED: {len(project_docs)} project docs, {len(code_docs)} code docs, {len(coop_docs)} coop docs")
        
        _log_retrieved_chunks_detailed(retrieved, log_query)

        t_elapsed = time.time() - t_start
        log_query.info(f"<<< RETRIEVE DONE in {t_elapsed:.2f}s")
        
        result = {
            "retrieved_docs": retrieved,
            "retrieval_completed": True,
            "needs_retrieval": False,
        }
        if code_docs and project_db_enabled:
            result["retrieved_code_docs"] = code_docs
        if coop_docs and (project_db_enabled or code_db_enabled):
            result["retrieved_coop_docs"] = coop_docs
        
        return result
    except GraphInterrupt:
        # CRITICAL: Do NOT catch GraphInterrupt - let it propagate to LangGraph runtime
        # This is how interrupts pause execution. If we catch it, the graph continues incorrectly.
        raise
    except Exception as e:
        print(f"❌ node_retrieve failed: {e}")  # Diagnostic - always visible
        import traceback
        traceback.print_exc()  # Show full traceback
        log_query.error(f"node_retrieve failed: {e}")
        t_elapsed = time.time() - t_start
        log_query.info(f"<<< RETRIEVE DONE (with error) in {t_elapsed:.2f}s")
        return {
            "retrieved_docs": [],
            "retrieval_completed": True,
            "needs_retrieval": False,
        }
