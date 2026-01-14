"""
DesktopAgent Subgraph
Handles desktop application interactions (Excel, Word, Revit, etc.)
"""
from langgraph.graph import StateGraph, START, END
from models.parent_state import ParentState
from models.desktop_agent_state import DesktopAgentState
from config.logging_config import log_route

# Import DesktopAgent nodes
from nodes.DesktopAgent.desktop_router import node_desktop_router
from nodes.DesktopAgent.excel_kb_agent import node_excel_kb_agent


def _parent_to_desktop_state(parent_state: ParentState) -> DesktopAgentState:
    """Convert ParentState to DesktopAgentState"""
    return DesktopAgentState(
        session_id=parent_state.session_id,
        user_query=parent_state.user_query,
        original_question=parent_state.original_question,
        user_role=parent_state.user_role,
        messages=parent_state.messages,
        excel_cache={},  # Start with empty cache
        desktop_result=None,
        desktop_citations=[]
    )


def _desktop_to_parent_state(desktop_state: DesktopAgentState) -> dict:
    """Convert DesktopAgentState back to dict for parent state update"""
    return {
        "desktop_result": desktop_state.desktop_result,
        "desktop_citations": desktop_state.desktop_citations
    }


def _route_desktop(state: DesktopAgentState) -> str:
    """Route to appropriate desktop agent based on query"""
    query_lower = state.user_query.lower()
    
    # Check for Excel-related queries
    excel_keywords = ["excel", "spreadsheet", "workbook", "sheet", "cell", "formula", "calculation"]
    if any(keyword in query_lower for keyword in excel_keywords):
        return "excel_kb_agent"
    
    # Default to excel_kb_agent for now (can add more agents later)
    return "excel_kb_agent"


def build_desktop_agent_subgraph():
    """
    Build the DesktopAgent subgraph.
    This subgraph handles desktop application interactions.
    
    Current structure:
    - desktop_router: Routes to appropriate desktop agents
    - excel_kb_agent: Excel knowledge base (reads on-demand, caches in state)
    
    Future expansion:
    - word_agent: Word document processing
    - revit_agent: Revit model interactions
    - verify: Verify desktop actions
    """
    g = StateGraph(DesktopAgentState)
    
    # Add nodes
    g.add_node("desktop_router", node_desktop_router)
    g.add_node("excel_kb_agent", node_excel_kb_agent)
    
    # Future nodes will be added here:
    # g.add_node("word_agent", node_word_agent)
    # g.add_node("revit_agent", node_revit_agent)
    # g.add_node("verify", node_verify_desktop)
    
    # Set entry point
    g.set_entry_point("desktop_router")
    
    # Route from desktop_router to appropriate agent
    g.add_conditional_edges(
        "desktop_router",
        _route_desktop,
        {
            "excel_kb_agent": "excel_kb_agent",
        }
    )
    
    # Excel KB agent → END
    g.add_edge("excel_kb_agent", END)
    
    # Compile subgraph (checkpointer will be propagated from parent)
    return g.compile()


# Global subgraph instance (will be initialized when first called)
_desktop_agent_subgraph = None


def call_desktop_agent_subgraph(state: ParentState) -> dict:
    """
    Wrapper node that invokes the DesktopAgent subgraph.
    This function is called from the parent graph or router_dispatcher.
    
    Converts ParentState to DesktopAgentState, runs subgraph, then converts back.
    Excel cache in DesktopAgentState is ephemeral - auto-clears when query completes.
    """
    global _desktop_agent_subgraph
    
    # Lazy initialization of subgraph
    if _desktop_agent_subgraph is None:
        log_route.info("🔧 Initializing DesktopAgent subgraph...")
        _desktop_agent_subgraph = build_desktop_agent_subgraph()
        log_route.info("✅ DesktopAgent subgraph initialized")
    
    # Convert ParentState to DesktopAgentState
    desktop_state = _parent_to_desktop_state(state)
    
    # Invoke subgraph with DesktopAgentState
    try:
        result_state = _desktop_agent_subgraph.invoke(desktop_state)
        
        # Handle both dict and DesktopAgentState return types
        # LangGraph may return dict in some cases
        if isinstance(result_state, dict):
            # Already a dict - extract desktop_result and desktop_citations
            result = {
                "desktop_result": result_state.get("desktop_result"),
                "desktop_citations": result_state.get("desktop_citations", [])
            }
        else:
            # DesktopAgentState object - convert to dict
            result = _desktop_to_parent_state(result_state)
        
        log_route.info(f"✅ DesktopAgent subgraph completed (Excel cache cleared automatically)")
        return result
        
    except Exception as e:
        log_route.error(f"❌ DesktopAgent subgraph failed: {e}")
        import traceback
        traceback.print_exc()
        # Return state with error indication
        return {
            "desktop_result": f"Error: {str(e)}",
            "desktop_citations": []
        }
