"""
RAG Router Node
Routes query to appropriate databases and determines smart/large chunk selection for project_db.
This runs in parallel with node_rag_plan (both are sub-nodes called by the top-level plan node).

Handles selection among 4 databases:
- project_db (with smart/large chunking)
- code_db
- coop_manual (internal_docs_db)
- speckle_db
"""
import json
import re
import time
from models.db_retrieval_state import DBRetrievalState
from prompts.router_prompts import ROUTER_PROMPT, router_llm
from config.logging_config import log_route
from utils.project_utils import detect_project_filter
from utils.role_utils import format_role_preferences_for_router


def _get_route_reasoning(data_route: str) -> str:
    """Get reasoning for routing decision"""
    route_reasoning = {
        "smart": "granular_chunks_for_broad_search",
        "large": "detailed_chunks_for_deep_analysis", 
        "hybrid": "mixed_strategy_for_complex_query"
    }
    return route_reasoning.get(data_route, "default_routing")


def node_rag_router(state: DBRetrievalState) -> dict:
    """
    RAG Router - Routes query to appropriate databases and determines smart/large chunk selection for project_db.
    This runs in parallel with node_rag_plan (both are sub-nodes called by the top-level plan node).
    
    Uses the router prompt to select from 4 databases:
    - project_db (with smart/large chunking options)
    - code_db
    - coop_manual (internal_docs_db)
    - speckle_db
    """
    t_start = time.time()
    log_route.info(">>> RAG ROUTER START")

    try:
        project_filter = detect_project_filter(state.user_query)
        
        # Get role-based preferences for router prompt
        role_preferences_str = format_role_preferences_for_router(state.user_role)
        if state.user_role:
            log_route.info(f"👤 Using role-based routing for role: {state.user_role}")
        
        # Call router LLM with query and role information
        router_response = router_llm.invoke(
            ROUTER_PROMPT.format(q=state.user_query, role_preferences=role_preferences_str)
        ).content.strip()
        
        # Parse JSON response from router
        try:
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in router_response:
                json_str = router_response.split("```json")[1].split("```")[0].strip()
            elif "```" in router_response:
                json_str = router_response.split("```")[1].split("```")[0].strip()
            else:
                # Try to find JSON object in response
                json_match = re.search(r'\{.*\}', router_response, re.DOTALL)
                json_str = json_match.group(0) if json_match else router_response.strip()
            
            router_result = json.loads(json_str)
            
        except json.JSONDecodeError as e:
            log_route.error(f"Failed to parse router JSON: {e}\nResponse: {router_response}")
            # Fallback to default
            router_result = {
                "databases": {"project_db": True, "code_db": False, "coop_manual": False, "speckle_db": False},
                "project_route": "smart"
            }
        
        # Extract database selections and project route
        # The router prompt uses "databases" key with the 4 database names
        databases = router_result.get("databases", {})
        data_sources = {
            "project_db": databases.get("project_db", False),
            "code_db": databases.get("code_db", False),
            "coop_manual": databases.get("coop_manual", False),
            "speckle_db": databases.get("speckle_db", False)
        }

        # Heuristic: if a specific project is detected and the query is structural/model-related,
        # auto-enable speckle_db (and ensure project_db) to surface BIM/Speckle content.
        structural_keywords = ["speckle", "model", "3d", "beam", "column", "lintel", "truss", "girder", "frame"]
        if project_filter and not data_sources["speckle_db"]:
            q_lower = state.user_query.lower() if state.user_query else ""
            if any(k in q_lower for k in structural_keywords):
                log_route.info("🛠️ Auto-enabling speckle_db based on structural query and project context")
                data_sources["speckle_db"] = True
                data_sources["project_db"] = True
        
        # ENFORCE CONSTRAINT: speckle_db cannot be selected alone - must have project_db
        if data_sources["speckle_db"] and not data_sources["project_db"]:
            log_route.warning("⚠️ Router selected speckle_db without project_db - enforcing constraint: enabling project_db")
            data_sources["project_db"] = True
        
        # Get project route (smart/large) - only relevant if project_db is enabled
        project_route = router_result.get("project_route", "smart")
        if not data_sources["project_db"]:
            project_route = None
        
        # Ensure at least one database is selected (fallback safety)
        if not any(data_sources.values()):
            log_route.warning("⚠️ No databases selected by router, defaulting to project_db")
            data_sources["project_db"] = True
            project_route = "smart"
        
        # Update state with selected data sources
        state.data_sources = data_sources
        
        log_route.info(f"🎯 RAG ROUTER DECISION:")
        log_route.info(f"   Query: '{state.user_query[:80]}...'")
        log_route.info(f"   Databases: project_db={data_sources['project_db']}, code_db={data_sources['code_db']}, coop_manual={data_sources['coop_manual']}, speckle_db={data_sources['speckle_db']}")
        log_route.info(f"   Project route: {project_route}")
        
        routing_intelligence = {
            "data_route": project_route,
            "data_sources": data_sources,
            "project_filter": project_filter,
            "route_reasoning": _get_route_reasoning(project_route) if project_route else "no_project_db",
            "scope_assessment": "filtered" if project_filter else "open",
            "timestamp": time.time(),
            "source": "rag_router_execution"
        }
        
        state._routing_intelligence = routing_intelligence

        t_elapsed = time.time() - t_start
        log_route.info(f"<<< RAG ROUTER DONE in {t_elapsed:.2f}s")
        
        return {
            "data_route": project_route,
            "data_sources": data_sources,
            "project_filter": project_filter
        }
    except Exception as e:
        log_route.error(f"RAG Router failed: {e}")
        import traceback
        traceback.print_exc()
        # Fallback to default
        fallback_sources = {"project_db": True, "code_db": False, "coop_manual": False, "speckle_db": False}
        state.data_sources = fallback_sources
        return {
            "data_route": "smart",
            "data_sources": fallback_sources,
            "project_filter": detect_project_filter(state.user_query) if state.user_query else None
        }
