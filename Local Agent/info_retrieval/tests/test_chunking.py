import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from ingest.chunking import classify_chunk_type, smart_chunk, tag_chunks_with_type  # noqa: E402
from ingest.document_parser import ParsedDocument, Section  # noqa: E402


def test_smart_chunk_respects_section():
    doc = ParsedDocument(
        text="Intro text\nMore text",
        sections=[Section(title="Introduction", content="Intro text", level=1)],
    )
    chunks = smart_chunk(doc, max_tokens=10)
    assert len(chunks) == 1
    assert chunks[0]["section_title"] == "Introduction"


def test_classify_chunk_type_identifies_style():
    chunk = {"text": "This section outlines the methodology.", "section_title": "Methodology"}
    chunk_type = classify_chunk_type(chunk, {"section_type": "methodology"})
    assert chunk_type == "style"


def test_tag_chunks_with_type():
    doc = ParsedDocument(text="Calc result", sections=[Section(title="Results", content="Calc result", level=1)])
    chunks = smart_chunk(doc, max_tokens=5)
    tagged = tag_chunks_with_type(chunks, {"section_type": "results"})
    assert all("chunk_type" in item for item in tagged)
