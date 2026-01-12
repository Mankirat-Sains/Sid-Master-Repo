"""
WebCalcs Subgraph
Handles web-based calculations and tools (Calculator, SkyCiv, Jabacus, etc.)
"""
from langgraph.graph import StateGraph, START, END
from models.parent_state import ParentState
from config.logging_config import log_route

# Import WebCalcs nodes
from nodes.WebCalcs.web_router import node_web_router

# Future nodes will be added here:
# from nodes.WebCalcs.calculator import node_calculator
# from nodes.WebCalcs.skyciv import node_skyciv
# from nodes.WebCalcs.jabacus import node_jabacus


def build_webcalcs_subgraph():
    """
    Build the WebCalcs subgraph.
    This subgraph handles web-based calculation tools.
    
    Current structure:
    - web_router: Routes to appropriate web tools
    
    Future expansion:
    - calculator: Python-based calculations
    - skyciv: SkyCiv API integration
    - jabacus: Jabacus tool integration
    - verify: Verify calculation results
    """
    g = StateGraph(ParentState)  # TODO: Create WebCalcsState in the future
    
    # Add nodes
    g.add_node("web_router", node_web_router)
    
    # Future nodes will be added here:
    # g.add_node("calculator", node_calculator)
    # g.add_node("skyciv", node_skyciv)
    # g.add_node("jabacus", node_jabacus)
    # g.add_node("verify", node_verify_webcalcs)
    
    # Set entry point
    g.set_entry_point("web_router")
    
    # Current: web_router → END
    # Future: web_router → [tool nodes] → verify → END
    g.add_edge("web_router", END)
    
    # Compile subgraph (checkpointer will be propagated from parent)
    return g.compile()


# Global subgraph instance (will be initialized when first called)
_webcalcs_subgraph = None


def call_webcalcs_subgraph(state: ParentState) -> dict:
    """
    Wrapper node that invokes the WebCalcs subgraph.
    This function is called from the parent graph or router_dispatcher.
    """
    global _webcalcs_subgraph
    
    # Lazy initialization of subgraph
    if _webcalcs_subgraph is None:
        log_route.info("🔧 Initializing WebCalcs subgraph...")
        _webcalcs_subgraph = build_webcalcs_subgraph()
        log_route.info("✅ WebCalcs subgraph initialized")
    
    # Invoke subgraph with current state
    try:
        result = _webcalcs_subgraph.invoke(state)
        return result
    except Exception as e:
        log_route.error(f"❌ WebCalcs subgraph failed: {e}")
        import traceback
        traceback.print_exc()
        # Return state with error indication
        return {
            "web_tools": [],
            "web_reasoning": f"Error: {str(e)}",
        }
