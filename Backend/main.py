"""
Main Entry Point for RAG System
Provides run_agentic_rag function and healthcheck
"""
import re
import time
from dataclasses import asdict
from typing import Dict, List, Optional
from models.rag_state import RAGState
from models.memory import (
    SESSION_MEMORY, MAX_CONVERSATION_HISTORY, MAX_SEMANTIC_HISTORY,
    intelligent_query_rewriter, update_focus_state, FOCUS_STATES
)
from graph.builder import build_graph
from config.settings import MAX_CITATIONS_DISPLAY, MAX_ROUTER_DOCS
from config.logging_config import log_query, log_vlm
from database import test_database_connection
from database.supabase_client import vs_smart, vs_large

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
        from nodes.DBRetrieval.image_nodes import describe_image_for_search
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

    # Combine question with image context for enhanced search
    enhanced_question = question + image_context if image_context else question

    # Intelligent query rewriting
    log_query.info(f"🎯 QUERY REWRITING INPUT: '{enhanced_question[:500]}...' (truncated)" if len(enhanced_question) > 500 else f"🎯 QUERY REWRITING INPUT: '{enhanced_question}'")
    rewritten_query, query_filters = intelligent_query_rewriter(enhanced_question, session_id)
    log_query.info(f"🎯 QUERY REWRITING OUTPUT: '{rewritten_query}'")
    log_query.info(f"🎯 QUERY FILTERS: {query_filters}")
    
    # Extract project filter from query_filters
    project_filter = None
    if query_filters.get("project_keys"):
        project_filter = query_filters["project_keys"][0]
        log_query.info(f"🎯 PROJECT FILTER FROM REWRITER: {project_filter}")
    
    base_query = rewritten_query
    log_query.info(f"🎯 FINAL QUERY FOR RAG: '{base_query}'")

    # Initialize RAGState - if data_sources is None, let the router decide
    # RAGState has a default_factory that provides fallback defaults, but router will override
    # We pass data_sources=None explicitly when we want router to decide
    if data_sources is None:
        # Don't set a default - let the router intelligently select based on query and user role
        # The router (in rag_router or route node) will set state.data_sources
        pass
    
    init = RAGState(
        session_id=session_id,
        user_query=base_query,
        query_plan=None, data_route=None,
        project_filter=project_filter,
        expanded_queries=[], retrieved_docs=[], graded_docs=[],
        db_result=None, final_answer=None,
        answer_citations=[], code_answer=None, code_citations=[],
        coop_answer=None, coop_citations=[],
        answer_support_score=0.0,
        corrective_attempted=False,
        data_sources=data_sources,  # None is OK - router will set it, or will use RAGState default
        images_base64=images_base64 if images_base64 else None,
        use_image_similarity=False,  # Image embedding disabled - using VLM description only
        query_intent=None
    )

    # Convert dataclass to dict - graph.invoke expects a dict, not a dataclass
    final = graph.invoke(asdict(init), config={"configurable": {"thread_id": session_id}})

    # Normalize dict vs. object - LangGraph can return either
    if isinstance(final, dict):
        final_state = RAGState(
            session_id=final.get("session_id", session_id),
            user_query=final.get("user_query", base_query),
            query_plan=final.get("query_plan"),
            data_route=final.get("data_route"),
            project_filter=final.get("project_filter"),
            expanded_queries=final.get("expanded_queries", []),
            retrieved_docs=final.get("retrieved_docs", []),
            graded_docs=final.get("graded_docs", []),
            db_result=final.get("db_result"),
            final_answer=final.get("final_answer"),
            answer_citations=final.get("answer_citations", []),
            code_answer=final.get("code_answer"),
            code_citations=final.get("code_citations", []),
            coop_answer=final.get("coop_answer"),
            coop_citations=final.get("coop_citations", []),
            answer_support_score=final.get("answer_support_score", 0.0),
            corrective_attempted=final.get("corrective_attempted", False),
            needs_fix=final.get("needs_fix", False),
            selected_projects=final.get("selected_projects", []),
            needs_clarification=final.get("needs_clarification", False),
            clarification_question=final.get("clarification_question"),
            images_base64=final.get("images_base64"),
            image_embeddings=final.get("image_embeddings"),
            image_similarity_results=final.get("image_similarity_results", []),
            use_image_similarity=final.get("use_image_similarity", False),
            query_intent=final.get("query_intent"),
            follow_up_questions=final.get("follow_up_questions", []),
            follow_up_suggestions=final.get("follow_up_suggestions", [])
        )
    else:
        final_state = final

    # Extract projects from answer text
    answer_text = final_state.final_answer or ""
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

    # Update conversation memory with sliding window
    session_data = SESSION_MEMORY.get(session_id, {})
    conversation_history = session_data.get("conversation_history", [])

    log_query.info("💾 UPDATING CONVERSATION MEMORY:")
    log_query.info(f"   Current history size: {len(conversation_history)} exchanges")

    # Append new exchange to conversation history
    answer_text = final_state.final_answer or ""
    if final_state.code_answer:
        answer_text = f"{answer_text}\n\n--- Code References ---\n\n{final_state.code_answer}"
    if final_state.coop_answer:
        answer_text = f"{answer_text}\n\n--- Training Manual References ---\n\n{final_state.coop_answer}"
    
    new_exchange = {
        "question": question,
        "answer": answer_text,
        "timestamp": time.time(),
        "projects": projects_in_answer
    }
    conversation_history.append(new_exchange)

    log_query.info(f"   Added new exchange:")
    log_query.info(f"      Q: {question[:100]}...")
    log_query.info(f"      A: {(answer_text or '')[:100]}...")
    log_query.info(f"      Projects in answer: {projects_in_answer}")

    # Maintain sliding window
    if len(conversation_history) > MAX_CONVERSATION_HISTORY:
        dropped = len(conversation_history) - MAX_CONVERSATION_HISTORY
        conversation_history = conversation_history[-MAX_CONVERSATION_HISTORY:]
        log_query.info(f"   ⚠️  Sliding window: Dropped {dropped} oldest exchange(s), keeping last {MAX_CONVERSATION_HISTORY}")

    log_query.info(f"   Final history size: {len(conversation_history)} exchanges")

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

    # Update session memory
    SESSION_MEMORY[session_id] = {
        "conversation_history": conversation_history,
        "project_filter": final_state.project_filter,
        "last_query": question,
        "last_answer": final_state.final_answer,
        "last_results": [r for r in result_items if r.get("project")],
        "selected_projects": final_state.selected_projects,
        "semantic_history": semantic_history,
        "last_semantic": current_semantic
    }

    log_query.info("   ✅ Session memory updated successfully")
    
    # Update focus state for intelligent query rewriting
    update_focus_state(
        session_id=session_id,
        query=question,
        projects=projects_in_answer,
        results_projects=final_state.selected_projects
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
    for d in (final_state.graded_docs or [])[:MAX_CITATIONS_DISPLAY]:
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
    return {
        "answer": final_state.final_answer,
        "code_answer": final_state.code_answer,
        "coop_answer": final_state.coop_answer,
        "support": round(final_state.answer_support_score, 3),
        "citations": final_state.answer_citations,
        "code_citations": final_state.code_citations,
        "coop_citations": final_state.coop_citations,
        "route": final_state.data_route,
        "project_filter": final_state.project_filter,
        "needs_clarification": False,
        "expanded_queries": final_state.expanded_queries[:MAX_ROUTER_DOCS],
        "latency_s": latency,
        "graded_preview": graded_preview,
        "plan": {
            "reasoning": plan_for_ui.get("reasoning", ""),
            "steps": plan_for_ui.get("steps", []),
            "subqueries": plan_for_ui.get("subqueries", []),
        },
        "image_similarity_results": final_state.image_similarity_results or [],
        "follow_up_questions": final_state.follow_up_questions or [],
        "follow_up_suggestions": final_state.follow_up_suggestions or [],
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

