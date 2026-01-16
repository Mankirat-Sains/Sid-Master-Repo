"""
BuildModelGen Subgraph
Handles building model generation and modification
"""
from langgraph.graph import StateGraph, START, END
from models.orchestration_state import OrchestrationState
from models.building_model_gen_state import BuildingModelGenState
from config.logging_config import log_query

# Future nodes will be added here:
# from nodes.BuildingModelGen.router import node_build_model_router
# from nodes.BuildingModelGen.create import node_create_model
# from nodes.BuildingModelGen.modify import node_modify_model
# from nodes.BuildingModelGen.verify import node_verify_model


def _placeholder_node(state: BuildingModelGenState) -> dict:
    """
    Placeholder node for BuildModelGen subgraph.
    This will be replaced with actual model generation logic.
    """
    log_query.info(">>> BUILD MODEL GEN PLACEHOLDER")
    log_query.warning("⚠️  BuildModelGen subgraph is not yet implemented")
    
    return {
        "build_model_result": None,
        "build_model_status": "not_implemented",
    }


def build_build_model_gen_subgraph():
    """
    Build the BuildModelGen subgraph.
    This subgraph handles building model generation and modification.
    
    Future structure:
    - router: Decide between create from scratch or modify existing
    - create: Create new building model
    - modify: Modify existing building model
    - verify: Verify structural coherence
    """
    g = StateGraph(BuildingModelGenState)
    
    # Add placeholder node for now
    g.add_node("placeholder", _placeholder_node)
    
    # Future nodes will be added here:
    # g.add_node("router", node_build_model_router)
    # g.add_node("create", node_create_model)
    # g.add_node("modify", node_modify_model)
    # g.add_node("verify", node_verify_model)
    
    # Set entry point
    g.set_entry_point("placeholder")
    
    # Current: placeholder → END
    # Future: router → [create/modify] → verify → END
    g.add_edge("placeholder", END)
    
    # Compile subgraph (checkpointer will be propagated from parent)
    return g.compile()


# Global subgraph instance (will be initialized when first called)
_build_model_gen_subgraph = None


def call_build_model_gen_subgraph(state: OrchestrationState) -> dict:
    """
    Wrapper node that invokes the BuildModelGen subgraph.
    Extracts needed fields from OrchestrationState → BuildingModelGenState → invokes subgraph → returns results.
    """
    global _build_model_gen_subgraph
    
    # Lazy initialization of subgraph
    if _build_model_gen_subgraph is None:
        log_query.info("🔧 Initializing BuildModelGen subgraph...")
        _build_model_gen_subgraph = build_build_model_gen_subgraph()
        log_query.info("✅ BuildModelGen subgraph initialized")
    
    # Extract fields from OrchestrationState and create BuildingModelGenState
    state_dict = state if isinstance(state, dict) else asdict(state)
    
    build_model_state = BuildingModelGenState(
        session_id=state_dict.get("session_id", ""),
        user_query=state_dict.get("user_query", ""),
        original_question=state_dict.get("original_question"),
        messages=state_dict.get("messages", []),
        conversation_history=state_dict.get("conversation_history", []),
        execution_trace=state_dict.get("execution_trace", []),
        execution_trace_verbose=state_dict.get("execution_trace_verbose", []),
    )
    
    # Invoke subgraph with BuildingModelGenState
    try:
        result = _build_model_gen_subgraph.invoke(build_model_state)
        
        # Return only key results to orchestration state
        return {
            "build_model_result": result.get("build_model_result"),
            "build_model_status": result.get("build_model_status"),
            "build_model_error": result.get("build_model_error"),
            "execution_trace": result.get("execution_trace", []),
            "execution_trace_verbose": result.get("execution_trace_verbose", []),
        }
    except Exception as e:
        log_query.error(f"❌ BuildModelGen subgraph failed: {e}")
        import traceback
        traceback.print_exc()
        # Return state with error indication
        return {
            "build_model_result": None,
            "build_model_status": "error",
            "build_model_error": str(e),
        }
