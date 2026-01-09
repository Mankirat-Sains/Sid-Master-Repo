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
from langgraph.config import get_stream_writer
import re


def strip_markdown_image_links(text: str) -> str:
    """Remove markdown image syntax (![alt](url)) from text, keeping only the alt text."""
    # Pattern matches ![alt text](url) and replaces with just "alt text"
    pattern = r'!\[([^\]]*)\]\([^\)]+\)'
    return re.sub(pattern, r'\1', text)


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

        # Check which databases are enabled (set by router) - include speckle_db in fallback
        data_sources = state.data_sources or {"project_db": True, "code_db": False, "coop_manual": False, "speckle_db": False}
        project_db_enabled = data_sources.get("project_db", True)
        code_db_enabled = data_sources.get("code_db", False)
        coop_db_enabled = data_sources.get("coop_manual", False)
        speckle_db_enabled = data_sources.get("speckle_db", False)
        
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
            log_query.info(f"🔍 MULTI-DB MODE: Synthesizing separately - {len(docs)} project docs, {len(code_docs)} code docs, {len(coop_docs)} coop docs")
            
            pre_fetched_metadata = getattr(state, '_project_metadata', None)
            
            # Try to get stream writer for token streaming (must be in main context)
            try:
                writer = get_stream_writer()
                has_writer = True
                log_query.info("✅ Stream writer obtained for token streaming")
            except Exception as e:
                has_writer = False
                writer = None
                log_query.info(f"⚠️ Stream writer not available: {e}")
            
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
            
            # Start secondary synthesis (code/coop) in background threads
            futures = {}
            executor = ThreadPoolExecutor(max_workers=2)
            if code_db_enabled and code_docs:
                futures['code'] = executor.submit(synthesize_code)
            if coop_db_enabled and coop_docs:
                futures['coop'] = executor.submit(synthesize_coop)
            
            # Run project synthesis in main context WITH STREAMING
            # Always use streaming so LangGraph's messages mode can capture tokens
            project_ans, project_cites = None, []
            if project_db_enabled and docs:
                log_query.info("🔄 [ANSWER NODE MULTI-DB] Starting streaming synthesis...")
                ans_parts = []
                token_count = 0
                stream_result = synthesize(
                    state.user_query, 
                    docs, 
                    state.session_id,
                    stream=True,  # Always enable streaming for token capture
                    project_metadata=pre_fetched_metadata,
                    code_docs=None,
                    use_code_prompt=False,
                    coop_docs=None,
                    use_coop_prompt=False,
                    active_filters=getattr(state, 'active_filters', None),
                    image_results=state.image_similarity_results  # Pass images - LLM decides whether to include
                )
                first_chunk = True
                for chunk in stream_result:
                    if first_chunk and isinstance(chunk, tuple):
                        token_content, project_cites = chunk
                        ans_parts.append(token_content)
                        token_count += 1
                        # DO NOT emit via custom writer - tokens are already streamed via "messages" mode
                        # Emitting here causes duplication ("Project Project", etc.)
                        # LangGraph's messages mode automatically captures and streams LLM tokens
                        first_chunk = False
                    else:
                        ans_parts.append(chunk)
                        token_count += 1
                        # DO NOT emit via custom writer - tokens are already streamed via "messages" mode
                project_ans = "".join(ans_parts)
                log_query.info(f"✅ [ANSWER NODE MULTI-DB] Streaming synthesis complete - {token_count} tokens, {len(project_ans)} chars")
            
            # Wait for secondary synthesis to complete
            code_ans, code_cites = futures['code'].result() if 'code' in futures else (None, [])
            coop_ans, coop_cites = futures['coop'].result() if 'coop' in futures else (None, [])
            executor.shutdown(wait=False)  # Don't wait, we already have results
            
            reranked = rerank_by_dimension_similarity(state.user_query, state.graded_docs) if project_db_enabled else []
            
            # Log image results - LLM decides whether to include them in the answer
            log_query.info(f"🖼️ [ANSWER NODE] Passed {len(state.image_similarity_results)} images to synthesis prompt")
            log_query.info(f"🖼️ [ANSWER NODE] LLM will decide whether to include image URLs based on query intent")
            
            # Clean markdown image links from all answers
            if project_ans:
                project_ans = strip_markdown_image_links(project_ans)
            if code_ans:
                code_ans = strip_markdown_image_links(code_ans)
            if coop_ans:
                coop_ans = strip_markdown_image_links(coop_ans)
            
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
            # Always return image results to frontend for rendering
            result["image_similarity_results"] = state.image_similarity_results or []
            
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
                                      active_filters=getattr(state, 'active_filters', None),
                                      image_results=state.image_similarity_results)  # Pass images - LLM decides
                ans = strip_markdown_image_links(ans)  # Clean markdown image links
                return {
                    "code_answer": ans, 
                    "code_citations": cites, 
                    "graded_docs": [],
                    "image_similarity_results": state.image_similarity_results or []
                }
            elif coop_docs and not project_db_enabled and not code_db_enabled:
                ans, cites = synthesize(state.user_query, [], state.session_id, 
                                      project_metadata=None,
                                      code_docs=None,
                                      use_code_prompt=False,
                                      coop_docs=coop_docs,
                                      use_coop_prompt=True,
                                      active_filters=getattr(state, 'active_filters', None),
                                      image_results=state.image_similarity_results)  # Pass images - LLM decides
                ans = strip_markdown_image_links(ans)  # Clean markdown image links
                return {
                    "coop_answer": ans, 
                    "coop_citations": cites, 
                    "graded_docs": [],
                    "image_similarity_results": state.image_similarity_results or []
                }
            else:
                # Use streaming synthesis for real-time token delivery
                # Stream tokens via custom events while accumulating answer
                log_query.info("🔍 [ANSWER NODE] Attempting to get stream writer...")
                writer = None
                has_writer = False
                try:
                    writer = get_stream_writer()
                    has_writer = True
                    log_query.info("✅ [ANSWER NODE] Stream writer obtained successfully!")
                except RuntimeError as e:
                    # RuntimeError is thrown when not in streaming context
                    log_query.warning(f"⚠️ [ANSWER NODE] Stream writer RuntimeError: {e}")
                except Exception as e:
                    log_query.warning(f"⚠️ [ANSWER NODE] Stream writer failed with {type(e).__name__}: {e}")
                
                # ALWAYS use streaming synthesis so LangGraph's messages mode can capture tokens
                # Even without the custom writer, tokens will be streamed via messages mode
                log_query.info("🔄 [ANSWER NODE] Starting streaming synthesis (messages mode)...")
                ans_parts = []
                cites = []
                token_count = 0
                stream_result = synthesize(state.user_query, docs, state.session_id,
                                          stream=True,  # Always enable streaming for token capture
                                          project_metadata=pre_fetched_metadata,
                                          code_docs=code_docs if code_docs else None,
                                          use_code_prompt=False,
                                          coop_docs=coop_docs if coop_docs else None,
                                          use_coop_prompt=False,
                                          active_filters=getattr(state, 'active_filters', None),
                                          image_results=state.image_similarity_results)  # Pass images - LLM decides
                
                # Handle streaming generator
                first_chunk = True
                for chunk in stream_result:
                    if first_chunk and isinstance(chunk, tuple):
                        # First chunk contains (content, cites)
                        token_content, cites = chunk
                        ans_parts.append(token_content)
                        token_count += 1
                        # DO NOT emit via custom writer - tokens are already streamed via "messages" mode
                        # Emitting here causes duplication ("Project Project", etc.)
                        # LangGraph's messages mode automatically captures and streams LLM tokens
                        first_chunk = False
                    else:
                        # Subsequent chunks are just content
                        ans_parts.append(chunk)
                        token_count += 1
                        # DO NOT emit via custom writer - tokens are already streamed via "messages" mode
                
                ans = "".join(ans_parts)
                log_query.info(f"✅ [ANSWER NODE] Streaming synthesis complete - {token_count} tokens, {len(ans)} chars")
                
                # Clean markdown image links from answer
                ans = strip_markdown_image_links(ans)
                
                reranked = rerank_by_dimension_similarity(state.user_query, state.graded_docs)
                
                # Log image results - LLM decides whether to include them in the answer
                log_query.info(f"🖼️ [ANSWER NODE] Passed {len(state.image_similarity_results)} images to synthesis prompt")
                log_query.info(f"🖼️ [ANSWER NODE] LLM will decide whether to include image URLs based on query intent")
                
                return {
                    "final_answer": ans, 
                    "answer_citations": cites, 
                    "graded_docs": reranked,
                    # Always return image results to frontend for rendering
                    "image_similarity_results": state.image_similarity_results or []
                }
    except Exception as e:
        log_syn.error(f"Answer synthesis failed: {e}")
        return {"final_answer": "Error synthesizing answer", "answer_citations": []}

