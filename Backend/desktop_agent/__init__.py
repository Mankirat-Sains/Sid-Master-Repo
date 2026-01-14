"""Desktop agent package (routing, deep agent loop, tools, and docgen shims)."""

from desktop_agent.routing import node_desktop_router
from desktop_agent.deep_agent.loop import node_deep_desktop_loop
from desktop_agent.tools import (
    DocumentGenerationTool,
    DocGenTool,
    get_document_generation_tool,
    get_docgen_tool,
    get_doc_edit_tool,
    DocEditTool,
)
from desktop_agent.agents.doc_generation import (
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
    "node_desktop_router",
    "node_deep_desktop_loop",
    "DocumentGenerationTool",
    "DocGenTool",
    "get_document_generation_tool",
    "get_docgen_tool",
    "get_doc_edit_tool",
    "DocEditTool",
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
