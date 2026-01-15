import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from ingest.document_parser import ParsedDocument, Section, infer_sections_from_text  # noqa: E402
from ingest import document_parser  # noqa: E402


def test_infer_sections_from_text():
    text = "1. Introduction\nThis is an intro.\n2. Methodology\nSteps go here."
    sections = infer_sections_from_text(text)
    assert len(sections) == 2
    assert sections[0].title.startswith("1.")
    assert "intro" in sections[0].content.lower()


def test_parse_sample_docs():
    base = Path(__file__).resolve().parents[1] / "data" / "sample_docs"
    docx_path = base / "thermal_calculation.docx"
    pdf_path = base / "structural_calc.pdf"
    if not docx_path.exists() or not pdf_path.exists():
        # If samples are missing, skip (CI/packaging will include them)
        return

    if document_parser.docx is not None:
        docx_parsed = document_parser.parse_docx(docx_path, company_id="acme")
        assert docx_parsed.text
        assert docx_parsed.artifact_id

    if document_parser.fitz is not None:
        pdf_parsed = document_parser.parse_pdf(pdf_path, company_id="acme")
        assert pdf_parsed.text
        assert pdf_parsed.metadata.get("page_count") == len(pdf_parsed.pages)
