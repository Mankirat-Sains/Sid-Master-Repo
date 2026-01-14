"""Compatibility shim for legacy imports.

All document-generation components now live under `Backend/document_generation/`.
This module re-exports the same node functions and helper classes to avoid
breaking legacy import paths.
"""

from document_generation import (
    node_doc_task_classifier,
    node_doc_plan,
    node_doc_think,
    node_doc_act,
    node_desktop_execute,
    node_doc_generate_section,
    node_doc_generate_report,
    node_doc_answer_adapter,
    SectionGenerator,
)

__all__ = [
    "node_doc_task_classifier",
    "node_doc_plan",
    "node_doc_think",
    "node_doc_act",
    "node_desktop_execute",
    "node_doc_generate_section",
    "node_doc_generate_report",
    "node_doc_answer_adapter",
    "SectionGenerator",
]
