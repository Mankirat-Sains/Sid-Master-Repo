"""
Main Entry Point for RAG System
Provides run_agentic_rag function and healthcheck
"""
import os
import re
import time
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Optional

from utils.path_setup import ensure_info_retrieval_on_path

ensure_info_retrieval_on_path()
from models.parent_state import ParentState
from models.memory import (
    SESSION_MEMORY, MAX_CONVERSATION_HISTORY, MAX_SEMANTIC_HISTORY,
    intelligent_query_rewriter, update_focus_state, FOCUS_STATES
)
from graph.builder import build_graph
from config.settings import MAX_CITATIONS_DISPLAY, MAX_ROUTER_DOCS
from config.logging_config import log_query, log_vlm
from nodes.DBRetrieval.KGdb import test_database_connection
from nodes.DBRetrieval.KGdb.supabase_client import vs_smart, vs_large
from utils.csv_logger import append_draft_csv

# Build graph once at module load and expose it for streaming
graph = build_graph()

# Project ID regex
PROJECT_RE = re.compile(r'\d{2}-\d{2}-\d{3,4}')


def run_agentic_rag(
    question: str,
    session_id: str = "default",
    data_sources: Optional[Dict[str, bool]] = None,
    images_base64: Optional[List[str]] = None
) -> Dict:
    """
    Main RAG entry point - runs the agentic RAG pipeline
    
    Args:
        question: User's question
        session_id: Session identifier for conversation memory
        data_sources: Dict specifying which databases to use
        images_base64: Optional list of base64-encoded images for VLM description (converted to text and used in search)
        
    Returns:
        Dict with answer, citations, and metadata
    """
    t0 = time.time()
    
    # Log image receipt at entry point
    log_vlm.info("")
    log_vlm.info("🔍" * 30)
    log_vlm.info(f"🔍 run_agentic_rag CALLED with images_base64={images_base64 is not None}")
    if images_base64:
        log_vlm.info(f"🔍 Image count: {len(images_base64)}")
        log_vlm.info(f"🔍 Image data lengths: {[len(img) for img in images_base64[:3]]} chars (first 3)")
    else:
        log_vlm.info(f"🔍 No images provided")
    log_vlm.info("🔍" * 30)
    log_vlm.info("")
    
    # Log memory state
    prior = SESSION_MEMORY.get(session_id, {})
    prev_q = prior.get("last_query")
    
    log_query.info(f"=== SESSION MEMORY (session_id={session_id}) ===")
    if prior:
        conv_history = prior.get('conversation_history', [])
        log_query.info(f"  conversation_history: {len(conv_history)} exchanges")
        log_query.info(f"  last_query: {prior.get('last_query')}")
        log_query.info(f"  project_filter: {prior.get('project_filter')}")
        log_query.info(f"  selected_projects: {prior.get('selected_projects')}")
        log_query.info(f"  last_results: {len(prior.get('last_results', []))} items")
    else:
        log_query.info("  No prior memory for this session")

    # Process images if provided - Convert to searchable text via VLM
    image_context = ""
    if images_base64 and len(images_base64) > 0:
        from nodes.DBRetrieval.SQLdb.image_nodes import describe_image_for_search
        log_vlm.info("")
        log_vlm.info("🔷" * 30)
        log_vlm.info(f"🖼️ PROCESSING {len(images_base64)} IMAGE(S) WITH VLM")
        log_vlm.info(f"📝 User question: {question[:150] if question else 'General image description'}")
        log_vlm.info("🔷" * 30)
        image_descriptions = []
        for i, image_base64 in enumerate(images_base64):
            log_vlm.info("")
            log_vlm.info(f"📸 Processing image {i+1}/{len(images_base64)}")
            try:
                image_description = describe_image_for_search(image_base64, question)
                image_descriptions.append(f"Image {i+1}: {image_description}")
                log_vlm.info(f"✅ Image {i+1} description completed successfully")
            except Exception as e:
                log_vlm.error(f"❌ VLM processing failed for image {i+1}, skipping: {e}")
        
        if image_descriptions:
            image_context = "\n\n[Image Context: " + " | ".join(image_descriptions) + "]"
            log_vlm.info("")
            log_vlm.info(f"📊 ALL IMAGES PROCESSED - Combined context length: {len(image_context)} chars")
            log_vlm.info("🔷" * 30)
            log_vlm.info("")

    # Load previous state from checkpointer (if exists) to get conversation history
    # This allows us to maintain conversation context across invocations
    previous_state = None
    try:
        # Get the latest checkpoint state for this thread
        state_snapshot = graph.get_state({"configurable": {"thread_id": session_id}})
        if state_snapshot and state_snapshot.values:
            previous_state = state_snapshot.values
            log_query.info(f"📖 Loaded previous state from checkpointer for thread_id={session_id}")
            if previous_state.get("conversation_history"):
                log_query.info(f"📖 Found {len(previous_state['conversation_history'])} previous exchanges")
    except Exception as e:
        # No previous state exists (first invocation) - this is fine
        log_query.info(f"📖 No previous state found (first invocation): {e}")
        previous_state = None
    
    # Get conversation history from previous state for query rewriting
    conversation_history_for_rewriter = previous_state.get("conversation_history", []) if previous_state else []

    # Combine question with image context for enhanced search
    enhanced_question = question + image_context if image_context else question

    # Intelligent query rewriting - NOW WITH CONVERSATION HISTORY
    log_query.info(f"🎯 QUERY REWRITING INPUT: '{enhanced_question[:500]}...' (truncated)" if len(enhanced_question) > 500 else f"🎯 QUERY REWRITING INPUT: '{enhanced_question}'")
    rewritten_query, query_filters = intelligent_query_rewriter(
        enhanced_question, 
        session_id,
        conversation_history=conversation_history_for_rewriter
    )
    log_query.info(f"🎯 QUERY REWRITING OUTPUT: '{rewritten_query}'")
    log_query.info(f"🎯 QUERY FILTERS: {query_filters}")
    
    # Extract project filter from query_filters
    project_filter = None
    if query_filters.get("project_keys"):
        project_filter = query_filters["project_keys"][0]
        log_query.info(f"🎯 PROJECT FILTER FROM REWRITER: {project_filter}")
    
    base_query = rewritten_query
    log_query.info(f"🎯 FINAL QUERY FOR RAG: '{base_query}'")

    init_state = ParentState(
        session_id=session_id,
        user_query=base_query,
        original_question=question,
        project_filter=project_filter,
        data_sources=data_sources,
        images_base64=images_base64 if images_base64 else None,
        conversation_history=conversation_history_for_rewriter,
        messages=previous_state.get("messages", []) if previous_state else [],
    )

    final = graph.invoke(asdict(init_state), config={"configurable": {"thread_id": session_id}})

    if isinstance(final, dict):
        final_state = ParentState(**asdict(init_state))
        for k, v in final.items():
            setattr(final_state, k, v)
    else:
        final_state = final

    if not getattr(final_state, "messages", None):
        final_state.messages = list(getattr(init_state, "messages", []))

    branch = "docgen" if (final_state.workflow == "docgen" or final_state.task_type in {"doc_section", "doc_report"}) else "qa"
    log_query.info(f"ROUTE SUMMARY | workflow={final_state.workflow} | task_type={final_state.task_type} | branch={branch} | desktop_policy={getattr(final_state, 'desktop_policy', None)}")

    # CSV logging for docgen runs
    if branch == "docgen":
        csv_path = os.getenv("DOCGEN_CSV_PATH")
        if not csv_path:
            base = Path(__file__).resolve().parent / "desktop_agent" / "info_retrieval"
            csv_path = base / "data" / "drafted_sections.csv"
        result = final_state.doc_generation_result or {}
        length_target = result.get("length_target") or {}
        min_chars = length_target.get("min_chars")
        max_chars = length_target.get("max_chars")
        draft_text = final_state.final_answer or ""
        citations = result.get("citations") or final_state.answer_citations or []
        warnings = final_state.doc_generation_warnings or result.get("warnings", []) or []
        length_actual = len(draft_text or "")
        try:
            append_draft_csv(
                csv_path=str(csv_path),
                request=question,
                doc_type=final_state.doc_type,
                section_type=final_state.section_type,
                min_chars=min_chars,
                max_chars=max_chars,
                length_actual=length_actual,
                draft_text=draft_text,
                citations=citations,
                execution_trace=final_state.execution_trace or [],
                warnings=warnings,
            )
            log_query.info(f"DOCGEN CSV append ok at {csv_path}")
        except Exception as exc:
            log_query.error(f"DOCGEN CSV append failed: {exc}")

    # Extract projects from answer text
    answer_text = (
        getattr(final_state, "final_answer", None)
        or getattr(final_state, "db_retrieval_result", "")
        or ""
    )
    projects_in_answer = []
    seen_in_answer = set()

    project_matches = PROJECT_RE.finditer(answer_text)
    for match in project_matches:
        proj_id = match.group(0)
        if proj_id not in seen_in_answer:
            projects_in_answer.append(proj_id)
            seen_in_answer.add(proj_id)

    log_query.info(f"📋 Projects extracted from answer text: {projects_in_answer}")

    # Build result items from ANSWER TEXT projects only
    result_items = []
    for proj_id in projects_in_answer:
        result_items.append({"project": proj_id})

    log_query.info(f"📋 Result items for entity resolution: {[r['project'] for r in result_items]}")

    # NOTE: Conversation history is updated by the 'correct' node (which runs last in the graph)
    # The correct node already adds the exchange to conversation_history and persists it via checkpointer
    # We don't need to update it here again - that would cause duplication!
    # The conversation_history in final_state is already updated by correct.py
    
    conversation_history = list(final_state.conversation_history or [])
    log_query.info(f"💾 Conversation history from correct node: {len(conversation_history)} exchanges")
    
    # Verify the conversation_history was updated correctly by correct node
    if conversation_history:
        last_exchange = conversation_history[-1]
        log_query.info(f"   Last exchange Q: {last_exchange.get('question', '')[:100]}...")
        log_query.info(f"   Last exchange projects: {last_exchange.get('projects', [])}")

    # SEMANTIC INTELLIGENCE: Gather semantic data from graph execution
    current_semantic = {}
    
    if hasattr(final_state, '_planning_intelligence'):
        current_semantic["planning"] = final_state._planning_intelligence
        log_query.info(f"📊 CAPTURED PLANNING INTELLIGENCE: {final_state._planning_intelligence.get('complexity_assessment', 'unknown')}")
    
    if hasattr(final_state, '_routing_intelligence'):
        current_semantic["routing"] = final_state._routing_intelligence
        log_query.info(f"📊 CAPTURED ROUTING INTELLIGENCE: {final_state._routing_intelligence.get('data_route', 'unknown')}")
    
    if hasattr(final_state, '_execution_intelligence'):
        current_semantic["execution"] = final_state._execution_intelligence
        log_query.info(f"📊 CAPTURED EXECUTION INTELLIGENCE: {len(final_state._execution_intelligence.get('operations_performed', []))} operations")
    
    # Get existing semantic history and manage sliding window
    session_data = SESSION_MEMORY.get(session_id, {})
    semantic_history = session_data.get("semantic_history", [])
    
    if current_semantic:
        semantic_history.append(current_semantic)
        
        if len(semantic_history) > MAX_SEMANTIC_HISTORY:
            dropped = len(semantic_history) - MAX_SEMANTIC_HISTORY
            semantic_history = semantic_history[-MAX_SEMANTIC_HISTORY:]
            log_query.info(f"   🧠 Semantic sliding window: Dropped {dropped} oldest semantic record(s), keeping last {MAX_SEMANTIC_HISTORY}")
    
    log_query.info(f"   🧠 Semantic history size: {len(semantic_history)} records")

    # NOTE: Conversation history is now stored in state (persisted by checkpointer)
    # We keep SESSION_MEMORY for backward compatibility with existing code that reads from it
    # TODO: Migrate all code to use state.conversation_history instead of SESSION_MEMORY
    SESSION_MEMORY[session_id] = {
        "conversation_history": conversation_history,
        "project_filter": getattr(final_state, "project_filter", project_filter),
        "last_query": question,
        "last_answer": answer_text,
        "last_results": [r for r in result_items if r.get("project")],
        "selected_projects": getattr(final_state, "selected_projects", []) or getattr(final_state, "db_retrieval_selected_projects", []),
        "semantic_history": semantic_history,
        "last_semantic": current_semantic,
    }

    log_query.info("   ✅ Session memory updated (backward compatibility)")
    log_query.info("   ✅ Conversation history stored in state (persisted by checkpointer)")
    
    # Update focus state for intelligent query rewriting
    update_focus_state(
        session_id=session_id,
        query=question,
        projects=projects_in_answer,
        results_projects=getattr(final_state, "selected_projects", []) or getattr(final_state, "db_retrieval_selected_projects", [])
    )
    
    if session_id in FOCUS_STATES:
        FOCUS_STATES[session_id]["last_answer_projects"] = projects_in_answer
        log_query.info(f"🎯 UPDATED LAST ANSWER PROJECTS: {projects_in_answer}")

    # Log final memory state summary
    log_query.info("📊 FINAL MEMORY STATE:")
    log_query.info(f"   Session ID: {session_id}")
    log_query.info(f"   Total exchanges stored: {len(conversation_history)}")
    log_query.info(f"   Total unique projects in memory: {len(set(p for ex in conversation_history for p in ex.get('projects', [])))}")
    log_query.info(f"   Current project filter: {final_state.project_filter or 'None'}")

    latency = round(time.time() - t0, 2)

    graded_preview = []
    graded_docs = getattr(final_state, "graded_docs", None) or []
    for d in graded_docs[:MAX_CITATIONS_DISPLAY]:
        md = d.metadata or {}
        graded_preview.append({
            "project": md.get("drawing_number") or md.get("project_key"),
            "page": md.get("page_id") or md.get("page"),
            "title": md.get("title"),
            "content": d.page_content[:500] if d.page_content else "",
            "search_type": md.get("search_type", "unknown"),
        })
    # Check if router needs clarification
    if final_state.needs_clarification:
        log_query.info(f"❓ Router requested clarification: {final_state.clarification_question}")
        return {
            "answer": final_state.clarification_question or "Which databases would you like me to search?",
            "code_answer": None,
            "coop_answer": None,
            "support": 0.0,
            "citations": [],
            "code_citations": [],
            "coop_citations": [],
            "route": None,
            "project_filter": final_state.project_filter,
            "needs_clarification": True
        }
    
    plan_for_ui = final_state.query_plan if isinstance(final_state.query_plan, dict) else {}
    expanded_queries = getattr(final_state, "expanded_queries", []) or getattr(final_state, "db_retrieval_expanded_queries", [])
    code_answer = getattr(final_state, "code_answer", None) or getattr(final_state, "db_retrieval_code_answer", None)
    coop_answer = getattr(final_state, "coop_answer", None) or getattr(final_state, "db_retrieval_coop_answer", None)
    citations = getattr(final_state, "answer_citations", []) or getattr(final_state, "db_retrieval_citations", [])
    code_citations = getattr(final_state, "code_citations", []) or getattr(final_state, "db_retrieval_code_citations", [])
    coop_citations = getattr(final_state, "coop_citations", []) or getattr(final_state, "db_retrieval_coop_citations", [])
    route = getattr(final_state, "data_route", None) or getattr(final_state, "db_retrieval_route", None)
    follow_up_questions = getattr(final_state, "follow_up_questions", []) or getattr(final_state, "db_retrieval_follow_up_questions", [])
    follow_up_suggestions = getattr(final_state, "follow_up_suggestions", []) or getattr(final_state, "db_retrieval_follow_up_suggestions", [])
    image_similarity_results = getattr(final_state, "image_similarity_results", []) or getattr(final_state, "db_retrieval_image_similarity_results", [])
    support_score = getattr(final_state, "answer_support_score", 0.0) or getattr(final_state, "db_retrieval_support_score", 0.0)

    return {
        "answer": answer_text or None,
        "code_answer": code_answer,
        "coop_answer": coop_answer,
        "support": round(support_score, 3),
        "citations": citations,
        "code_citations": code_citations,
        "coop_citations": coop_citations,
        "route": route,
        "project_filter": getattr(final_state, "project_filter", project_filter),
        "needs_clarification": False,
        "expanded_queries": expanded_queries[:MAX_ROUTER_DOCS] if expanded_queries else [],
        "latency_s": latency,
        "graded_preview": graded_preview,
        "plan": {
            "reasoning": plan_for_ui.get("reasoning", ""),
            "steps": plan_for_ui.get("steps", []),
            "subqueries": plan_for_ui.get("subqueries", []),
        },
        "image_similarity_results": image_similarity_results,
        "follow_up_questions": follow_up_questions,
        "follow_up_suggestions": follow_up_suggestions,
        "execution_trace": getattr(final_state, "execution_trace", []) or [],
        "workflow": getattr(final_state, "workflow", None),
        "task_type": getattr(final_state, "task_type", None),
        "doc_type": getattr(final_state, "doc_type", None),
        "section_type": getattr(final_state, "section_type", None),
        "doc_generation_warnings": getattr(final_state, "doc_generation_warnings", []) or [],
    }


def rag_healthcheck() -> Dict:
    """Health check for RAG system"""
    project_db_status = test_database_connection()

    supabase_status = {
        "vs_smart": vs_smart is not None,
        "vs_large": vs_large is not None,
        "project_info": project_db_status
    }

    return {
        "status": "healthy" if project_db_status else "degraded",
        "supabase": supabase_status,
    }
