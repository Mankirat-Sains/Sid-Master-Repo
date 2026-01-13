"""
Tool result eviction and summarization utilities.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict
from uuid import uuid4

from config.settings import MAX_INLINE_TOOL_RESULT

logger = logging.getLogger(__name__)


class ToolResultEvictor:
    """Handles eviction of large tool outputs to files with summarization."""

    def __init__(self, max_inline_size: int = MAX_INLINE_TOOL_RESULT):
        self.max_inline_size = max_inline_size
        self.summary_length = 500

    def process_result(self, tool_name: str, result: Any, workspace_dir: Path) -> Dict[str, Any]:
        """Process tool result, evicting large outputs to files."""
        if isinstance(result, dict) or isinstance(result, (list, tuple)):
            result_str = json.dumps(result, indent=2)
        else:
            result_str = str(result)

        if len(result_str) <= self.max_inline_size:
            return {"inline": result, "evicted": False}

        logger.info(f"Evicting large result from {tool_name}: {len(result_str)} chars > {self.max_inline_size}")
        filename = f"{tool_name}_{uuid4().hex[:8]}.json"
        filepath = workspace_dir / filename
        filepath.write_text(result_str, encoding="utf-8")

        summary = self._create_summary(result, result_str)

        return {
            "evicted": True,
            "file_ref": str(filepath),
            "filename": filename,
            "summary": summary,
            "size_chars": len(result_str),
            "size_bytes": filepath.stat().st_size,
            "original_type": type(result).__name__,
        }

    def _create_summary(self, result: Any, result_str: str) -> str:
        """Create intelligent summary of evicted result."""
        if isinstance(result, list):
            return f"List with {len(result)} items. Preview: {result_str[:self.summary_length]}..."
        if isinstance(result, dict):
            keys = list(result.keys())[:10]
            extra = len(result.keys()) - len(keys)
            key_str = ", ".join(keys) + (f", ... (+{extra})" if extra > 0 else "")
            return f"Dict with keys: [{key_str}]. Preview: {result_str[:self.summary_length]}..."
        return result_str[:self.summary_length] + "..."

    def load_evicted_result(self, file_ref: str) -> Any:
        """Load an evicted result from file."""
        filepath = Path(file_ref)
        if not filepath.exists():
            logger.error(f"Evicted file not found: {file_ref}")
            return None
        content = filepath.read_text(encoding="utf-8")
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return content
        except Exception as exc:
            logger.error(f"Error loading evicted result: {exc}")
            return None


_evictor: ToolResultEvictor | None = None


def get_evictor() -> ToolResultEvictor:
    """Get global evictor instance."""
    global _evictor
    if _evictor is None:
        _evictor = ToolResultEvictor()
    return _evictor
