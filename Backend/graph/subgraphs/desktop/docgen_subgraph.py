"""
Doc Generation Subgraph
Runs the document generation pipeline (plan → generation → answer adaptation).
"""
import time
from dataclasses import asdict

from langgraph.graph import StateGraph, END

from models.parent_state import ParentState
from models.rag_state import RAGState
from config.settings import MAX_CONVERSATION_HISTORY
from config.logging_config import log_query
from nodes.DesktopAgent.doc_generation.plan import node_doc_plan
from nodes.DesktopAgent.doc_generation.section_generator import node_doc_generate_section
from nodes.DesktopAgent.doc_generation.report_generator import node_doc_generate_report
from nodes.DesktopAgent.doc_generation.answer_adapter import node_doc_answer_adapter


def _doc_entry_passthrough(state: RAGState) -> dict:
    """Entry node to allow routing decisions."""
    return {}


def _doc_generate_route(state: RAGState) -> str:
    """Route to section vs report generation."""
    if getattr(state, "task_type", None) == "doc_report":
        return "doc_generate_report"
    return "doc_generate_section"


def _doc_should_retrieve(state: RAGState) -> str:
    """Decide whether to run retrieval before planning."""
    needs_retrieval = getattr(state, "needs_retrieval", False)
    retrieval_completed = getattr(state, "retrieval_completed", False)
    log_query.info("🔀 DOCGEN ROUTING: needs_retrieval=%s, completed=%s", needs_retrieval, retrieval_completed)
    if needs_retrieval and not retrieval_completed:
        log_query.info("➡️  DOCGEN routing to retrieve")
        return "doc_retrieve"
    log_query.info("➡️  DOCGEN routing to plan (skip retrieval)")
    return "doc_plan"


def _doc_retrieve(state: RAGState) -> dict:
    """
    Placeholder retrieval guard for doc generation.
    Marks retrieval as completed to avoid loops when generation doesn't need DB retrieval.
    """
    needs_retrieval = getattr(state, "needs_retrieval", True)
    retrieval_completed = getattr(state, "retrieval_completed", False)
    log_query.info(
        "DOCGEN: retrieve (guard) | needs_retrieval=%s | retrieval_completed=%s", needs_retrieval, retrieval_completed
    )
    if retrieval_completed:
        log_query.info("⏭️ DOCGEN retrieval already completed; skipping")
        return {"retrieval_completed": True, "needs_retrieval": False}
    if not needs_retrieval:
        log_query.info("⏭️ DOCGEN retrieval not needed for simple generation")
        return {"retrieval_completed": True, "needs_retrieval": False, "retrieved_docs": []}
    # Hook for future retrieval logic; mark completion to avoid re-entry
    return {"retrieval_completed": True, "needs_retrieval": False}


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
    messages = list(getattr(state, "messages", []) or [])
    answer_text = getattr(state, "final_answer", None) or ""

    # Ensure the user turn is present, then append assistant turn
    if state.original_question and (not messages or messages[-1].get("role") != "user"):
        messages.append({"role": "user", "content": state.original_question})
    if answer_text:
        if messages and messages[-1].get("role") == "assistant":
            messages[-1] = {"role": "assistant", "content": answer_text}
        else:
            messages.append({"role": "assistant", "content": answer_text})
        max_messages = MAX_CONVERSATION_HISTORY * 2
        if len(messages) > max_messages:
            messages = messages[-max_messages:]

    history = list(getattr(state, "conversation_history", []) or [])
    if state.original_question or answer_text:
        history.append(
            {
                "question": state.original_question or state.user_query,
                "answer": answer_text,
                "timestamp": time.time(),
                "projects": [],
                "doc_type": getattr(state, "doc_type", None),
                "section_type": getattr(state, "section_type", None),
            }
        )
        if len(history) > MAX_CONVERSATION_HISTORY:
            history = history[-MAX_CONVERSATION_HISTORY:]

    return {
        "final_answer": getattr(state, "final_answer", None),
        "answer_citations": getattr(state, "answer_citations", []),
        "doc_generation_result": getattr(state, "doc_generation_result", None),
        "doc_generation_warnings": getattr(state, "doc_generation_warnings", []),
        "messages": messages,
        "conversation_history": history,
    }


def build_doc_generation_subgraph():
    """Compile the doc generation subgraph."""
    g = StateGraph(RAGState)

    g.add_node("doc_entry", _doc_entry_passthrough)
    g.add_node("doc_retrieve", _doc_retrieve)
    g.add_node("doc_plan", node_doc_plan)
    g.add_node("doc_generate_section", node_doc_generate_section)
    g.add_node("doc_generate_report", node_doc_generate_report)
    g.add_node("doc_answer_adapter", node_doc_answer_adapter)
    g.add_node("doc_verify", _doc_verify)
    g.add_node("doc_correct", _doc_correct)

    g.set_entry_point("doc_entry")

    g.add_conditional_edges(
        "doc_entry",
        _doc_should_retrieve,
        {
            "doc_retrieve": "doc_retrieve",
            "doc_plan": "doc_plan",
        },
    )
    g.add_edge("doc_retrieve", "doc_plan")

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
        conversation_history=getattr(state, "conversation_history", []),
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
        needs_retrieval=getattr(state, "needs_retrieval", True),
        retrieval_completed=getattr(state, "retrieval_completed", False),
        retrieved_docs=getattr(state, "retrieved_docs", []),
        retrieved_code_docs=getattr(state, "retrieved_code_docs", []),
        retrieved_coop_docs=getattr(state, "retrieved_coop_docs", []),
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
        "needs_retrieval": result.get("needs_retrieval", getattr(state, "needs_retrieval", True)),
        "retrieval_completed": result.get("retrieval_completed", getattr(state, "retrieval_completed", False)),
        "final_answer": result.get("final_answer"),
        "answer_citations": result.get("answer_citations", []),
        "execution_trace": result.get("execution_trace", []),
        "execution_trace_verbose": result.get("execution_trace_verbose", []),
        "messages": result.get("messages", []),
        "conversation_history": result.get("conversation_history", []),
    }
