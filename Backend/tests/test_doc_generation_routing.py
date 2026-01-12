import sys
from pathlib import Path
import types
import importlib.machinery

import pytest

pytest.importorskip("langgraph")

if "dotenv" not in sys.modules:
    dotenv_stub = types.ModuleType("dotenv")
    dotenv_stub.load_dotenv = lambda *args, **kwargs: None
    dotenv_stub.__spec__ = importlib.machinery.ModuleSpec("dotenv", None)
    sys.modules["dotenv"] = dotenv_stub

class _DummyClient:
    def __init__(self, *args, **kwargs):
        pass

openai_stub = types.ModuleType("openai")
openai_stub.DefaultHttpxClient = _DummyClient
openai_stub.DefaultAsyncHttpxClient = _DummyClient
openai_stub.AsyncOpenAI = _DummyClient
openai_stub.__spec__ = importlib.machinery.ModuleSpec("openai", None)
sys.modules["openai"] = openai_stub

# Stub langchain_openai to avoid heavy client setup
lc_stub = types.ModuleType("langchain_openai")
class _DummyLLM:
    def __init__(self, *args, **kwargs):
        pass
    @staticmethod
    def model_rebuild(*args, **kwargs):
        return None
class _DummyEmb:
    def __init__(self, *args, **kwargs):
        pass
lc_stub.ChatOpenAI = _DummyLLM
lc_stub.OpenAIEmbeddings = _DummyEmb
lc_stub.__spec__ = importlib.machinery.ModuleSpec("langchain_openai", None)
sys.modules["langchain_openai"] = lc_stub
chat_models_stub = types.ModuleType("langchain_openai.chat_models")
chat_models_stub.ChatOpenAI = _DummyLLM
chat_models_stub.AzureChatOpenAI = _DummyLLM
chat_models_stub.__spec__ = importlib.machinery.ModuleSpec("langchain_openai.chat_models", None)
sys.modules["langchain_openai.chat_models"] = chat_models_stub


openai_stub = types.ModuleType("openai")
class _DummyClient:
    def __init__(self, *args, **kwargs):
        pass
