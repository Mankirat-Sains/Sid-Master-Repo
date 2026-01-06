"""
Planning Node - Router Selection Only
Determines which routers (rag, web, desktop) should handle the query
"""
import json
import re
import time
from models.rag_state import RAGState
from prompts.router_selection_prompts import ROUTER_SELECTION_PROMPT, router_selection_llm
from config.logging_config import log_query


def node_plan(state: RAGState) -> dict:
    """Planning node - selects which routers to use"""
    t_start = time.time()
    log_query.info(">>> PLAN START (Router Selection)")

    try:
        # Get router selection from LLM
        choice = router_selection_llm.invoke(
            ROUTER_SELECTION_PROMPT.format(q=state.user_query)
        ).content.strip()

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
