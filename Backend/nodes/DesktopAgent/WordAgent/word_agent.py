"""
Word Agent
Handles Word/DocX style desktop requests and document generation.
Routes to doc generation subgraph when workflow is docgen.
"""
from typing import Any, Dict
from dataclasses import asdict

from models.desktop_agent_state import DesktopAgentState
from models.desktop_agent_state import DesktopAgentState
from config.logging_config import log_route
from graph.subgraphs.desktop.docgen_subgraph import call_doc_generation_subgraph


def node_word_agent(state: DesktopAgentState) -> Dict[str, Any]:
    """
    Word agent - handles document generation and Word operations.
    If workflow is docgen, routes to doc generation subgraph.
    Otherwise provides basic Word agent functionality.
    """
    log_route.info(">>> WORD AGENT (DesktopAgent) START")
    
    workflow = getattr(state, "workflow", None)
    task_type = getattr(state, "task_type", None)
    
    # If doc generation requested, route to doc generation subgraph
    if workflow == "docgen" or task_type in {"doc_section", "doc_report"}:
        log_route.info("📝 Routing to document generation subgraph")
        
        # DesktopAgentState already has all needed fields for doc generation
        # Pass it directly to doc generation subgraph
        result = call_doc_generation_subgraph(state)
        
        log_route.info("<<< WORD AGENT (DesktopAgent) DONE - Document generated")
        return {
            **result,
            "selected_app": "word",
        }
    
    # Basic Word agent functionality (for non-docgen requests)
    log_route.info("📄 Basic Word agent functionality")
    result = {
        "desktop_result": {
            "app": "word",
            "status": "basic",
            "message": "Word agent executed.",
            "query": getattr(state, "user_query", ""),
        },
        "selected_app": "word",
    }
    log_route.info("<<< WORD AGENT (DesktopAgent) DONE")
    return result


__all__ = ["node_word_agent"]