openai_stub.DefaultHttpxClient = _DummyClient
openai_stub.DefaultAsyncHttpxClient = _DummyClient
openai_stub.AsyncOpenAI = _DummyClient
openai_stub.__spec__ = importlib.machinery.ModuleSpec("openai", None)
sys.modules["openai"] = openai_stub

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
        return {"doc_request": {"doc_type": "design_report", "section_type": "methodology"}, "requires_desktop_action": True, "desktop_action_plan": {"action": "open", "tool": "word"}}

    monkeypatch.setattr("Backend.graph.builder.node_doc_plan", stub_doc_plan)

    def stub_desktop_router(state):
        order.append("desktop_router")
        return {"desktop_action_plan": {"action": "open", "tool": "word"}}

    monkeypatch.setattr("Backend.graph.builder.node_desktop_router", stub_desktop_router)

    def stub_doc_think(state):
        order.append("doc_think")
        return {"desktop_steps": [{"action": "open", "tool": "word"}]}

    monkeypatch.setattr("Backend.graph.builder.node_doc_think", stub_doc_think)

    def stub_doc_act(state):
        order.append("doc_act")
        return {"desktop_execution": "ran", "desktop_steps": getattr(state, "desktop_steps", [])}

    monkeypatch.setattr("Backend.graph.builder.node_doc_act", stub_doc_act)

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
    out = app.invoke(RAGState(user_query="Open artifact X in Word and apply edits"), config={"configurable": {"thread_id": "test-docgen"}})

    assert out.get("requires_desktop_action") is True
    assert out.get("desktop_action_plan")
    assert out.get("final_answer") == "DOCGEN_DRAFT"
    assert out.get("answer_citations") == [{"id": "c1"}]
    print(f"TRACE DOCGEN: {order}")
    assert order == [
        "doc_task_classifier",
        "doc_plan",
        "desktop_router",
        "doc_think",
        "doc_act",
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
    monkeypatch.setattr("Backend.graph.builder.node_desktop_router", lambda state: (_ for _ in ()).throw(RuntimeError("desktop_router called")))
    monkeypatch.setattr("Backend.graph.builder.node_doc_think", lambda state: (_ for _ in ()).throw(RuntimeError("doc_think called")))
    monkeypatch.setattr("Backend.graph.builder.node_doc_act", lambda state: (_ for _ in ()).throw(RuntimeError("doc_act called")))
    monkeypatch.setattr("Backend.graph.builder.node_doc_generate_section", lambda state: (_ for _ in ()).throw(RuntimeError("doc_generate_section called")))
    monkeypatch.setattr("Backend.graph.builder.node_doc_generate_report", lambda state: (_ for _ in ()).throw(RuntimeError("doc_generate_report called")))

    monkeypatch.setattr("Backend.graph.builder.node_rag", lambda state: order.append("rag") or {"rag_called": True})
    monkeypatch.setattr("Backend.graph.builder.node_retrieve", lambda state: order.append("retrieve") or {"graded_docs": []})
    monkeypatch.setattr("Backend.graph.builder.node_grade", lambda state: order.append("grade") or {"graded_docs": []})
    monkeypatch.setattr("Backend.graph.builder.node_answer", lambda state: order.append("answer") or {"final_answer": "QA_ANSWER"})
    monkeypatch.setattr("Backend.graph.builder.node_verify", lambda state: order.append("verify") or {"needs_fix": False})
    monkeypatch.setattr("Backend.graph.builder.node_correct", lambda state, max_hops=1, min_score=0.6: order.append("correct") or {"final_answer": state.final_answer})

    app = build_graph()
    out = app.invoke(RAGState(user_query="Summarize report X"), config={"configurable": {"thread_id": "test-qa"}})

    assert out["final_answer"] == "QA_ANSWER"
    assert "doc_plan" not in order and "doc_generate_section" not in order and "doc_generate_report" not in order
    print(f"TRACE QA: {order}")
    assert order == ["doc_task_classifier", "rag", "retrieve", "grade", "answer", "verify", "correct"]


def test_doc_generation_report_branch(monkeypatch):
    order = []

    monkeypatch.setattr("Backend.graph.builder.node_plan", lambda state: {"selected_routers": []})

    def stub_classifier(state):
        order.append("doc_task_classifier")
        return {"task_type": "doc_report", "workflow": "docgen", "doc_type": "design_report"}

    monkeypatch.setattr("Backend.graph.builder.node_doc_task_classifier", stub_classifier)

    monkeypatch.setattr("Backend.graph.builder.node_doc_plan", lambda state: order.append("doc_plan") or {"doc_request": {"doc_type": "design_report"}, "requires_desktop_action": True, "desktop_action_plan": {"action": "open", "tool": "word"}})
    monkeypatch.setattr("Backend.graph.builder.node_desktop_router", lambda state: order.append("desktop_router") or {"desktop_action_plan": {"action": "open", "tool": "word"}})
    monkeypatch.setattr("Backend.graph.builder.node_doc_think", lambda state: order.append("doc_think") or {"desktop_steps": [{"action": "open", "tool": "word"}]})
    monkeypatch.setattr("Backend.graph.builder.node_doc_act", lambda state: order.append("doc_act") or {"desktop_execution": "ran"})
    monkeypatch.setattr("Backend.graph.builder.node_doc_generate_section", lambda state: (_ for _ in ()).throw(RuntimeError("doc_generate_section called")))
    monkeypatch.setattr("Backend.graph.builder.node_doc_generate_report", lambda state: order.append("doc_generate_report") or {"doc_generation_result": {"combined_text": "REPORT_DRAFT", "citations": [{"id": "r1"}]}})
    monkeypatch.setattr("Backend.graph.builder.node_doc_answer_adapter", lambda state: order.append("doc_answer_adapter") or {"final_answer": "REPORT_DRAFT", "answer_citations": [{"id": "r1"}]})
    monkeypatch.setattr("Backend.graph.builder.node_verify", lambda state: order.append("verify") or {"needs_fix": False})
    monkeypatch.setattr("Backend.graph.builder.node_correct", lambda state, max_hops=1, min_score=0.6: order.append("correct") or {"final_answer": state.final_answer})

    app = build_graph()
    out = app.invoke(RAGState(user_query="Create an RP report doc for client"), config={"configurable": {"thread_id": "test-doc-report"}})

    assert out["final_answer"] == "REPORT_DRAFT"
    assert out.get("answer_citations") == [{"id": "r1"}]
    print(f"TRACE DOC REPORT: {order}")
    assert order == ["doc_task_classifier", "doc_plan", "desktop_router", "doc_think", "doc_act", "doc_generate_report", "doc_answer_adapter", "verify", "correct"]


def test_doc_generation_section_branch(monkeypatch):
    order = []

    monkeypatch.setattr("Backend.graph.builder.node_plan", lambda state: {"selected_routers": []})

    def stub_classifier(state):
        order.append("doc_task_classifier")
        return {"task_type": "doc_section", "workflow": "docgen", "section_type": "introduction"}

    monkeypatch.setattr("Backend.graph.builder.node_doc_task_classifier", stub_classifier)

    monkeypatch.setattr("Backend.graph.builder.node_doc_plan", lambda state: order.append("doc_plan") or {"doc_request": {"section_type": "introduction"}, "requires_desktop_action": True, "desktop_action_plan": {"action": "open", "tool": "word"}})
    monkeypatch.setattr("Backend.graph.builder.node_desktop_router", lambda state: order.append("desktop_router") or {"desktop_action_plan": {"action": "open", "tool": "word"}})
    monkeypatch.setattr("Backend.graph.builder.node_doc_think", lambda state: order.append("doc_think") or {"desktop_steps": [{"action": "open", "tool": "word"}]})
    monkeypatch.setattr("Backend.graph.builder.node_doc_act", lambda state: order.append("doc_act") or {"desktop_execution": "ran"})
    monkeypatch.setattr("Backend.graph.builder.node_doc_generate_section", lambda state: order.append("doc_generate_section") or {"doc_generation_result": {"draft_text": "SECTION_DRAFT", "citations": [{"id": "s1"}]}})
    monkeypatch.setattr("Backend.graph.builder.node_doc_generate_report", lambda state: (_ for _ in ()).throw(RuntimeError("doc_generate_report called")))
    monkeypatch.setattr("Backend.graph.builder.node_doc_answer_adapter", lambda state: order.append("doc_answer_adapter") or {"final_answer": "SECTION_DRAFT", "answer_citations": [{"id": "s1"}]})
    monkeypatch.setattr("Backend.graph.builder.node_verify", lambda state: order.append("verify") or {"needs_fix": False})
    monkeypatch.setattr("Backend.graph.builder.node_correct", lambda state, max_hops=1, min_score=0.6: order.append("correct") or {"final_answer": state.final_answer})

    app = build_graph()
    out = app.invoke(RAGState(user_query="Draft an RFP introduction section"), config={"configurable": {"thread_id": "test-doc-section"}})

    assert out["final_answer"] == "SECTION_DRAFT"
    assert out.get("answer_citations") == [{"id": "s1"}]
    print(f"TRACE DOC SECTION: {order}")
    assert order == ["doc_task_classifier", "doc_plan", "desktop_router", "doc_think", "doc_act", "doc_generate_section", "doc_answer_adapter", "verify", "correct"]
