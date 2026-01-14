"""
Document generation tool wrapper for deep desktop loop.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import uuid4

from models.rag_state import RAGState
from utils.tool_eviction import get_evictor
from persistence.workspace_manager import get_workspace_manager

logger = logging.getLogger(__name__)


class DocumentGenerationTool:
    """Wrapper that makes the document-generation pipeline callable as a tool."""

    def __init__(self) -> None:
        self.evictor = get_evictor()
        self.workspace_mgr = get_workspace_manager()

    def generate_document(
        self,
        params: Dict[str, Any],
        workspace_dir: Path,
        thread_id: str,
        state: Optional[RAGState] = None,
    ) -> Dict[str, Any]:
        """Generate document content using the document-generation pipeline."""
        try:
            doc_request = params.get("doc_request", {}) or {}
            context = params.get("context", {}) or {}

            context_file = self._prepare_context(
                context=context,
                doc_request=doc_request,
                workspace_dir=workspace_dir,
                state=state,
            )

            result = self._generate_section(
                doc_request=doc_request,
                context_file=context_file,
                workspace_dir=workspace_dir,
            )

            processed = self._process_generation_result(result=result, workspace_dir=workspace_dir)
            docgen_payload = {
                "draft_text": processed.get("content"),
                "citations": result.get("citations", []),
                "warnings": result.get("warnings", []),
                "metadata": processed.get("metadata", {}),
                "length_target": (result.get("length_target") or {}),
                "doc_type": doc_request.get("doc_type"),
                "section_type": doc_request.get("section_type"),
            }

            return {
                "success": True,
                "output": processed.get("content"),
                "eviction": processed.get("eviction"),
                "metadata": processed.get("metadata", {}),
                "doc_generation_result": docgen_payload,
            }
        except Exception as exc:  # pragma: no cover - defensive
            logger.error(f"Error in document generation tool: {exc}", exc_info=True)
            return {"success": False, "error": str(exc)}

    def _prepare_context(
        self,
        context: Dict[str, Any],
        doc_request: Dict[str, Any],
        workspace_dir: Path,
        state: Optional[RAGState],
    ) -> Path:
        """Prepare context file for document generation."""
        full_context: Dict[str, Any] = {
            "doc_request": doc_request,
            "user_context": context,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if state:
            full_context["state_context"] = {
                "user_query": getattr(state, "user_query", None),
                "retrieved_docs": getattr(state, "retrieved_docs", {}),
                "conversation_history": getattr(state, "conversation_history", [])[-3:],
            }

        context_file = workspace_dir / f"docgen_context_{uuid4().hex[:8]}.json"
        context_file.write_text(json.dumps(full_context, indent=2), encoding="utf-8")
        logger.info(f"Prepared docgen context at {context_file}")
        return context_file

    def _generate_section(
        self,
        doc_request: Dict[str, Any],
        context_file: Path,
        workspace_dir: Path,
    ) -> Dict[str, Any]:
        """Call existing document-generation logic."""
        try:
            from document_generation import SectionGenerator

            generator = SectionGenerator()
            result = generator.generate(
                doc_request=doc_request,
                context_path=str(context_file),
                output_dir=str(workspace_dir),
            )
            return result
        except Exception as exc:  # pragma: no cover - defensive
            # Fall back to a lightweight mock result rather than failing the loop
            logger.warning(f"Document generation unavailable, returning fallback content: {exc}")
            return {
                "draft_text": f"# Document\n\nGenerated content for: {doc_request.get('title', 'Untitled')}",
                "sections": [],
                "metadata": {"fallback": True, "reason": f"Document generation unavailable: {exc}"},
            }

    def _process_generation_result(self, result: Dict[str, Any], workspace_dir: Path) -> Dict[str, Any]:
        """Process doc generation result with output eviction."""
        draft_text = result.get("draft_text", "") or ""

        if len(draft_text) > self.evictor.max_inline_size:
            logger.info(f"Evicting large document-generation output: {len(draft_text)} chars")
            output_file = workspace_dir / f"doc_output_{uuid4().hex[:8]}.md"
            output_file.write_text(draft_text, encoding="utf-8")
            summary = draft_text[: self.evictor.summary_length] + "... [truncated]"
            return {
                "content": summary,
                "eviction": {
                    "evicted": True,
                    "file_ref": str(output_file),
                    "filename": output_file.name,
                    "full_size": len(draft_text),
                },
                "metadata": result.get("metadata", {}),
            }

        eviction = self.evictor.process_result("docgen", draft_text, workspace_dir)
        if eviction.get("evicted"):
            return {
                "content": eviction.get("summary"),
                "eviction": eviction,
                "metadata": result.get("metadata", {}),
            }

        return {
            "content": draft_text,
            "eviction": {"evicted": False},
            "metadata": result.get("metadata", {}),
        }


_document_generation_tool: DocumentGenerationTool | None = None


def get_document_generation_tool() -> DocumentGenerationTool:
    """Get global document-generation tool instance."""
    global _document_generation_tool
    if _document_generation_tool is None:
        _document_generation_tool = DocumentGenerationTool()
    return _document_generation_tool


# Backwards-compatible aliases
DocGenTool = DocumentGenerationTool
get_docgen_tool = get_document_generation_tool

__all__ = [
    "DocumentGenerationTool",
    "DocGenTool",
    "get_document_generation_tool",
    "get_docgen_tool",
]
