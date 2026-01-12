"""
Main Entry Point for RAG System
Provides run_agentic_rag function and healthcheck
"""
import os
import re
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Dict, List, Optional

from models.rag_state import RAGState
from models.memory import (
    SESSION_MEMORY,
    MAX_CONVERSATION_HISTORY,
    MAX_SEMANTIC_HISTORY,
    intelligent_query_rewriter,
    update_focus_state,
    FOCUS_STATES,
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
PROJECT_RE = re.compile(r"\d{2}-\d{2}-\d{3,4}")


def run_agentic_rag(
    question: str,
    session_id: str = "default",
    data_sources: Optional[Dict[str, bool]] = None,
    images_base64: Optional[List[str]] = None,
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
        log_vlm.info("🔍 No images provided")
    log_vlm.info("🔍" * 30)
    log_vlm.info("")

    # Log memory state
    prior = SESSION_MEMORY.get(session_id, {})
    log_query.info(f"=== SESSION MEMORY (session_id={session_id}) ===")
    if prior:
        messages = prior.get("messages", [])
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
    previous_state = None
    try:
        state_snapshot = graph.get_state({"configurable": {"thread_id": session_id}})
        if state_snapshot and state_snapshot.values:
            previous_state = state_snapshot.values
            log_query.info(f"📖 Loaded previous state from checkpointer for thread_id={session_id}")
            if previous_state.get("messages"):
                log_query.info(f"📖 Found {len(previous_state['messages'])} previous messages")
    except Exception as e:
        log_query.info(f"📖 No previous state found (first invocation): {e}")
        previous_state = None

    previous_messages = previous_state.get("messages", []) if previous_state else []

    # Combine question with image context for enhanced search
    enhanced_question = question + image_context if image_context else question

    # Intelligent query rewriting - NOW WITH MESSAGES
    log_query.info(
        f"🎯 QUERY REWRITING INPUT: '{enhanced_question[:500]}...' (truncated)"
        if len(enhanced_question) > 500
        else f"🎯 QUERY REWRITING INPUT: '{enhanced_question}'"
    )
    rewritten_query, query_filters = intelligent_query_rewriter(
        enhanced_question,
        session_id,
        messages=previous_messages,
    )
    log_query.info(f"🎯 QUERY REWRITING OUTPUT: '{rewritten_query}'")
    log_query.info(f"🎯 QUERY FILTERS: {query_filters}")

    project_filter = None
    if query_filters.get("project_keys"):
        project_filter = query_filters["project_keys"][0]
        log_query.info(f"🎯 PROJECT FILTER FROM REWRITER: {project_filter}")

    base_query = rewritten_query
    log_query.info(f"🎯 FINAL QUERY FOR RAG: '{base_query}'")

    init_messages = list(previous_messages) if previous_messages else []
    init_messages.append({"role": "user", "content": question})

    init_state = RAGState(
        session_id=session_id,
        user_query=base_query,
        original_question=question,
        project_filter=project_filter,
        messages=init_messages,
        data_sources=data_sources,
        images_base64=images_base64 if images_base64 else None,
        use_image_similarity=False,
        query_intent=None,
    )
    # Seed docgen-specific fields so doc nodes can read them safely
    init_state.selected_routers = []
    init_state.workflow = None
    init_state.desktop_policy = None
    init_state.task_type = None
    init_state.doc_type = None
    init_state.section_type = None
    init_state.doc_request = None
    init_state.requires_desktop_action = False
    init_state.desktop_action_plan = None
    init_state.output_artifact_ref = None
    init_state.doc_generation_result = None
    init_state.doc_generation_warnings = []

    durability_mode = os.getenv("CHECKPOINTER_DURABILITY", "exit").lower()
    final = graph.invoke(
        init_state.__dict__,
        config={"configurable": {"thread_id": session_id}},
        durability=durability_mode,
    )

    if isinstance(final, dict):
        final_state = SimpleNamespace(**final)
    else:
        final_state = final

    if not getattr(final_state, "messages", None):
        final_state.messages = init_messages

    workflow = getattr(final_state, "workflow", None)
    task_type = getattr(final_state, "task_type", None)
    branch = "docgen" if (workflow == "docgen" or task_type in {"doc_section", "doc_report"}) else "qa"
    log_query.info(
        f"ROUTE SUMMARY | workflow={workflow} | task_type={task_type} | branch={branch} | desktop_policy={getattr(final_state, 'desktop_policy', None)}"
    )

    # CSV logging for docgen runs
    if branch == "docgen":
        csv_path = os.getenv("DOCGEN_CSV_PATH")
        if not csv_path:
            base = Path(__file__).resolve().parent.parent
            csv_path = base / "info_retrieval" / "data" / "drafted_sections.csv"
        result = final_state.doc_generation_result or {}
        length_target = result.get("length_target") or {}
        min_chars = length_target.get("min_chars")
        max_chars = length_target.get("max_chars")
        draft_text = getattr(final_state, "final_answer", "") or ""
        citations = result.get("citations") or getattr(final_state, "answer_citations", []) or []
        warnings = getattr(final_state, "doc_generation_warnings", []) or result.get("warnings", []) or []
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
                execution_trace=getattr(final_state, "execution_trace", []) or [],
                warnings=warnings,
            )
            log_query.info(f"DOCGEN CSV append ok at {csv_path}")
        except Exception as exc:
            log_query.error(f"DOCGEN CSV append failed: {exc}")

    # Extract projects from answer text
    answer_text = getattr(final_state, "final_answer", "") or ""
    projects_in_answer = []
    seen_in_answer = set()
    for match in PROJECT_RE.finditer(answer_text):
        proj_id = match.group(0)
        if proj_id not in seen_in_answer:
            projects_in_answer.append(proj_id)
            seen_in_answer.add(proj_id)

    log_query.info(f"📋 Projects extracted from answer text: {projects_in_answer}")

    result_items = [{"project": proj_id} for proj_id in projects_in_answer]
    log_query.info(f"📋 Result items for entity resolution: {[r['project'] for r in result_items]}")

    # Update conversation memory with sliding window
    session_data = SESSION_MEMORY.get(session_id, {})
    conversation_history = session_data.get("conversation_history", [])

    log_query.info("💾 UPDATING CONVERSATION MEMORY:")
    log_query.info(f"   Current history size: {len(conversation_history)} exchanges")

    if getattr(final_state, "code_answer", None):
        answer_text = f"{answer_text}\n\n--- Code References ---\n\n{final_state.code_answer}"
    if getattr(final_state, "coop_answer", None):
        answer_text = f"{answer_text}\n\n--- Training Manual References ---\n\n{final_state.coop_answer}"

    new_exchange = {"question": question, "answer": answer_text, "timestamp": time.time()}
    conversation_history.append(new_exchange)
    if len(conversation_history) > MAX_CONVERSATION_HISTORY:
        dropped = len(conversation_history) - MAX_CONVERSATION_HISTORY
        conversation_history = conversation_history[-MAX_CONVERSATION_HISTORY:]
        log_query.info(f"   🧠 Conversation sliding window: Dropped {dropped} oldest exchange(s)")

    log_query.info(f"   New history size: {len(conversation_history)} exchanges")

    # Semantic intelligence capture
    current_semantic = {}
    if hasattr(final_state, "_planning_intelligence"):
        current_semantic["planning"] = final_state._planning_intelligence
        log_query.info(
            f"📊 CAPTURED PLANNING INTELLIGENCE: {final_state._planning_intelligence.get('complexity_assessment', 'unknown')}"
        )
    if hasattr(final_state, "_routing_intelligence"):
        current_semantic["routing"] = final_state._routing_intelligence
        log_query.info(
            f"📊 CAPTURED ROUTING INTELLIGENCE: {final_state._routing_intelligence.get('data_route', 'unknown')}"
        )
    if hasattr(final_state, "_execution_intelligence"):
        current_semantic["execution"] = final_state._execution_intelligence
        log_query.info(
            f"📊 CAPTURED EXECUTION INTELLIGENCE: {len(final_state._execution_intelligence.get('operations_performed', []))} operations"
        )

    semantic_history = session_data.get("semantic_history", [])
    if current_semantic:
        semantic_history.append(current_semantic)
        if len(semantic_history) > MAX_SEMANTIC_HISTORY:
            dropped = len(semantic_history) - MAX_SEMANTIC_HISTORY
            semantic_history = semantic_history[-MAX_SEMANTIC_HISTORY:]
            log_query.info(
                f"   🧠 Semantic sliding window: Dropped {dropped} oldest semantic record(s), keeping last {MAX_SEMANTIC_HISTORY}"
            )
    log_query.info(f"   🧠 Semantic history size: {len(semantic_history)} records")

    SESSION_MEMORY[session_id] = {
        "conversation_history": conversation_history,
        "project_filter": project_filter,
        "last_query": question,
        "last_answer": answer_text,
        "last_results": [r for r in result_items if r.get("project")],
        "selected_projects": getattr(final_state, "selected_projects", []),
        "semantic_history": semantic_history,
        "last_semantic": current_semantic,
        "messages": list(getattr(final_state, "messages", [])),
    }

    log_query.info("   ✅ Session memory updated (backward compatibility)")
    log_query.info("   ✅ Messages stored in state (persisted by checkpointer)")

    update_focus_state(
        session_id=session_id,
        query=question,
        projects=projects_in_answer,
        results_projects=getattr(final_state, "selected_projects", []),
    )

    if session_id in FOCUS_STATES:
        FOCUS_STATES[session_id]["last_answer_projects"] = projects_in_answer
        log_query.info(f"🎯 UPDATED LAST ANSWER PROJECTS: {projects_in_answer}")

    log_query.info("📊 FINAL MEMORY STATE:")
    log_query.info(f"   Session ID: {session_id}")
    log_query.info(f"   Total messages stored: {len(getattr(final_state, 'messages', []))}")
    all_projects = set()
    for msg in getattr(final_state, "messages", []):
        if msg.get("role") == "assistant":
            content = msg.get("content", "")
            for match in PROJECT_RE.finditer(content):
                all_projects.add(match.group(0))
    log_query.info(f"   Total unique projects in memory: {len(all_projects)}")
    log_query.info(f"   Current project filter: {getattr(final_state, 'project_filter', None) or 'None'}")

    latency = round(time.time() - t0, 2)

    graded_preview = []
    for d in (getattr(final_state, "graded_docs", None) or [])[:MAX_CITATIONS_DISPLAY]:
        md = d.metadata or {}
        graded_preview.append(
            {
                "project": md.get("drawing_number") or md.get("project_key"),
                "page": md.get("page_id") or md.get("page"),
                "title": md.get("title"),
                "content": d.page_content[:500] if d.page_content else "",
                "search_type": md.get("search_type", "unknown"),
            }
        )

    plan_for_ui = final_state.query_plan if isinstance(getattr(final_state, "query_plan", None), dict) else {}
    expanded_queries = getattr(final_state, "expanded_queries", []) or []
    if expanded_queries:
        expanded_queries = expanded_queries[:MAX_ROUTER_DOCS]

    if getattr(final_state, "needs_clarification", False):
        log_query.info(f"❓ Router requested clarification: {getattr(final_state, 'clarification_question', None)}")
        return {
            "answer": getattr(final_state, "clarification_question", "Which databases would you like me to search?"),
            "code_answer": None,
            "coop_answer": None,
            "support": 0.0,
            "citations": [],
            "code_citations": [],
            "coop_citations": [],
            "route": None,
            "project_filter": getattr(final_state, "project_filter", None),
            "needs_clarification": True,
        }

    return {
        "answer": getattr(final_state, "final_answer", None),
        "code_answer": getattr(final_state, "code_answer", None),
        "coop_answer": getattr(final_state, "coop_answer", None),
        "support": round(getattr(final_state, "answer_support_score", 0.0), 3),
        "citations": getattr(final_state, "answer_citations", []),
        "code_citations": getattr(final_state, "code_citations", []),
        "coop_citations": getattr(final_state, "coop_citations", []),
        "route": getattr(final_state, "data_route", None),
        "project_filter": getattr(final_state, "project_filter", None),
        "needs_clarification": False,
        "expanded_queries": expanded_queries,
        "latency_s": latency,
        "graded_preview": graded_preview,
        "plan": {
            "reasoning": plan_for_ui.get("reasoning", ""),
            "steps": plan_for_ui.get("steps", []),
            "subqueries": plan_for_ui.get("subqueries", []),
        },
        "image_similarity_results": getattr(final_state, "image_similarity_results", []) or [],
        "follow_up_questions": getattr(final_state, "follow_up_questions", []) or [],
        "follow_up_suggestions": getattr(final_state, "follow_up_suggestions", []) or [],
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

    supabase_status = {"vs_smart": vs_smart is not None, "vs_large": vs_large is not None, "project_info": project_db_status}

    return {"status": "healthy" if project_db_status else "degraded", "supabase": supabase_status}
