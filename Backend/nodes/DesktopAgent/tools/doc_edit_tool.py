"""
DOCX edit tool wrapper for deep desktop loop.
Calls the standalone doc-agent service to apply structured ops to a DOCX file.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class DocEditTool:
    """Wrapper around the doc-agent HTTP API."""

    def __init__(self) -> None:
        self.base_url = os.getenv("DOC_API_URL", "http://localhost:8002").rstrip("/")
        self.timeout = float(os.getenv("DOC_API_TIMEOUT", "30"))
        logger.info(f"DocEditTool using base_url={self.base_url}")

    def edit_document(
        self,
        params: Dict[str, Any],
        workspace_dir: Path,
        thread_id: str,
    ) -> Dict[str, Any]:
        doc_path = params.get("file_path") or params.get("doc_path") or params.get("filename")
        doc_id = params.get("doc_id")
        ops: List[Dict[str, Any]] = params.get("ops") or params.get("operations") or []
        save_as = params.get("save_as")

        if not doc_path:
            return {"success": False, "error": "file_path or doc_path required for edit_document"}
        if not ops:
            return {"success": False, "error": "ops[] required for edit_document"}

        resolved_path = Path(doc_path)
        if not resolved_path.is_absolute():
            resolved_path = (workspace_dir / resolved_path).resolve()
        else:
            resolved_path = resolved_path.resolve()

        payload: Dict[str, Any] = {
            "doc_id": doc_id or resolved_path.stem,
            "file_path": str(resolved_path),
            "ops": ops,
            "schema_version": 1,
        }
        if save_as:
            payload["save_as"] = save_as

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(f"{self.base_url}/api/doc/apply", json=payload)
                resp.raise_for_status()
                data = resp.json()
                return {
                    "success": True,
                    "doc_id": data.get("doc_id"),
                    "file_path": data.get("file_path"),
                    "change_summary": data.get("change_summary"),
                    "structure": data.get("structure"),
                    "output": "\n".join(data.get("change_summary", [])) if data.get("change_summary") else "",
                }
        except httpx.HTTPStatusError as exc:
            logger.error(f"DocEditTool HTTP error: {exc.response.text}")
            return {"success": False, "error": f"Doc agent error: {exc.response.text}"}
        except Exception as exc:  # pragma: no cover - defensive
            logger.error(f"DocEditTool failed: {exc}", exc_info=True)
            return {"success": False, "error": str(exc)}


_doc_edit_tool: Optional[DocEditTool] = None


def get_doc_edit_tool() -> DocEditTool:
    global _doc_edit_tool
    if _doc_edit_tool is None:
        _doc_edit_tool = DocEditTool()
    return _doc_edit_tool
