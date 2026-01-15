"""
Desktop Router Node
Routes query to appropriate desktop applications
"""
import json
import re
import time
from models.desktop_agent_state import DesktopAgentState
from prompts.desktop_router_prompts import DESKTOP_ROUTER_PROMPT, desktop_router_llm
from config.logging_config import log_route


def node_desktop_router(state: DesktopAgentState) -> dict:
    """Route query to appropriate desktop applications"""
    t_start = time.time()
    log_route.info(">>> DESKTOP ROUTER START")

    try:
        # Desktop router always runs in DesktopAgent subgraph
        # (Parent graph already routed here)

        choice = desktop_router_llm.invoke(
            DESKTOP_ROUTER_PROMPT.format(q=state.user_query)
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
            log_route.error(f"Desktop router JSON parse failed: {e}\nRAW:\n{choice}")
            selected_tools = []
            reasoning = "Failed to parse desktop router response."

        log_route.info(f"🖥️  DESKTOP ROUTER DECISION: '{state.user_query[:50]}...' → Tools: {selected_tools}")
        log_route.info(f"   Reasoning: {reasoning}")

        t_elapsed = time.time() - t_start
        log_route.info(f"<<< DESKTOP ROUTER DONE in {t_elapsed:.2f}s")

        return {
            "desktop_tools": selected_tools,
            "desktop_reasoning": reasoning
        }
    except Exception as e:
        log_route.error(f"Desktop router failed: {e}")
        t_elapsed = time.time() - t_start
        log_route.info(f"<<< DESKTOP ROUTER DONE (with error) in {t_elapsed:.2f}s")
        return {"desktop_tools": [], "desktop_reasoning": f"Error: {str(e)}"}

