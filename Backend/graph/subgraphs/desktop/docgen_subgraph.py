"""
Doc Generation Subgraph
Runs the document generation pipeline (plan → generation → answer adaptation).
"""
from dataclasses import asdict

from langgraph.graph import StateGraph, END

from models.parent_state import ParentState
from models.rag_state import RAGState
from config.logging_config import log_query
from desktop_agent.agents.doc_generation.plan import node_doc_plan
from desktop_agent.agents.doc_generation.section_generator import node_doc_generate_section
from desktop_agent.agents.doc_generation.report_generator import node_doc_generate_report
from desktop_agent.agents.doc_generation.answer_adapter import node_doc_answer_adapter


def _doc_generate_route(state: RAGState) -> str:
    """Route to section vs report generation."""
    if getattr(state, "task_type", None) == "doc_report":
        return "doc_generate_report"
    return "doc_generate_section"


def _doc_verify(state: RAGState) -> dict:
    """Lightweight verify node for doc generation."""
    log_query.info("DOCGEN: verify (noop)")
    return {
        "needs_fix": False,
        "follow_up_questions": getattr(state, "follow_up_questions", []),
        "follow_up_suggestions": getattr(state, "follow_up_suggestions", []),
    }


def _doc_correct(state: RAGState) -> dict:
    """Finalize doc generation answer; ensure fields propagate to parent."""
    log_query.info("DOCGEN: correct (pass-through)")
    return {
        "final_answer": getattr(state, "final_answer", None),
        "answer_citations": getattr(state, "answer_citations", []),
        "doc_generation_result": getattr(state, "doc_generation_result", None),
        "doc_generation_warnings": getattr(state, "doc_generation_warnings", []),
    }


def build_doc_generation_subgraph():
    """Compile the doc generation subgraph."""
    g = StateGraph(RAGState)

    g.add_node("doc_plan", node_doc_plan)
    g.add_node("doc_generate_section", node_doc_generate_section)
    g.add_node("doc_generate_report", node_doc_generate_report)
    g.add_node("doc_answer_adapter", node_doc_answer_adapter)
    g.add_node("doc_verify", _doc_verify)
    g.add_node("doc_correct", _doc_correct)

    g.set_entry_point("doc_plan")

    g.add_conditional_edges(
        "doc_plan",
        _doc_generate_route,
        {
            "doc_generate_section": "doc_generate_section",
            "doc_generate_report": "doc_generate_report",
        },
    )
    g.add_edge("doc_generate_section", "doc_answer_adapter")
    g.add_edge("doc_generate_report", "doc_answer_adapter")
    g.add_edge("doc_answer_adapter", "doc_verify")
    g.add_edge("doc_verify", "doc_correct")
    g.add_edge("doc_correct", END)

    return g.compile()


_doc_generation_subgraph = None


def call_doc_generation_subgraph(state: ParentState) -> dict:
    """
    Wrapper node that invokes the doc generation subgraph from the parent graph.
    Transforms ParentState → RAGState → invokes subgraph → back to ParentState fields.
    """
    global _doc_generation_subgraph

    if _doc_generation_subgraph is None:
        log_query.info("🔧 Initializing DocGeneration subgraph...")
        _doc_generation_subgraph = build_doc_generation_subgraph()
        log_query.info("✅ DocGeneration subgraph initialized")

    doc_state = RAGState(
        session_id=state.session_id,
        user_query=state.user_query,
        original_question=state.original_question,
        user_role=state.user_role,
        messages=state.messages,
        selected_routers=getattr(state, "selected_routers", []),
        workflow=getattr(state, "workflow", None) or "docgen",
        desktop_policy=getattr(state, "desktop_policy", None),
        task_type=getattr(state, "task_type", None),
        doc_type=getattr(state, "doc_type", None),
        section_type=getattr(state, "section_type", None),
        doc_request=getattr(state, "doc_request", None),
        requires_desktop_action=getattr(state, "requires_desktop_action", False),
        desktop_action_plan=getattr(state, "desktop_action_plan", None),
        doc_generation_result=getattr(state, "doc_generation_result", None),
        doc_generation_warnings=getattr(state, "doc_generation_warnings", []),
        execution_trace=getattr(state, "execution_trace", []),
        execution_trace_verbose=getattr(state, "execution_trace_verbose", []),
    )

    result = _doc_generation_subgraph.invoke(asdict(doc_state))

    return {
        "workflow": result.get("workflow") or "docgen",
        "task_type": result.get("task_type"),
        "doc_type": result.get("doc_type"),
        "section_type": result.get("section_type"),
        "doc_request": result.get("doc_request"),
        "requires_desktop_action": result.get("requires_desktop_action", False),
        "desktop_action_plan": result.get("desktop_action_plan"),
        "desktop_steps": result.get("desktop_steps", []),
        "desktop_execution": result.get("desktop_execution"),
        "doc_generation_result": result.get("doc_generation_result"),
        "doc_generation_warnings": result.get("doc_generation_warnings", []),
        "final_answer": result.get("final_answer"),
        "answer_citations": result.get("answer_citations", []),
        "execution_trace": result.get("execution_trace", []),
        "execution_trace_verbose": result.get("execution_trace_verbose", []),
    }
