"""Document generation workflow components."""

from .document_classifier import classify_document_task, node_doc_task_classifier
from .document_planner import build_document_plan, node_doc_plan
from .section_drafter import (
    draft_section,
    node_doc_generate_section,
    SectionDraftGenerator,
    SectionGenerator,
)
from .report_drafter import draft_report, node_doc_generate_report
from .answer_adapter import adapt_generation_output, node_doc_answer_adapter
from .desktop_actions import (
    build_desktop_action_steps,
    execute_desktop_actions,
    run_desktop_execution,
    node_doc_think,
    node_doc_act,
    node_desktop_execute,
)

__all__ = [
    "classify_document_task",
    "node_doc_task_classifier",
    "build_document_plan",
    "node_doc_plan",
    "draft_section",
    "node_doc_generate_section",
    "SectionDraftGenerator",
    "SectionGenerator",
    "draft_report",
    "node_doc_generate_report",
    "adapt_generation_output",
    "node_doc_answer_adapter",
    "build_desktop_action_steps",
    "execute_desktop_actions",
    "run_desktop_execution",
    "node_doc_think",
    "node_doc_act",
    "node_desktop_execute",
]
