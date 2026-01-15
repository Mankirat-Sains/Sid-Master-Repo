"""
DesktopAgent Subgraph
Handles desktop application interactions and delegates doc generation when requested.
"""
from dataclasses import asdict
from langgraph.graph import StateGraph, END

from models.rag_state import RAGState
from models.parent_state import ParentState
from config.logging_config import log_route
from config.settings import DEEP_AGENT_ENABLED
from desktop_agent.routing import node_desktop_router
from graph.subgraphs.document_generation_subgraph import call_doc_generation_subgraph
from graph.subgraphs.deep_desktop_subgraph import call_deep_desktop_subgraph
from graph.tracing import wrap_subgraph_node

def _desktop_to_next(state: RAGState) -> str:
    """
    Route after desktop router:
    - If doc generation is requested, route to deep_desktop when enabled, otherwise doc_generation.
    - Otherwise finish.
    """
    is_doc_task = getattr(state, "workflow", None) == "docgen" or getattr(state, "task_type", None) in {
        "doc_section",
        "doc_report",
    }
    if not is_doc_task:
        return "finish"
    if DEEP_AGENT_ENABLED:
        return "deep_desktop"
    return "doc_generation"



def build_desktop_agent_subgraph():
    """
    Build the DesktopAgent subgraph.
    Current structure: desktop_router → (doc_generation?) → finish.
    """
    g = StateGraph(RAGState)

    g.add_node("desktop_router", wrap_subgraph_node("desktop_router")(node_desktop_router))
    g.add_node("doc_generation", wrap_subgraph_node("doc_generation")(call_doc_generation_subgraph))
    if DEEP_AGENT_ENABLED:
        g.add_node("deep_desktop", wrap_subgraph_node("deep_desktop")(call_deep_desktop_subgraph))
    g.add_node("finish", wrap_subgraph_node("finish")(lambda state: {}))

    g.set_entry_point("desktop_router")
    if DEEP_AGENT_ENABLED:
        g.add_conditional_edges(
            "desktop_router",
            _desktop_to_next,
            {
                "deep_desktop": "deep_desktop",
                "doc_generation": "doc_generation",
                "finish": "finish",
            },
        )
        g.add_edge("deep_desktop", "finish")
    else:
        g.add_conditional_edges(
            "desktop_router",
            _desktop_to_next,
            {
                "doc_generation": "doc_generation",
                "finish": "finish",
            },
        )
    g.add_edge("doc_generation", "finish")
    g.add_edge("finish", END)

    return g.compile()


_desktop_agent_subgraph = None


def call_desktop_agent_subgraph(state: ParentState) -> dict:
    """
    Wrapper node that invokes the DesktopAgent subgraph.
    """
    global _desktop_agent_subgraph

    if _desktop_agent_subgraph is None:
        log_route.info("🔧 Initializing DesktopAgent subgraph...")
        _desktop_agent_subgraph = build_desktop_agent_subgraph()
        log_route.info("✅ DesktopAgent subgraph initialized")

    # Normalize state to RAGState with defaults for new fields
    state_dict = state if isinstance(state, dict) else asdict(state)
    rag_state_dict = _ensure_rag_state_fields(state_dict)
    rag_state = RAGState(**rag_state_dict)

    parent_trace = rag_state.execution_trace or []
    parent_verbose = rag_state.execution_trace_verbose or []

    try:
        result = _desktop_agent_subgraph.invoke(rag_state)
        if not isinstance(result, dict):
            return {"desktop_result": result}
        return {
            **result,
            "desktop_result": result,
            "execution_trace": parent_trace + (result.get("execution_trace", []) or []),
            "execution_trace_verbose": parent_verbose + (result.get("execution_trace_verbose", []) or []),
        }
    except Exception as e:
        log_route.error(f"❌ DesktopAgent subgraph failed: {e}")
        import traceback

        traceback.print_exc()
        return {
            "desktop_result": f"Error: {str(e)}",
            "desktop_citations": []
        }


def _ensure_rag_state_fields(state_dict: dict) -> dict:
    """Ensure all RAGState fields exist in the state dictionary."""
    rag_state_defaults = {
        "desktop_plan_steps": [],
        "desktop_current_step": 0,
        "desktop_iteration_count": 0,
        "desktop_workspace_dir": None,
        "desktop_workspace_files": [],
        "desktop_memories": [],
        "desktop_context": {},
        "desktop_interrupt_pending": False,
        "desktop_approved_actions": [],
        "desktop_interrupt_data": None,
        "tool_execution_log": [],
        "large_output_refs": {},
        "desktop_loop_result": None,
    }
    for field, default in rag_state_defaults.items():
        if field not in state_dict:
            state_dict[field] = default
    return state_dict
