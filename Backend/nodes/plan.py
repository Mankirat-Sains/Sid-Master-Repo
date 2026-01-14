"""
Planning Node - Router Selection Only
Determines which routers (rag, web, desktop) should handle the query
This is the orchestrator - keeps it simple and fast
"""
import json
import re
import time
from models.parent_state import ParentState
from prompts.router_selection_prompts import ROUTER_SELECTION_PROMPT, router_selection_llm
from config.logging_config import log_query
from langgraph.config import get_stream_writer


def node_plan(state: ParentState) -> dict:
    """
    Planning node - selects which routers to use (orchestrator level - keep it simple)
    Determines which routers (rag, web, desktop) should handle the query
    """
    t_start = time.time()
    log_query.info(">>> PLAN START (Router Selection)")
    
    # Emit custom progress event (LangGraph best practice)
    try:
        writer = get_stream_writer()
        writer({"type": "thinking", "node": "plan", "message": "🎯 Analyzing your query to determine the best approach..."})
    except Exception:
        # get_stream_writer only works in streaming context, ignore if not available
        pass

    try:
        # Get router selection from LLM
        # Match the exact pattern used by other working routers (desktop_router, web_router, etc.)
        # They all pass formatted prompt strings directly to .invoke()
        formatted_prompt = ROUTER_SELECTION_PROMPT.format(q=state.user_query)
        
        # Invoke with string (same pattern as desktop_router.py, web_router.py, rag_plan.py)
        response = router_selection_llm.invoke(formatted_prompt)
        
        # Extract content - should be AIMessage with .content attribute
        # This matches the pattern: desktop_router_llm.invoke(...).content.strip()
        if hasattr(response, 'content'):
            choice = response.content.strip()
        else:
            # Fallback: try to extract from ChatResult if needed
            log_query.warning(f"Unexpected response type: {type(response)}, trying to extract content")
            if hasattr(response, 'generations') and response.generations:
                choice = response.generations[0].message.content.strip()
            else:
                choice = str(response).strip()

        # Parse JSON response
        try:
            m = re.search(r"\{.*\}\s*$", choice, flags=re.S)
            json_str = m.group(0) if m else choice
            log_query.info(f"🔍 ROUTER SELECTION RAW JSON: {json_str}")
            obj = json.loads(json_str)
        except Exception as e:
            log_query.error(f"Router selection JSON parse failed: {e}\nRAW:\n{choice}")
            obj = {}

        # Extract routers
        routers_in = obj.get("routers") or []
        reasoning = obj.get("reasoning", "No reasoning provided.")
        
        # Normalize and validate routers
        allowed_routers = {"rag", "web", "desktop"}
        selected_routers = []
        if isinstance(routers_in, list):
            for r in routers_in:
                r_str = str(r).strip().lower()
                if r_str in allowed_routers:
                    selected_routers.append(r_str)
        
        # Fallback: if no routers specified, default to "rag"
        if not selected_routers:
            selected_routers = ["rag"]
            log_query.warning("⚠️  No valid routers found, defaulting to 'rag'")

        log_query.info("🎯 ROUTER SELECTION:")
        log_query.info(f"   Selected Routers: {selected_routers}")
        log_query.info(f"   Reasoning: {reasoning}")

        t_elapsed = time.time() - t_start
        log_query.info(f"<<< PLAN DONE (Router Selection) in {t_elapsed:.2f}s")

        return {
            "selected_routers": selected_routers
        }
    except Exception as e:
        log_query.error(f"Router selection failed: {e}")
        t_elapsed = time.time() - t_start
        log_query.info(f"<<< PLAN DONE (Router Selection - with error) in {t_elapsed:.2f}s")
        # Fallback to rag router
        return {"selected_routers": ["rag"]}
