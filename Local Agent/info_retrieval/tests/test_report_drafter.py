import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from tier2.report_drafter import ReportDrafter  # noqa: E402
from tier2.generator import Tier2Generator  # noqa: E402


class DummyGenerator(Tier2Generator):
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def draft_section(self, company_id, user_request, overrides=None):
        section = overrides.get("section_type") if overrides else None
        self.calls.append(section)
        resp = self.responses.get(section, {})
        return {
            "draft_text": resp.get("text", "[TBD – insufficient source content]"),
            "length_target": resp.get("length_target", {"min_chars": 50, "max_chars": 100}),
            "citations": resp.get("citations", []),
            "doc_type": overrides.get("doc_type") if overrides else None,
            "section_type": section,
            "warnings": resp.get("warnings", []),
        }


class DummyMetadataDB:
    def __init__(self, section_types):
        self.section_types = section_types

    def _connect(self):
        # Return a dummy connection with context manager
        import sqlite3
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        conn.execute("CREATE TABLE chunks(section_type TEXT, company_id TEXT, doc_type TEXT);")
        for st in self.section_types:
            conn.execute("INSERT INTO chunks(section_type, company_id, doc_type) VALUES (?, ?, ?);", (st, "demo", "design_report"))
        conn.commit()
        return conn


def test_report_drafter_infers_sections_and_combines_text():
    responses = {
        "introduction": {"text": "Intro text", "citations": [{"c": 1}]},
        "methodology": {"text": "Method text", "citations": [{"c": 2}]},
    }
    gen = DummyGenerator(responses)
    metadata_db = DummyMetadataDB(section_types=["introduction", "methodology"])
    drafter = ReportDrafter(generator=gen, metadata_db=metadata_db)

    result = drafter.draft_report(company_id="demo", user_request="Draft full report", doc_type="design_report")
    assert "Introduction" in result["combined_text"]
    assert "Method text" in result["combined_text"]
    assert len(result["sections"]) == 2
    assert result["sections"][0]["section_type"] == "introduction"
    assert result["sections"][1]["section_type"] == "methodology"
    assert not result["warnings"]


def test_report_drafter_skips_when_no_content():
    responses = {
        "introduction": {"text": "[TBD – insufficient source content]", "warnings": ["missing"]},
        "conclusion": {"text": "Conclusion text", "citations": []},
    }
    gen = DummyGenerator(responses)
    metadata_db = DummyMetadataDB(section_types=["introduction", "conclusion"])
    drafter = ReportDrafter(generator=gen, metadata_db=metadata_db)

    result = drafter.draft_report(company_id="demo", user_request="Draft full report", doc_type="design_report")
    # intro skipped
    assert len(result["sections"]) == 1
    assert result["sections"][0]["section_type"] == "conclusion"
    assert any("skipped" in w for w in result["warnings"])
