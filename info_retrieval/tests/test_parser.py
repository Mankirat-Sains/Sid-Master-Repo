import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from ingest.document_parser import ParsedDocument, Section, infer_sections_from_text  # noqa: E402


def test_infer_sections_from_text():
    text = "1. Introduction\nThis is an intro.\n2. Methodology\nSteps go here."
    sections = infer_sections_from_text(text)
    assert len(sections) == 2
    assert sections[0].title.startswith("1.")
    assert "intro" in sections[0].content.lower()
