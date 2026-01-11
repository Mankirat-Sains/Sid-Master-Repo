import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from tier2.generator import Tier2Generator  # noqa: E402


class DummyRetriever:
    def __init__(self, content, style):
        self._content = content
        self._style = style

    def retrieve_for_query(self, query_text, company_id, chunk_type, top_k=6, filters=None):
        return self._content if chunk_type == "content" else self._style


class DummyLLM:
    def __init__(self, responses):
        self.responses = responses
        self.calls = 0

    def generate_chat(self, system_prompt, user_prompt, max_tokens=800, temperature=0.3):
        resp = self.responses[min(self.calls, len(self.responses) - 1)]
        self.calls += 1
        return resp


class DummyMetadataDB:
    def get_section_profile(self, company_id, doc_type, section_type):
        return {"avg_chars": 120, "min_chars": 100, "max_chars": 150, "avg_sentences": 2, "avg_sentence_length": 12, "avg_paragraphs": 1}


def test_draft_section_with_rewrite():
    content = [
        {"text": "Fact one about structure.", "score": 0.9, "metadata": {"artifact_id": "a1", "version_id": "v1", "heading": "H1", "page_number": 1, "chunk_id": "c1"}},
        {"text": "Fact two about load.", "score": 0.8, "metadata": {"artifact_id": "a1", "version_id": "v1", "heading": "H2", "page_number": 2, "chunk_id": "c2"}},
    ]
    style = [
        {"text": "This is a formal example of style.", "score": 0.7, "metadata": {}},
    ]
    retriever = DummyRetriever(content, style)
    llm = DummyLLM(["Too short", "This is a rewritten text that should now be within the required character limits and grounded."])
    generator = Tier2Generator(retriever=retriever, metadata_db=DummyMetadataDB(), llm_client=llm)

    result = generator.draft_section(company_id="demo", user_request="Draft conclusion for design report")
    assert result["draft_text"].startswith("This is a rewritten")
    assert result["citations"][0]["artifact_id"] == "a1"
    assert result["length_target"]["min_chars"] <= len(result["draft_text"]) <= result["length_target"]["max_chars"]
