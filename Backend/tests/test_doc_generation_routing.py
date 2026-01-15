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
from Backend.models.parent_state import ParentState  # noqa: E402


def test_doc_generation_branch(monkeypatch):
    order = []

    monkeypatch.setattr(
        "Backend.graph.builder.node_plan",
        lambda state: order.append("plan") or {"selected_routers": []},
    )

    def stub_classifier(state):
        order.append("doc_task_classifier")
        return {
            "task_type": "doc_section",
            "workflow": "docgen",
            "doc_type": "design_report",
            "section_type": "methodology",
        }

    monkeypatch.setattr("Backend.graph.builder.node_doc_task_classifier", stub_classifier)

    def stub_desktop_agent(state):
        order.append("desktop_agent")
        assert state.workflow == "docgen"
        return {
            "workflow": "docgen",
            "task_type": "doc_section",
            "doc_type": "design_report",
            "section_type": "methodology",
            "requires_desktop_action": True,
            "desktop_action_plan": {"action": "open"},
            "doc_generation_result": {"draft_text": "DOCGEN_DRAFT", "citations": [{"id": "c1"}]},
            "final_answer": "DOCGEN_DRAFT",
            "answer_citations": [{"id": "c1"}],
            "execution_trace": ["doc_plan", "doc_generate_section"],
        }

    monkeypatch.setattr("Backend.graph.builder.call_desktop_agent_subgraph", stub_desktop_agent)
    monkeypatch.setattr(
        "Backend.graph.builder.call_db_retrieval_subgraph",
        lambda state: (_ for _ in ()).throw(RuntimeError("db_retrieval called")),
    )
    monkeypatch.setattr(
        "Backend.graph.builder.node_router_dispatcher",
        lambda state: (_ for _ in ()).throw(RuntimeError("router_dispatcher called")),
    )

    app = build_graph()
    out = app.invoke(
        ParentState(user_query="Open artifact X in Word and apply edits"),
        config={"configurable": {"thread_id": "test-docgen"}},
    )

    assert out.get("workflow") == "docgen"
    assert out.get("requires_desktop_action") is True
    assert out.get("desktop_action_plan")
    assert out.get("final_answer") == "DOCGEN_DRAFT"
    assert out.get("answer_citations") == [{"id": "c1"}]
    assert order == ["plan", "doc_task_classifier", "desktop_agent"]


def test_qa_branch_skips_doc_generation(monkeypatch):
    order = []

    monkeypatch.setattr(
        "Backend.graph.builder.node_plan",
        lambda state: order.append("plan") or {"selected_routers": []},
    )

    def stub_classifier(state):
        order.append("doc_task_classifier")
        return {"task_type": "qa", "workflow": "qa"}

    monkeypatch.setattr("Backend.graph.builder.node_doc_task_classifier", stub_classifier)
    monkeypatch.setattr(
        "Backend.graph.builder.call_desktop_agent_subgraph",
        lambda state: (_ for _ in ()).throw(RuntimeError("desktop_agent called")),
    )

    def stub_db_retrieval(state):
        order.append("db_retrieval")
        return {
            "db_retrieval_result": "QA_ANSWER",
            "db_retrieval_citations": [],
        }

    monkeypatch.setattr("Backend.graph.builder.call_db_retrieval_subgraph", stub_db_retrieval)
    monkeypatch.setattr(
        "Backend.graph.builder.node_router_dispatcher",
        lambda state: (_ for _ in ()).throw(RuntimeError("router_dispatcher called")),
    )

    app = build_graph()
    out = app.invoke(
        ParentState(user_query="Summarize report X"),
        config={"configurable": {"thread_id": "test-qa"}},
    )

    assert out.get("db_retrieval_result") == "QA_ANSWER"
    assert "desktop_agent" not in order
    assert order == ["plan", "doc_task_classifier", "db_retrieval"]
