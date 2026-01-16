"""
DesktopAgent Subgraph
Handles desktop application interactions and delegates to specific desktop agents.
Routes to ExcelAgent, WordAgent, or RevitAgent based on desktop_router decisions.
"""
from dataclasses import asdict
from langgraph.graph import StateGraph, END

from models.orchestration_state import OrchestrationState
from models.desktop_agent_state import DesktopAgentState
from config.logging_config import log_route
from config.settings import DEEP_AGENT_ENABLED
from nodes.DesktopAgent.desktop_router import node_desktop_router
from nodes.DesktopAgent.ExcelAgent.excel_agent import node_excel_agent
from nodes.DesktopAgent.WordAgent.word_agent import node_word_agent
from nodes.DesktopAgent.RevitAgent.revit_agent import node_revit_agent
from graph.subgraphs.deep_desktop_subgraph import call_deep_desktop_subgraph
from graph.tracing import wrap_subgraph_node


def _desktop_to_next(state: DesktopAgentState) -> str:
    """
    Route after desktop router:
    - Route to the requested desktop app agent (excel, word, revit)
    - Word agent handles doc generation internally
    """
    selected_app = (getattr(state, "selected_app", None) or "").lower()
    desktop_tools = getattr(state, "desktop_tools", []) or []

    target = selected_app or (str(desktop_tools[0]).lower() if desktop_tools else "")

    if "excel" in target:
        return "excel_agent"
    if "word" in target:
        return "word_agent"
    if "revit" in target:
        return "revit_agent"
    return "finish"


def build_desktop_agent_subgraph():
    """
    Build the DesktopAgent subgraph.
    Structure: desktop_router → (excel_agent|word_agent|revit_agent) → finish.
    Word agent handles doc generation internally.
    """
    g = StateGraph(DesktopAgentState)

    g.add_node("desktop_router", wrap_subgraph_node("desktop_router")(node_desktop_router))
    g.add_node("excel_agent", wrap_subgraph_node("excel_agent")(node_excel_agent))
    g.add_node("word_agent", wrap_subgraph_node("word_agent")(node_word_agent))
    g.add_node("revit_agent", wrap_subgraph_node("revit_agent")(node_revit_agent))
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
                "excel_agent": "excel_agent",
                "word_agent": "word_agent",
                "revit_agent": "revit_agent",
                "finish": "finish",
            },
        )
        g.add_edge("deep_desktop", "finish")
    else:
        g.add_conditional_edges(
            "desktop_router",
            _desktop_to_next,
            {
                "excel_agent": "excel_agent",
                "word_agent": "word_agent",
                "revit_agent": "revit_agent",
                "finish": "finish",
            },
        )

    g.add_edge("excel_agent", "finish")
    g.add_edge("word_agent", "finish")
    g.add_edge("revit_agent", "finish")
    g.add_edge("finish", END)

    return g.compile()


_desktop_agent_subgraph = None


def call_desktop_agent_subgraph(state: OrchestrationState) -> dict:
    """
    Wrapper node that invokes the DesktopAgent subgraph.
    Extracts needed fields from OrchestrationState → DesktopAgentState → invokes subgraph → returns results.
    """
    global _desktop_agent_subgraph

    if _desktop_agent_subgraph is None:
        log_route.info("🔧 Initializing DesktopAgent subgraph...")
        _desktop_agent_subgraph = build_desktop_agent_subgraph()
        log_route.info("✅ DesktopAgent subgraph initialized")

    # Extract fields from OrchestrationState and create DesktopAgentState
    state_dict = state if isinstance(state, dict) else asdict(state)
    
    # Create DesktopAgentState with fields from orchestration state
    desktop_state = DesktopAgentState(
        session_id=state_dict.get("session_id", ""),
        user_query=state_dict.get("user_query", ""),
        original_question=state_dict.get("original_question"),
        user_role=state_dict.get("user_role"),
        messages=state_dict.get("messages", []),
        conversation_history=state_dict.get("conversation_history", []),
        selected_app=state_dict.get("selected_app", ""),
        operation_type=state_dict.get("operation_type", ""),
        file_path=state_dict.get("file_path", ""),
        verification_result=state_dict.get("verification_result", {}),
        desktop_tools=state_dict.get("desktop_tools", []),
        desktop_reasoning=state_dict.get("desktop_reasoning", ""),
        workflow=state_dict.get("workflow"),
        desktop_policy=state_dict.get("desktop_policy"),
        task_type=state_dict.get("task_type"),
        doc_type=state_dict.get("doc_type"),
        section_type=state_dict.get("section_type"),
        doc_request=state_dict.get("doc_request"),
        requires_desktop_action=state_dict.get("requires_desktop_action", False),
        desktop_action_plan=state_dict.get("desktop_action_plan"),
        desktop_steps=state_dict.get("desktop_steps", []),
        desktop_execution=state_dict.get("desktop_execution"),
        output_artifact_ref=state_dict.get("output_artifact_ref"),
        desktop_plan_steps=state_dict.get("desktop_plan_steps", []),
        desktop_current_step=state_dict.get("desktop_current_step", 0),
        desktop_iteration_count=state_dict.get("desktop_iteration_count", 0),
        desktop_workspace_dir=state_dict.get("desktop_workspace_dir"),
        desktop_workspace_files=state_dict.get("desktop_workspace_files", []),
        desktop_memories=state_dict.get("desktop_memories", []),
        desktop_context=state_dict.get("desktop_context", {}),
        desktop_interrupt_pending=state_dict.get("desktop_interrupt_pending", False),
        desktop_approved_actions=state_dict.get("desktop_approved_actions", []),
        desktop_interrupt_data=state_dict.get("desktop_interrupt_data"),
        tool_execution_log=state_dict.get("tool_execution_log", []),
        large_output_refs=state_dict.get("large_output_refs", {}),
        desktop_loop_result=state_dict.get("desktop_loop_result"),
        doc_generation_result=state_dict.get("doc_generation_result"),
        doc_generation_warnings=state_dict.get("doc_generation_warnings", []),
        needs_retrieval=state_dict.get("needs_retrieval", True),
        retrieval_completed=state_dict.get("retrieval_completed", False),
        execution_trace=state_dict.get("execution_trace", []),
        execution_trace_verbose=state_dict.get("execution_trace_verbose", []),
    )

    parent_trace = desktop_state.execution_trace or []
    parent_verbose = desktop_state.execution_trace_verbose or []

    try:
        result = _desktop_agent_subgraph.invoke(desktop_state)
        if not isinstance(result, dict):
            return {"desktop_result": result}
        
        # Extract only key results to return to orchestration state
        return {
            "desktop_result": result.get("desktop_result") or result,
            "desktop_tools": result.get("desktop_tools", []),
            "desktop_reasoning": result.get("desktop_reasoning", ""),
            "selected_app": result.get("selected_app", ""),
            "workflow": result.get("workflow"),
            "task_type": result.get("task_type"),
            "doc_type": result.get("doc_type"),
            "section_type": result.get("section_type"),
            "doc_generation_result": result.get("doc_generation_result"),
            "doc_generation_warnings": result.get("doc_generation_warnings", []),
            "final_answer": result.get("final_answer"),
            "answer_citations": result.get("answer_citations", []),
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
