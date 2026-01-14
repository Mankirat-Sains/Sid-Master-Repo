"""Compatibility layer for desktop agent tools (moved to `desktop_agent.tools`)."""

from desktop_agent.tools import (
    DocumentGenerationTool,
    DocGenTool,
    get_document_generation_tool,
    get_docgen_tool,
    get_doc_edit_tool,
    DocEditTool,
)

__all__ = [
    "DocumentGenerationTool",
    "DocGenTool",
    "get_document_generation_tool",
    "get_docgen_tool",
    "get_doc_edit_tool",
    "DocEditTool",
]
