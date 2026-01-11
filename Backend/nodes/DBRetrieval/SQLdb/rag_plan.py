"""
RAG Planning Node
Decomposes user query into executable plan (sub-node, runs in parallel with rag_router)
Also handles query rewriting (follow-up detection, pronoun resolution, context expansion)
"""
import json
import re
import time
from models.rag_state import RAGState
from models.memory import (
    get_conversation_context, 
    SESSION_MEMORY, 
    FOCUS_STATES,
    _extract_semantic_context_for_rewriter
)
from prompts.rag_planner_prompts import RAG_PLANNER_PROMPT, rag_planner_llm
from config.settings import PLANNER_PLAYBOOK
from config.logging_config import log_query


def _normalize_plan(raw: dict, fallback_q: str) -> dict:
    """Force a stable schema for the UI and executor"""
    plan = {} if not isinstance(raw, dict) else dict(raw)

    # 1) reasoning
    reasoning = plan.get("reasoning")
    if not isinstance(reasoning, str):
        reasoning = "No explicit reasoning provided."

    # 2) steps -> list of {op,args}
    steps_in = plan.get("steps") or []
    norm_steps = []
    for s in steps_in if isinstance(steps_in, list) else []:
        if not isinstance(s, dict):
            continue
        op = (s.get("op") or "").strip().upper()
        args = s.get("args") or {}
        if not isinstance(args, dict):
            args = {}
        if op:
            norm_steps.append({"op": op, "args": args})

    # minimal fallback so executor still works
    if not norm_steps:
        norm_steps = [
            {"op": "RETRIEVE", "args": {"queries": [fallback_q], "k": 333}},
        ]

    # 3) subqueries (derived for UI, safe even if absent)
    subqs = []
    for s in norm_steps:
        ql = s["args"].get("queries")
        if isinstance(ql, list):
            for q in ql:
                if isinstance(q, str) and q.strip():
                    subqs.append(q.strip())
    if not subqs:
        subqs = [fallback_q]

    return {"reasoning": reasoning, "steps": norm_steps, "subqueries": subqs}


def _extract_complexity_from_reasoning(reasoning: str) -> str:
    """Extract complexity assessment from planner reasoning"""
    reasoning_lower = reasoning.lower()
    
    if any(word in reasoning_lower for word in ["comprehensive", "extensive", "detailed", "all projects", "complete list"]):
        return "comprehensive_analysis"
    elif any(word in reasoning_lower for word in ["specific", "particular", "focused", "single project"]):
        return "focused_query"  
    elif any(word in reasoning_lower for word in ["compare", "comparison", "versus", "different"]):
        return "comparative_analysis"
    elif any(word in reasoning_lower for word in ["recent", "latest", "newest", "current"]):
        return "temporal_query"
    else:
        return "general_query"


