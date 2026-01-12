"""
Main Entry Point for RAG System
Provides run_agentic_rag function and healthcheck
"""
import re
import time
from dataclasses import asdict
from typing import Dict, List, Optional
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
        messages = prior.get('messages', [])
        log_query.info(f"  messages: {len(messages)} messages ({len(messages) // 2} exchanges)")
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

    # Load previous state from checkpointer (if exists) to get messages
    # This allows us to maintain conversation context across invocations
    previous_state = None
    try:
        # Get the latest checkpoint state for this thread
        state_snapshot = graph.get_state({"configurable": {"thread_id": session_id}})
        if state_snapshot and state_snapshot.values:
            previous_state = state_snapshot.values
            log_query.info(f"📖 Loaded previous state from checkpointer for thread_id={session_id}")
            if previous_state.get("messages"):
                log_query.info(f"📖 Found {len(previous_state['messages'])} previous messages")
    except Exception as e:
        # No previous state exists (first invocation) - this is fine
        log_query.info(f"📖 No previous state found (first invocation): {e}")
        previous_state = None
    
    # Get messages from previous state for query rewriting
    previous_messages = previous_state.get("messages", []) if previous_state else []

    # Combine question with image context for enhanced search
    enhanced_question = question + image_context if image_context else question

    # Intelligent query rewriting - NOW WITH MESSAGES
    log_query.info(f"🎯 QUERY REWRITING INPUT: '{enhanced_question[:500]}...' (truncated)" if len(enhanced_question) > 500 else f"🎯 QUERY REWRITING INPUT: '{enhanced_question}'")
    rewritten_query, query_filters = intelligent_query_rewriter(
        enhanced_question, 
        session_id,
        messages=previous_messages
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

    # Initialize RAGState - if data_sources is None, let the router decide
    # RAGState has a default_factory that provides fallback defaults, but router will override
    # We pass data_sources=None explicitly when we want router to decide
    if data_sources is None:
        # Don't set a default - let the router intelligently select based on query and user role
        # The router (in rag_router or route node) will set state.data_sources
        pass
    
    # Initialize messages from previous state if available
    # CRITICAL: Add the NEW user message to the state BEFORE invoking the graph
    # This ensures nodes like rag_plan can see the current user question in the conversation context
    init_messages = list(previous_messages) if previous_messages else []
    
    # Add the current user message to the conversation history
    # This is what LangGraph expects - the new message should be in state before processing
    init_messages.append({
        "role": "user",
        "content": question  # Use original question, not rewritten query
    })
    
    init = ParentState(
        session_id=session_id,
        user_query=base_query,  # Rewritten query for retrieval
        original_question=question,  # Original question (already added to messages above)
        images_base64=images_base64 if images_base64 else None,
        messages=init_messages,  # Includes previous messages + new user message
        selected_routers=[],  # Will be set by plan node
        # Results will be populated by subgraphs
        db_retrieval_result=None,
        webcalcs_result=None,
        desktop_result=None,
        build_model_result=None,
    )
    
    log_query.info(f"📖 Initialized messages: {len(previous_messages) if previous_messages else 0} previous + 1 new = {len(init_messages)} total")
    
    # Convert dataclass to dict - graph.invoke expects a dict, not a dataclass
    # Use "exit" durability mode to only save final state (not after each node)
    # This reduces storage by ~85% - only 1 checkpoint per query instead of 7+
    import os
    durability_mode = os.getenv("CHECKPOINTER_DURABILITY", "exit").lower()
    # CRITICAL: durability is a DIRECT parameter, not in config dict!
    final = graph.invoke(
        asdict(init), 
        config={"configurable": {"thread_id": session_id}},
        durability=durability_mode  # "exit" = only save at end, "async"/"sync" = save after each node
    )

    # Normalize dict vs. object - LangGraph can return either
    if isinstance(final, dict):
        final_state = ParentState(
            session_id=final.get("session_id", session_id),
            user_query=final.get("user_query", base_query),
            original_question=final.get("original_question", question),
            messages=final.get("messages", init.messages if hasattr(init, 'messages') else []),
            selected_routers=final.get("selected_routers", []),
            images_base64=final.get("images_base64"),
            db_retrieval_result=final.get("db_retrieval_result"),
            webcalcs_result=final.get("webcalcs_result"),
            desktop_result=final.get("desktop_result"),
            build_model_result=final.get("build_model_result"),
        )
    else:
        final_state = final
        # Ensure messages is set
        if not hasattr(final_state, 'messages') or not final_state.messages:
            final_state.messages = init.messages if hasattr(init, 'messages') else []

    # Extract projects from answer text
    # Get answer from db_retrieval_result (which contains final_answer from DBRetrieval subgraph)
    answer_text = final_state.db_retrieval_result or ""
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

    # NOTE: Messages are updated by the 'correct' node (which runs last in the graph)
    # The correct node already adds the new messages and persists them via checkpointer
    # We don't need to update it here again - that would cause duplication!
    # The messages in final_state are already updated by correct.py
    
    messages = list(final_state.messages or [])
    log_query.info(f"💾 Messages from correct node: {len(messages)} messages")
    
    # Verify the messages were updated correctly by correct node
    if messages:
        last_message = messages[-1]
        log_query.info(f"   Last message role: {last_message.get('role', '')}")
        log_query.info(f"   Last message content: {last_message.get('content', '')[:100]}...")

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

    # NOTE: Messages are now stored in state (persisted by checkpointer)
    # We keep SESSION_MEMORY for backward compatibility with existing code that reads from it
    # TODO: Migrate all code to use state.messages instead of SESSION_MEMORY
    SESSION_MEMORY[session_id] = {
        "messages": messages,  # Store messages in SESSION_MEMORY for backward compatibility
        "project_filter": None,  # No longer in ParentState, would need to be passed if needed
        "last_query": question,
        "last_answer": final_state.db_retrieval_result,
        "last_results": [r for r in result_items if r.get("project")],
        "selected_projects": final_state.db_retrieval_selected_projects,
        "semantic_history": semantic_history,
        "last_semantic": current_semantic
    }

    log_query.info("   ✅ Session memory updated (backward compatibility)")
    log_query.info("   ✅ Messages stored in state (persisted by checkpointer)")
    
    # Update focus state for intelligent query rewriting
    update_focus_state(
        session_id=session_id,
        query=question,
        projects=projects_in_answer,
        results_projects=final_state.db_retrieval_selected_projects
    )
    
    if session_id in FOCUS_STATES:
        FOCUS_STATES[session_id]["last_answer_projects"] = projects_in_answer
        log_query.info(f"🎯 UPDATED LAST ANSWER PROJECTS: {projects_in_answer}")

    # Log final memory state summary
    log_query.info("📊 FINAL MEMORY STATE:")
    log_query.info(f"   Session ID: {session_id}")
    log_query.info(f"   Total messages stored: {len(messages)} ({len(messages) // 2} exchanges)")
    # Extract projects from messages for logging
    all_projects = set()
    for msg in messages:
        if msg.get("role") == "assistant":
            content = msg.get("content", "")
            for match in PROJECT_RE.finditer(content):
                all_projects.add(match.group(0))
    log_query.info(f"   Total unique projects in memory: {len(all_projects)}")
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
            "project_filter": None,  # No longer in ParentState
            "needs_clarification": True
        }
    
    # Extract DBRetrieval results (all fields are now in db_retrieval_* fields)
    return {
        "answer": final_state.db_retrieval_result,
        "code_answer": final_state.db_retrieval_code_answer,
        "coop_answer": final_state.db_retrieval_coop_answer,
        "support": final_state.db_retrieval_support_score,
        "citations": final_state.db_retrieval_citations,
        "code_citations": final_state.db_retrieval_code_citations,
        "coop_citations": final_state.db_retrieval_coop_citations,
        "route": final_state.db_retrieval_route,
        "project_filter": None,  # No longer in ParentState (would need to be passed if needed)
        "needs_clarification": False,
        "expanded_queries": final_state.db_retrieval_expanded_queries,
        "latency_s": latency,
        "graded_preview": graded_preview,
        "plan": {
            "reasoning": "",
            "steps": [],
            "subqueries": [],
        },
        "image_similarity_results": final_state.db_retrieval_image_similarity_results,
        "follow_up_questions": final_state.db_retrieval_follow_up_questions,
        "follow_up_suggestions": final_state.db_retrieval_follow_up_suggestions,
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

