"""Compatibility shim for document section drafting."""

from document_generation.section_drafter import (
    draft_section,
    node_doc_generate_section,
    SectionDraftGenerator,
    SectionGenerator,
)

__all__ = [
    "draft_section",
    "node_doc_generate_section",
    "SectionDraftGenerator",
    "SectionGenerator",
]
