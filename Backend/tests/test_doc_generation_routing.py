import sys
from pathlib import Path

import pytest

pytest.importorskip("langgraph")

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))
backend_dir = ROOT / "Backend"
if backend_dir.exists() and str(backend_dir) not in sys.path:
    sys.path.append(str(backend_dir))

from Backend.graph.builder import build_graph  # noqa: E402
from Backend.models.rag_state import RAGState  # noqa: E402


def test_doc_generation_branch(monkeypatch):
    calls = []

    order = []

    monkeypatch.setattr("Backend.graph.builder.node_plan", lambda state: {"selected_routers": []})

    def stub_classifier(state):
        order.append("doc_task_classifier")
        return {"task_type": "doc_section", "doc_type": "design_report", "section_type": "methodology"}

    monkeypatch.setattr("Backend.graph.builder.node_doc_task_classifier", stub_classifier)

    def stub_doc_plan(state):
        order.append("doc_plan")
        return {"doc_request": {"doc_type": "design_report", "section_type": "methodology"}, "requires_desktop_action": True, "desktop_action_plan": {"action": "open"}}

    monkeypatch.setattr("Backend.graph.builder.node_doc_plan", stub_doc_plan)

    def stub_desktop_execute(state):
        order.append("desktop_execute")
        assert state.requires_desktop_action
        assert state.desktop_action_plan
        return {"desktop_execution": "ran"}

    monkeypatch.setattr("Backend.graph.builder.node_desktop_execute", stub_desktop_execute)

    def stub_generate_section(state):
        order.append("doc_generate_section")
        return {
            "doc_generation_result": {
                "draft_text": "DOCGEN_DRAFT",
                "citations": [{"id": "c1"}],
                "warnings": ["w1"],
            },
            "doc_generation_warnings": ["w1"],
        }

    monkeypatch.setattr("Backend.graph.builder.node_doc_generate_section", stub_generate_section)
    monkeypatch.setattr("Backend.graph.builder.node_doc_generate_report", lambda state: (_ for _ in ()).throw(RuntimeError("report gen called")))

    def stub_answer_adapter(state):
        order.append("doc_answer_adapter")
        res = state.doc_generation_result or {}
        return {"final_answer": res.get("draft_text", ""), "answer_citations": res.get("citations", [])}

    monkeypatch.setattr("Backend.graph.builder.node_doc_answer_adapter", stub_answer_adapter)
    monkeypatch.setattr("Backend.graph.builder.node_verify", lambda state: order.append("verify") or {"needs_fix": False})
    monkeypatch.setattr("Backend.graph.builder.node_correct", lambda state, max_hops=1, min_score=0.6: order.append("correct") or {"final_answer": state.final_answer, "answer_citations": getattr(state, "answer_citations", [])})

    app = build_graph()
    out = app.invoke(RAGState(user_query="Open artifact X in Word and apply edits"))

    assert out.get("requires_desktop_action") is True
    assert out.get("desktop_action_plan")
    assert out.get("final_answer") == "DOCGEN_DRAFT"
    assert out.get("answer_citations") == [{"id": "c1"}]
    print(f"TRACE DOCGEN: {order}")
    assert order == [
        "doc_task_classifier",
        "doc_plan",
        "desktop_execute",
        "doc_generate_section",
        "doc_answer_adapter",
        "verify",
        "correct",
    ]


def test_qa_branch_skips_doc_generation(monkeypatch):
    order = []

    monkeypatch.setattr("Backend.graph.builder.node_plan", lambda state: {"selected_routers": []})

    def stub_classifier(state):
        order.append("doc_task_classifier")
        return {"task_type": "qa"}

    monkeypatch.setattr("Backend.graph.builder.node_doc_task_classifier", stub_classifier)
    # Doc nodes should not be hit; make them raise if called
    monkeypatch.setattr("Backend.graph.builder.node_doc_plan", lambda state: (_ for _ in ()).throw(RuntimeError("doc_plan called")))
    monkeypatch.setattr("Backend.graph.builder.node_doc_generate_section", lambda state: (_ for _ in ()).throw(RuntimeError("doc_generate_section called")))
    monkeypatch.setattr("Backend.graph.builder.node_doc_generate_report", lambda state: (_ for _ in ()).throw(RuntimeError("doc_generate_report called")))

    monkeypatch.setattr("Backend.graph.builder.node_rag", lambda state: order.append("rag") or {"rag_called": True})
    monkeypatch.setattr("Backend.graph.builder.node_retrieve", lambda state: order.append("retrieve") or {"graded_docs": []})
    monkeypatch.setattr("Backend.graph.builder.node_grade", lambda state: order.append("grade") or {"graded_docs": []})
    monkeypatch.setattr("Backend.graph.builder.node_answer", lambda state: order.append("answer") or {"final_answer": "QA_ANSWER"})
    monkeypatch.setattr("Backend.graph.builder.node_verify", lambda state: order.append("verify") or {"needs_fix": False})
    monkeypatch.setattr("Backend.graph.builder.node_correct", lambda state, max_hops=1, min_score=0.6: order.append("correct") or {"final_answer": state.final_answer})

    app = build_graph()
    out = app.invoke(RAGState(user_query="Summarize report X"))

    assert out["final_answer"] == "QA_ANSWER"
    assert "doc_plan" not in order and "doc_generate_section" not in order and "doc_generate_report" not in order
    print(f"TRACE QA: {order}")
    assert order == ["doc_task_classifier", "rag", "retrieve", "grade", "answer", "verify", "correct"]
