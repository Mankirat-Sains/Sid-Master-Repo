"""
Web Router Node
Routes query to appropriate web applications and Python tools
"""
import json
import re
import time
from models.webcalcs_state import WebCalcsState
from prompts.web_router_prompts import WEB_ROUTER_PROMPT, web_router_llm
from config.logging_config import log_route


def node_web_router(state: WebCalcsState) -> dict:
    """Route query to appropriate web applications and Python tools"""
    t_start = time.time()
    log_route.info(">>> WEB ROUTER START")

    try:
        # Only run if "web" is in selected routers
        if "web" not in (state.selected_routers or []):
            log_route.info("⏭️  Skipping web router - not selected")
            return {"web_tools": [], "web_reasoning": ""}

        choice = web_router_llm.invoke(
            WEB_ROUTER_PROMPT.format(q=state.user_query)
        ).content.strip()

        # Parse JSON response
        try:
            m = re.search(r"\{.*\}\s*$", choice, flags=re.S)
            json_str = m.group(0) if m else choice
            obj = json.loads(json_str)
            selected_tools = obj.get("selected_tools", [])
            reasoning = obj.get("reasoning", "No reasoning provided.")
            
            if not isinstance(selected_tools, list):
                selected_tools = []
            if not isinstance(reasoning, str):
                reasoning = "No reasoning provided."
        except Exception as e:
            log_route.error(f"Web router JSON parse failed: {e}\nRAW:\n{choice}")
            selected_tools = []
            reasoning = "Failed to parse web router response."

        log_route.info(f"🌐 WEB ROUTER DECISION: '{state.user_query[:50]}...' → Tools: {selected_tools}")
        log_route.info(f"   Reasoning: {reasoning}")

        t_elapsed = time.time() - t_start
        log_route.info(f"<<< WEB ROUTER DONE in {t_elapsed:.2f}s")

        return {
            "web_tools": selected_tools,
            "web_reasoning": reasoning
        }
    except Exception as e:
        log_route.error(f"Web router failed: {e}")
        t_elapsed = time.time() - t_start
        log_route.info(f"<<< WEB ROUTER DONE (with error) in {t_elapsed:.2f}s")
        return {"web_tools": [], "web_reasoning": f"Error: {str(e)}"}

