import sys
import types
import importlib.machinery
import os
from pathlib import Path

import pytest

# Minimal stubs for external deps
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

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))
backend_dir = ROOT / "Backend"
if backend_dir.exists() and str(backend_dir) not in sys.path:
    sys.path.append(str(backend_dir))

from Backend import main  # noqa: E402
from Backend.main import run_agentic_rag  # noqa: E402
import Backend.models.memory as mem  # noqa: E402


class _StubGraph:
    def __init__(self, payload):
        self.payload = payload

    def invoke(self, *args, **kwargs):
        return self.payload


def test_docgen_csv_logging(monkeypatch, tmp_path):
    csv_path = tmp_path / "drafted.csv"
    os.environ["DOCGEN_CSV_PATH"] = str(csv_path)

    payload = {
        "final_answer": "DOCGEN_TEXT",
        "answer_citations": [{"id": "c1"}],
        "doc_generation_result": {"length_target": {"min_chars": 100, "max_chars": 200}, "citations": [{"id": "c1"}]},
        "doc_generation_warnings": ["w1"],
        "workflow": "docgen",
        "task_type": "doc_section",
        "doc_type": "design_report",
        "section_type": "methodology",
        "execution_trace": ["doc_task_classifier", "doc_plan", "doc_generate_section"],
    }
    monkeypatch.setattr(main, "graph", _StubGraph(payload))
    called = {}

    def stub_append(**kwargs):
        called.update(kwargs)

    monkeypatch.setattr("Backend.main.append_draft_csv", lambda *args, **kwargs: stub_append(**kwargs))
    monkeypatch.setattr(mem, "intelligent_query_rewriter", lambda q, s: (q, {}))

    result = run_agentic_rag("Draft section", session_id="s1")
    assert result["workflow"] == "docgen"
    assert called["draft_text"] == "DOCGEN_TEXT"
    assert called["execution_trace"] == ["doc_task_classifier", "doc_plan", "doc_generate_section"]


def test_qa_skips_csv(monkeypatch, tmp_path):
    csv_path = tmp_path / "drafted.csv"
    os.environ["DOCGEN_CSV_PATH"] = str(csv_path)
    payload = {
        "final_answer": "QA_TEXT",
        "answer_citations": [],
        "workflow": "qa",
        "task_type": "qa",
        "execution_trace": ["doc_task_classifier", "rag", "retrieve"],
    }
    monkeypatch.setattr(main, "graph", _StubGraph(payload))
    called = {"count": 0}
    monkeypatch.setattr("Backend.main.append_draft_csv", lambda *args, **kwargs: called.__setitem__("count", called["count"] + 1))
    monkeypatch.setattr(mem, "intelligent_query_rewriter", lambda q, s: (q, {}))
    result = run_agentic_rag("What is beam size?", session_id="s2")
    assert result["workflow"] == "qa"
    assert called["count"] == 0
