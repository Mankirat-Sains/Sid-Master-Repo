"""
DesktopAgent Subgraph
Handles desktop application interactions (Excel, Word, Revit, etc.)
"""
from langgraph.graph import StateGraph, START, END
from models.parent_state import ParentState
from config.logging_config import log_route

# Import DesktopAgent nodes
from nodes.DesktopAgent.desktop_router import node_desktop_router

# Future nodes will be added here:
# from nodes.DesktopAgent.excel_agent import node_excel_agent
# from nodes.DesktopAgent.word_agent import node_word_agent
# from nodes.DesktopAgent.revit_agent import node_revit_agent
# from nodes.DesktopAgent.verify import node_verify_desktop


def build_desktop_agent_subgraph():
    """
    Build the DesktopAgent subgraph.
    This subgraph handles desktop application interactions.
    
    Current structure:
    - desktop_router: Routes to appropriate desktop agents
    
    Future expansion:
    - excel_agent: Excel automation
    - word_agent: Word document processing
    - revit_agent: Revit model interactions
    - verify: Verify desktop actions
    """
    g = StateGraph(ParentState)  # TODO: Create DesktopAgentState in the future
    
    # Add nodes
    g.add_node("desktop_router", node_desktop_router)
    
    # Future nodes will be added here:
    # g.add_node("excel_agent", node_excel_agent)
    # g.add_node("word_agent", node_word_agent)
    # g.add_node("revit_agent", node_revit_agent)
    # g.add_node("verify", node_verify_desktop)
    
    # Set entry point
    g.set_entry_point("desktop_router")
    
    # Current: desktop_router → END
    # Future: desktop_router → [agent nodes] → verify → END
    g.add_edge("desktop_router", END)
    
    # Compile subgraph (checkpointer will be propagated from parent)
    return g.compile()


# Global subgraph instance (will be initialized when first called)
_desktop_agent_subgraph = None


def call_desktop_agent_subgraph(state: ParentState) -> dict:
    """
    Wrapper node that invokes the DesktopAgent subgraph.
    This function is called from the parent graph or router_dispatcher.
    """
    global _desktop_agent_subgraph
    
    # Lazy initialization of subgraph
    if _desktop_agent_subgraph is None:
        log_route.info("🔧 Initializing DesktopAgent subgraph...")
        _desktop_agent_subgraph = build_desktop_agent_subgraph()
        log_route.info("✅ DesktopAgent subgraph initialized")
    
    # Invoke subgraph with current state
    try:
        result = _desktop_agent_subgraph.invoke(state)
        return result
    except Exception as e:
        log_route.error(f"❌ DesktopAgent subgraph failed: {e}")
        import traceback
        traceback.print_exc()
        # Return state with error indication
        return {
            "desktop_tools": [],
            "desktop_reasoning": f"Error: {str(e)}",
        }
