"""
Routing Node
Routes query to smart or large database
"""
import time
from models.rag_state import RAGState
from prompts.router_prompts import ROUTER_PROMPT, router_llm
from config.logging_config import log_route
from utils.project_utils import detect_project_filter


def _get_route_reasoning(data_route: str) -> str:
    """Get reasoning for routing decision"""
    route_reasoning = {
        "smart": "granular_chunks_for_broad_search",
        "large": "detailed_chunks_for_deep_analysis", 
        "hybrid": "mixed_strategy_for_complex_query"
    }
    return route_reasoning.get(data_route, "default_routing")


def node_route(state: RAGState) -> dict:
    """Route query to the correct source with guardrails"""
    t_start = time.time()
    log_route.info(">>> ROUTE START")

    # Check if routing was already done in parallel during node_plan
    if hasattr(state, '_parallel_route_result'):
        route_result = state._parallel_route_result
        log_route.info(f"Using pre-computed route from parallel execution")
        log_route.info(f"Routing to {route_result.get('data_route')} (filter={route_result.get('project_filter')})")

        # SEMANTIC INTELLIGENCE: Capture routing intelligence 
        routing_intelligence = {
            "data_route": route_result.get('data_route'),
            "project_filter": route_result.get('project_filter'),
            "route_reasoning": _get_route_reasoning(route_result.get('data_route', 'smart')) if route_result.get('data_route') else "code_database_only",
            "scope_assessment": "filtered" if route_result.get('project_filter') else "open",
            "timestamp": time.time(),
            "source": "parallel_execution"
        }
        
        state._routing_intelligence = routing_intelligence

        t_elapsed = time.time() - t_start
        log_route.info(f"<<< ROUTE DONE in {t_elapsed:.2f}s (used cached result)")
        return route_result

    # Fallback: run routing if it wasn't done in parallel
    try:
        data_sources = state.data_sources or {"project_db": True, "code_db": False}
        project_db_enabled = data_sources.get("project_db", True)
        
        if not project_db_enabled:
            project_filter = detect_project_filter(state.user_query)
            log_route.info("⏭️  Skipping router - code database only mode")
            return {"data_route": None, "project_filter": project_filter}
        
        project_filter = detect_project_filter(state.user_query)
        choice = router_llm.invoke(
            ROUTER_PROMPT.format(q=state.user_query)
        ).content.strip().lower()
        allowed = {"smart", "large"}
        data_route = choice if choice in allowed else "smart"
        
        log_route.info(f"🎯 ROUTER DECISION: '{state.user_query[:50]}...' → '{choice}' → '{data_route}'")
        
        routing_intelligence = {
            "data_route": data_route,
            "project_filter": project_filter,
            "route_reasoning": _get_route_reasoning(data_route),
            "scope_assessment": "filtered" if project_filter else "open",
            "timestamp": time.time(),
            "source": "standalone_execution"
        }
        
        state._routing_intelligence = routing_intelligence

        t_elapsed = time.time() - t_start
        log_route.info(f"<<< ROUTE DONE in {t_elapsed:.2f}s")
        return {"data_route": data_route, "project_filter": project_filter}
    except Exception as e:
        log_route.error(f"Router failed: {e}")
        return {"data_route": None, "project_filter": None}

