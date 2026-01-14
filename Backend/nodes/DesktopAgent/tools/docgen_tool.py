"""Compatibility shim for document generation tool."""

from desktop_agent.tools import (
    DocumentGenerationTool,
    DocGenTool,
    get_document_generation_tool,
    get_docgen_tool,
)

__all__ = [
    "DocumentGenerationTool",
    "DocGenTool",
    "get_document_generation_tool",
    "get_docgen_tool",
]
