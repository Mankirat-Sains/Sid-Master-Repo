"""
DesktopAgent Subgraph
Handles desktop application interactions and delegates doc generation when requested.
"""
from langgraph.graph import StateGraph, END

from models.parent_state import ParentState
from config.logging_config import log_route
from nodes.DesktopAgent.desktop_router import node_desktop_router
from graph.subgraphs.desktop.docgen_subgraph import call_doc_generation_subgraph
from graph.tracing import wrap_subgraph_node


def _desktop_to_next(state: ParentState) -> str:
    """
    Route after desktop router:
    - If doc generation is requested, run the doc_generation subgraph.
    - Otherwise finish.
    """
    if getattr(state, "workflow", None) == "docgen" or getattr(state, "task_type", None) in {"doc_section", "doc_report"}:
        return "doc_generation"
    return "finish"


def build_desktop_agent_subgraph():
    """
    Build the DesktopAgent subgraph.
    Current structure: desktop_router → (doc_generation?) → finish.
    """
    g = StateGraph(ParentState)

    g.add_node("desktop_router", wrap_subgraph_node("desktop_router")(node_desktop_router))
    g.add_node("doc_generation", wrap_subgraph_node("doc_generation")(call_doc_generation_subgraph))
    g.add_node("finish", wrap_subgraph_node("finish")(lambda state: {}))

    g.set_entry_point("desktop_router")
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

    parent_trace = getattr(state, "execution_trace", []) or []
    parent_verbose = getattr(state, "execution_trace_verbose", []) or []

    try:
        result = _desktop_agent_subgraph.invoke(state)
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
            "desktop_tools": [],
            "desktop_reasoning": f"Error: {str(e)}",
        }
