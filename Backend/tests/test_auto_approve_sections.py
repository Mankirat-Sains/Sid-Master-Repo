import os
from types import SimpleNamespace

import Backend.nodes.DesktopAgent.doc_generation.section_generator as sg
from Backend.nodes.DesktopAgent.doc_generation import approval as doc_approval
from models.rag_state import RAGState


class StubGen:
    def __init__(self):
        self.calls = []

    def draft_section(self, company_id, user_request, overrides=None):
        self.calls.append(overrides or {})
        return {
            "draft_text": f"draft for {overrides.get('section_type')}",
            "citations": [{"id": "c1"}],
            "metadata": {"section_id": overrides.get("section_id"), "template_id": overrides.get("template_id")},
        }


def _make_state(section_queue=None, template_sections=None):
    return RAGState(
        user_query="Generate intro",
        doc_type="design_report",
        section_type=None,
        template_id="tmpl-auto",
        template_sections=template_sections,
        section_queue=section_queue,
        approved_sections=[],
    )


def test_auto_approve_unlocks_next_section(monkeypatch):
    section_queue = [
        {"section_id": "s1", "section_type": "intro", "position_order": 1, "status": "pending"},
        {"section_id": "s2", "section_type": "methodology", "position_order": 2, "status": "locked"},
        {"section_id": "s3", "section_type": "results", "position_order": 3, "status": "locked"},
    ]
    template_sections = list(section_queue)
    state = _make_state(section_queue=section_queue, template_sections=template_sections)

    stub = StubGen()
    monkeypatch.setattr(sg, "_load_services", lambda: {"generator": stub})
    monkeypatch.setattr(doc_approval, "AUTO_APPROVE_SECTIONS", True)

    res = sg.node_doc_generate_section(state)
    section_status = {s["section_id"]: s["status"] for s in res["section_status"]}

    # Still single-section generation
    assert len(stub.calls) == 1
    assert stub.calls[0].get("section_id") == "s1"

    # Current section auto-approved; next unlocked; remaining locked
    assert section_status["s1"] == "approved"
    assert section_status["s2"] == "pending"
    assert section_status["s3"] == "locked"
