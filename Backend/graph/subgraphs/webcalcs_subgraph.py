"""
WebCalcs Subgraph
Handles web-based calculations and tools (Calculator, SkyCiv, Jabacus, etc.)
"""
from langgraph.graph import StateGraph, START, END
from models.orchestration_state import OrchestrationState
from models.webcalcs_state import WebCalcsState
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
    g = StateGraph(WebCalcsState)
    
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


def call_webcalcs_subgraph(state: OrchestrationState) -> dict:
    """
    Wrapper node that invokes the WebCalcs subgraph.
    Extracts needed fields from OrchestrationState → WebCalcsState → invokes subgraph → returns results.
    """
    global _webcalcs_subgraph
    
    # Lazy initialization of subgraph
    if _webcalcs_subgraph is None:
        log_route.info("🔧 Initializing WebCalcs subgraph...")
        _webcalcs_subgraph = build_webcalcs_subgraph()
        log_route.info("✅ WebCalcs subgraph initialized")
    
    # Extract fields from OrchestrationState and create WebCalcsState
    state_dict = state if isinstance(state, dict) else asdict(state)
    
    webcalcs_state = WebCalcsState(
        session_id=state_dict.get("session_id", ""),
        user_query=state_dict.get("user_query", ""),
        original_question=state_dict.get("original_question"),
        messages=state_dict.get("messages", []),
        conversation_history=state_dict.get("conversation_history", []),
        selected_routers=state_dict.get("selected_routers", []),
        execution_trace=state_dict.get("execution_trace", []),
        execution_trace_verbose=state_dict.get("execution_trace_verbose", []),
    )
    
    # Invoke subgraph with WebCalcsState
    try:
        result = _webcalcs_subgraph.invoke(webcalcs_state)
        
        # Return only key results to orchestration state
        return {
            "webcalcs_result": result.get("webcalcs_result"),
            "web_tools": result.get("web_tools", []),
            "web_reasoning": result.get("web_reasoning", ""),
            "execution_trace": result.get("execution_trace", []),
            "execution_trace_verbose": result.get("execution_trace_verbose", []),
        }
    except Exception as e:
        log_route.error(f"❌ WebCalcs subgraph failed: {e}")
        import traceback
        traceback.print_exc()
        # Return state with error indication
        return {
            "web_tools": [],
            "web_reasoning": f"Error: {str(e)}",
        }
