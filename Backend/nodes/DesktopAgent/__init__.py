"""Compatibility namespace for desktop agent nodes (logic now in `desktop_agent`)."""

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

__all__ = [
    "node_desktop_router",
    "node_deep_desktop_loop",
    "DocumentGenerationTool",
    "DocGenTool",
    "get_document_generation_tool",
    "get_docgen_tool",
    "get_doc_edit_tool",
    "DocEditTool",
]