def _combined_rewrite_and_plan(user_query: str, session_id: str, conversation_context: str, messages: list = None) -> tuple[str, dict, dict]:
    """
    Combined query rewriting and planning in a single LLM call.
    Uses full conversation history (messages) for intelligent context understanding.
    Returns (rewritten_query, query_filters, plan_dict)
    """
    # Guardrail: Extract explicit project IDs with regex
    explicit_ids = re.findall(r'\b\d{2}-\d{2}-\d{3,4}\b', user_query)
    if explicit_ids:
        log_query.info(f"🎯 EXPLICIT IDs DETECTED: {explicit_ids}")
        # If explicit IDs found, skip rewriting and create simple plan
        return user_query, {"project_keys": explicit_ids}, {
            "reasoning": f"Explicit project IDs detected: {explicit_ids}",
            "steps": [{"op": "RETRIEVE", "args": {"queries": [user_query], "k": 20}}],
            "subqueries": [user_query]
        }
    
    session_data = SESSION_MEMORY.get(session_id, {})
    semantic_context = _extract_semantic_context_for_rewriter(session_data)
    
    # Format prompt using the template from prompts folder
    # Pass conversation_context (formatted string) AND ensure it includes full history
    combined_prompt = RAG_PLANNER_PROMPT.format(
        user_query=user_query,
        focus_context_json=json.dumps({}, indent=2),  # Deprecated - using conversation_context instead
        recent_topics=semantic_context["recent_topics"],
        recent_complexity_patterns=semantic_context["recent_complexity_patterns"],
        last_route=semantic_context["last_route"],
        last_scope=semantic_context["last_scope"],
        conversation_context=conversation_context or "(No prior conversation)",
        playbook=PLANNER_PLAYBOOK
    )

    try:
        response = rag_planner_llm.invoke(combined_prompt).content.strip()
        log_query.info(f"🎯 COMBINED LLM RESPONSE: {response[:500]}...")
        
        # Parse JSON response
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
            else:
                result = json.loads(response)
        except json.JSONDecodeError:
            log_query.error(f"🎯 JSON PARSE ERROR: {response}")
            # Fallback: use original query and create simple plan
            return user_query, {}, {"reasoning": "Parse error", "steps": [{"op": "RETRIEVE", "args": {"queries": [user_query]}}], "subqueries": [user_query]}
        
        # Extract rewriting results
        rewriting = result.get("rewriting", {})
        confidence = rewriting.get("confidence", 0.0)
        is_followup = rewriting.get("is_followup", False)
        
        # Trust LLM's judgment - it has the full conversation context
        confidence_threshold = 0.85
        
        if is_followup and confidence >= confidence_threshold:
            rewritten_query = rewriting.get("rewritten_query", user_query)
            filters = rewriting.get("filters", {})
            
            # Trust LLM's project_keys extraction - it read the conversation history
            project_keys = filters.get("project_keys", [])
            if project_keys:
                log_query.info(f"🎯 LLM EXTRACTED PROJECTS FROM CONVERSATION: {project_keys}")
            
            log_query.info(f"🎯 FOLLOW-UP DETECTED: '{user_query}' → '{rewritten_query}'")
        else:
            rewritten_query = user_query
            filters = {}
            log_query.info(f"🎯 NON-FOLLOW-UP: Using original query (confidence={confidence:.2f})")
        
        # Handle explicit IDs (override if found)
        if explicit_ids:
            filters["project_keys"] = explicit_ids
            log_query.info(f"🎯 EXPLICIT IDs OVERRIDE: {explicit_ids}")
        
        log_query.info(f"🎯 QUERY REWRITER: {user_query} → {rewritten_query}")
        log_query.info(f"🎯 FILTERS: {filters}")
        
        # Extract planning results
        planning = result.get("planning", {})
        
        return rewritten_query, filters, planning
        
    except Exception as e:
        log_query.error(f"🎯 COMBINED REWRITE+PLAN ERROR: {e}")
        # Fallback
        return user_query, {}, {"reasoning": "Error", "steps": [{"op": "RETRIEVE", "args": {"queries": [user_query]}}], "subqueries": [user_query]}


