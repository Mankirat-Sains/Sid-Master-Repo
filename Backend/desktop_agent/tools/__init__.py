"""Desktop agent tools."""

from .document_generation_tool import (
    DocumentGenerationTool,
    DocGenTool,
    get_document_generation_tool,
    get_docgen_tool,
)
from .document_edit_tool import get_doc_edit_tool, DocEditTool

__all__ = [
    "DocumentGenerationTool",
    "DocGenTool",
    "get_document_generation_tool",
    "get_docgen_tool",
    "get_doc_edit_tool",
    "DocEditTool",
]
