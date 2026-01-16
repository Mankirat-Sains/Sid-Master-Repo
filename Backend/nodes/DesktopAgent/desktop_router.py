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
from nodes.DesktopAgent.WordAgent.task_classifier import _detect_task_type, _detect_doc_type, _detect_section, _classify_generation_complexity


def _infer_operation_type(query: str) -> str:
    """Infer high-level operation type from the user query."""
    q = (query or "").lower()
    if any(k in q for k in ["write", "update", "edit", "modify", "change"]):
        return "write"
    if any(k in q for k in ["analy", "calc", "review", "inspect", "check"]):
        return "analyze"
    return "read"


def node_desktop_router(state: DesktopAgentState) -> dict:
    """Route query to appropriate desktop applications"""
    t_start = time.time()
    log_route.info(">>> DESKTOP ROUTER START")

    try:
        # Desktop router always runs in DesktopAgent subgraph
        # (Parent graph already routed here)
        user_query = getattr(state, "user_query", "") or ""
        choice = desktop_router_llm.invoke(
            DESKTOP_ROUTER_PROMPT.format(q=user_query)
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

        # Choose the primary app target
        selected_app = ""
        if selected_tools:
            selected_app = str(selected_tools[0]).lower()
        
        # Check if this is a document generation request (even if not explicitly Word)
        # Use WordAgent task classifier to detect doc generation intent
        task_type, section_hint, rule, doc_type_hint = _detect_task_type(user_query)
        doc_type = doc_type_hint or _detect_doc_type(user_query)
        section_type = section_hint or _detect_section(user_query)
        gen_task_type, _, _ = _classify_generation_complexity(user_query)
        
        # If doc generation detected, route to word agent
        doc_intent = (
            task_type in {"doc_section", "doc_report"}
            or bool(doc_type)
            or bool(rule)
            or bool(gen_task_type)
        )
        
        if doc_intent and not selected_app:
            selected_app = "word"
            selected_tools = ["word"]
            log_route.info(f"📝 Detected document generation intent → routing to Word agent")
            log_route.info(f"   Task type: {task_type}, Doc type: {doc_type}, Section: {section_type}")

        operation_type = _infer_operation_type(user_query)

        log_route.info(
            "🖥️  DESKTOP ROUTER DECISION: '%s...' → Tools: %s | selected_app=%s | op=%s",
            user_query[:50],
            selected_tools,
            selected_app,
            operation_type,
        )
        log_route.info(f"   Reasoning: {reasoning}")

        t_elapsed = time.time() - t_start
        log_route.info(f"<<< DESKTOP ROUTER DONE in {t_elapsed:.2f}s")

        # If doc generation detected, set workflow and task_type
        result = {
            "desktop_tools": selected_tools,
            "desktop_reasoning": reasoning,
            "selected_app": selected_app,
            "operation_type": operation_type,
        }
        
        if doc_intent:
            result["workflow"] = "docgen"
            if task_type:
                result["task_type"] = task_type
            if doc_type:
                result["doc_type"] = doc_type
            if section_type:
                result["section_type"] = section_type
        
        return result
    except Exception as e:
        log_route.error(f"Desktop router failed: {e}")
        t_elapsed = time.time() - t_start
        log_route.info(f"<<< DESKTOP ROUTER DONE (with error) in {t_elapsed:.2f}s")
        return {
            "desktop_tools": [],
            "desktop_reasoning": f"Error: {str(e)}",
            "selected_app": "",
            "operation_type": "",
        }