def node_rag_plan(state: RAGState) -> dict:
    """
    RAG Planning node - rewrites query and decomposes into executable plan in a SINGLE LLM call.
    This runs in parallel with node_rag_router (both are sub-nodes called by the top-level plan node).
    """
    t_start = time.time()
    log_query.info(">>> RAG PLAN START (Combined Rewrite + Planning)")

    # CRITICAL: Use original_question for rewriting, not user_query
    # user_query is already rewritten by main.py, but we need to rewrite the ORIGINAL question
    # with full conversation context to properly understand follow-ups
    query_to_rewrite = getattr(state, 'original_question', None) or state.user_query
    log_query.info(f"🎯 QUERY INPUT (original): '{query_to_rewrite[:500]}...' (truncated)" if len(query_to_rewrite) > 500 else f"🎯 QUERY INPUT (original): '{query_to_rewrite}'")
    log_query.info(f"🎯 QUERY INPUT (already rewritten): '{state.user_query[:500]}...' (truncated)" if len(state.user_query) > 500 else f"🎯 QUERY INPUT (already rewritten): '{state.user_query}'")
    
    # Get conversation context - try state.messages first, then load from checkpointer if needed
    # CRITICAL: state.messages might be empty if state wasn't properly initialized with previous messages
    # We need to load from checkpointer to get the full conversation history
    messages = getattr(state, 'messages', None) or []
    
    # If state.messages is empty, try to load from checkpointer directly
    # This ensures we have conversation history even if state wasn't properly initialized
    if not messages:
        try:
            # Access the graph instance that's already built (from main.py)
            # This is safe because the graph is built at module level
            import sys
            main_module = sys.modules.get('main')
            if main_module and hasattr(main_module, 'graph'):
                graph_instance = main_module.graph
                state_snapshot = graph_instance.get_state({"configurable": {"thread_id": state.session_id}})
                if state_snapshot and state_snapshot.values:
                    messages = state_snapshot.values.get("messages", [])
                    if messages:
                        log_query.info(f"📖 Loaded {len(messages)} messages from checkpointer for rag_plan")
        except Exception as e:
            log_query.info(f"📖 Could not load messages from checkpointer: {e}")
    
    conversation_context = get_conversation_context(
        state.session_id, 
        max_exchanges=10,  # Show more exchanges for better context
        messages=messages if messages else None
    )
    if conversation_context:
        log_query.info("📖 Using conversation context")
    else:
        log_query.info("📖 No conversation context available")

    # Combined rewrite + planning in one LLM call
    # CRITICAL: Rewrite the ORIGINAL question with full conversation context
    # This ensures follow-up detection works properly
    rewritten_query, query_filters, plan_dict = _combined_rewrite_and_plan(
        query_to_rewrite,  # Use original question, not already-rewritten user_query
        state.session_id, 
        conversation_context or "(No prior conversation)",
        messages=messages if messages else None
    )
    
    log_query.info(f"🎯 QUERY REWRITING OUTPUT: '{rewritten_query}'")
    log_query.info(f"🎯 QUERY FILTERS: {query_filters}")
    
    # Extract project filter
    project_filter = None
    if query_filters.get("project_keys"):
        project_filter = query_filters["project_keys"][0]
        log_query.info(f"🎯 PROJECT FILTER: {project_filter}")

    # Normalize plan
    plan = _normalize_plan(plan_dict, fallback_q=rewritten_query)

    log_query.info("🎯 RAG PLANNING DETAILS:")
    log_query.info(f"   Reasoning: {plan.get('reasoning', 'N/A')}")
    log_query.info(f"   Number of steps: {len(plan.get('steps', []))}")

    for i, step in enumerate(plan.get('steps', []), 1):
        op = step.get('op', '?')
        args = step.get('args', {})
        log_query.info(f"   Step {i}: {op}")
        if args:
            for key, val in args.items():
                if key == 'queries' and isinstance(val, list):
                    log_query.info(f"      - {key}: {len(val)} queries")
                else:
                    log_query.info(f"      - {key}: {val}")

    subqueries = plan.get('subqueries', [rewritten_query])
    log_query.info(f"🔍 SUBQUERIES FORMED ({len(subqueries)} total):")
    for i, subq in enumerate(subqueries, 1):
        log_query.info(f"   [{i}] {subq}")

    t_elapsed = time.time() - t_start
    log_query.info(f"<<< RAG PLAN DONE in {t_elapsed:.2f}s")

    # SEMANTIC INTELLIGENCE: Capture planning intelligence
    planning_intelligence = {
        "reasoning": plan.get("reasoning", ""),
        "complexity_assessment": _extract_complexity_from_reasoning(plan.get("reasoning", "")),
        "topics_explored": plan.get("subqueries", [rewritten_query])[:5],
        "strategy_operations": [step.get("op") for step in plan.get("steps", [])],
        "extract_targets": [step.get("args", {}).get("target", "") for step in plan.get("steps", []) if step.get("op") == "EXTRACT"],
        "timestamp": time.time()
    }
    
    state._planning_intelligence = planning_intelligence
    
    return {
        "user_query": rewritten_query,  # Update state with rewritten query
        "project_filter": project_filter,  # Set project filter from rewriting
        "query_plan": plan,
        "expanded_queries": plan.get("subqueries", [rewritten_query])
    }
