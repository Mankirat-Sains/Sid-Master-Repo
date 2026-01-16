"""
Deep Desktop Subgraph
Runs the deep desktop loop as a standalone subgraph.
"""
from langgraph.graph import StateGraph, END

from models.desktop_agent_state import DesktopAgentState
from nodes.DesktopAgent.WordAgent.deep_desktop_loop import node_deep_desktop_loop


def build_deep_desktop_subgraph():
    """Compile deep desktop subgraph."""
    graph = StateGraph(DesktopAgentState)
    graph.add_node("deep_desktop_loop", node_deep_desktop_loop)
    graph.set_entry_point("deep_desktop_loop")
    graph.add_edge("deep_desktop_loop", END)
    return graph.compile()


_deep_desktop_subgraph = None


def call_deep_desktop_subgraph(state: DesktopAgentState) -> dict:
    """
    Wrapper that invokes the deep desktop subgraph.
    Allows GraphInterrupt to propagate to the caller.
    """
    global _deep_desktop_subgraph
    if _deep_desktop_subgraph is None:
        _deep_desktop_subgraph = build_deep_desktop_subgraph()
    return _deep_desktop_subgraph.invoke(state)
