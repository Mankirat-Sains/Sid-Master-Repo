"""
Planning Node
Decomposes user query into executable plan
"""
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor
from models.rag_state import RAGState
from models.memory import get_conversation_context
from prompts.planner_prompts import PLANNER_PROMPT, planner_llm
from prompts.router_prompts import ROUTER_PROMPT, router_llm
from config.settings import PLANNER_PLAYBOOK
from config.logging_config import log_query, log_route
from utils.project_utils import detect_project_filter


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


def node_plan(state: RAGState) -> dict:
    """Planning node - decomposes query into executable plan"""
    t_start = time.time()
    log_query.info(">>> PLAN START")

    # OPTIMIZATION: Run Plan + Route LLM calls in parallel to save ~1s
    def plan_task():
        conversation_context = get_conversation_context(state.session_id, max_exchanges=2)
        if conversation_context:
            log_query.info("📖 Using conversation context for planning")

        full_prompt = PLANNER_PROMPT.format(
            q=state.user_query,
            playbook=PLANNER_PLAYBOOK,
            conversation_context=conversation_context or "(No prior conversation)"
        )
        return planner_llm.invoke(full_prompt).content.strip()

    def route_task():
        data_sources = state.data_sources or {"project_db": True, "code_db": False}
        project_db_enabled = data_sources.get("project_db", True)
        
        if not project_db_enabled:
            project_filter = detect_project_filter(state.user_query)
            log_route.info("⏭️  Skipping router - code database only mode")
            return {"data_route": None, "project_filter": project_filter}
        
        try:
            project_filter = detect_project_filter(state.user_query)
            choice = router_llm.invoke(
                ROUTER_PROMPT.format(q=state.user_query)
            ).content.strip().lower()
            allowed = {"smart", "large"}
            data_route = choice if choice in allowed else "smart"
            
            log_route.info(f"🎯 ROUTER DECISION: '{state.user_query[:50]}...' → '{choice}' → '{data_route}'")
            
            return {"data_route": data_route, "project_filter": project_filter}
        except Exception as e:
            log_route.error(f"Router failed: {e}")
            return {"data_route": None, "project_filter": None}

    # Run both LLM calls in parallel
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_plan = executor.submit(plan_task)
        future_route = executor.submit(route_task)

        raw = future_plan.result()
        route_result = future_route.result()

    # Store route result in state for node_route to return
    state._parallel_route_result = route_result

    # parse -> normalize -> store
    try:
        m = re.search(r"\{.*\}\s*$", raw, flags=re.S)
        json_str = m.group(0) if m else raw
        log_query.info(f"🔍 PLANNER RAW JSON: {json_str}")
        obj = json.loads(json_str)
    except Exception as e:
        log_query.error(f"Planner JSON parse failed: {e}\nRAW:\n{raw}")
        obj = {}

    plan = _normalize_plan(obj, fallback_q=state.user_query)

    log_query.info("🎯 PLANNING DETAILS:")
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

    subqueries = plan.get('subqueries', [state.user_query])
    log_query.info(f"🔍 SUBQUERIES FORMED ({len(subqueries)} total):")
    for i, subq in enumerate(subqueries, 1):
        log_query.info(f"   [{i}] {subq}")

    t_elapsed = time.time() - t_start
    log_query.info(f"<<< PLAN DONE in {t_elapsed:.2f}s (including parallel route)")

    # SEMANTIC INTELLIGENCE: Capture planning intelligence
    planning_intelligence = {
        "reasoning": plan.get("reasoning", ""),
        "complexity_assessment": _extract_complexity_from_reasoning(plan.get("reasoning", "")),
        "topics_explored": plan.get("subqueries", [state.user_query])[:5],
        "strategy_operations": [step.get("op") for step in plan.get("steps", [])],
        "extract_targets": [step.get("args", {}).get("target", "") for step in plan.get("steps", []) if step.get("op") == "EXTRACT"],
        "timestamp": time.time()
    }
    
    state._planning_intelligence = planning_intelligence
    
    return {
        "query_plan": plan,
        "expanded_queries": plan.get("subqueries", [state.user_query])
    }

