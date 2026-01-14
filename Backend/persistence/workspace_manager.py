"""
Workspace manager for ephemeral per-thread storage used by the deep desktop agent.
"""
import logging
import os
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)


class WorkspaceManager:
    """Manages ephemeral workspace files for deep agent operations."""

    def __init__(self, base_path: Optional[str] = None):
        # Default to repo-local workspace unless explicitly overridden
        default_repo_workspace = Path(__file__).resolve().parents[2] / "workspace"
        preferred = Path(base_path or os.getenv("WORKSPACE_BASE_PATH") or default_repo_workspace)
        fallback = default_repo_workspace
        self.retention_hours = int(os.getenv("WORKSPACE_RETENTION_HOURS", "24"))

        self.base = preferred
        try:
            self.base.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            logger.warning(f"Workspace base '{preferred}' not writable ({exc}), falling back to '{fallback}'")
            self.base = fallback
            self.base.mkdir(parents=True, exist_ok=True)

        logger.info(f"WorkspaceManager initialized at {self.base}")

    def get_thread_workspace(self, thread_id: str) -> Path:
        """Get or create workspace directory for a thread and clean old files."""
        workspace = self.base / thread_id
        workspace.mkdir(parents=True, exist_ok=True)
        self._clean_old_files(workspace)
        return workspace

    def write_file(self, thread_id: str, filename: str, content: str) -> Path:
        """Write content to a file in the thread workspace."""
        workspace = self.get_thread_workspace(thread_id)
        filepath = workspace / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(content, encoding="utf-8")
        logger.info(f"Wrote {len(content)} chars to {filepath}")
        return filepath

    def read_file(self, thread_id: str, filename: str) -> Optional[str]:
        """Read content from a file in the thread workspace."""
        workspace = self.get_thread_workspace(thread_id)
        filepath = workspace / filename
        if not filepath.exists():
            logger.warning(f"File not found: {filepath}")
            return None
        content = filepath.read_text(encoding="utf-8")
        logger.info(f"Read {len(content)} chars from {filepath}")
        return content

    def list_files(self, thread_id: str, pattern: str = "*") -> List[Path]:
        """List files in the thread workspace matching a glob pattern."""
        workspace = self.get_thread_workspace(thread_id)
        if not workspace.exists():
            return []
        files = list(workspace.glob(pattern))
        logger.info(f"Found {len(files)} files matching '{pattern}' in {workspace}")
        return files

    def delete_file(self, thread_id: str, filename: str) -> bool:
        """Delete a file from the thread workspace."""
        workspace = self.get_thread_workspace(thread_id)
        filepath = workspace / filename
        if not filepath.exists():
            logger.warning(f"File not found for deletion: {filepath}")
            return False
        filepath.unlink()
        logger.info(f"Deleted file: {filepath}")
        return True

    def clear_workspace(self, thread_id: str) -> None:
        """Clear all files in the thread workspace."""
        workspace = self.base / thread_id
        if workspace.exists():
            shutil.rmtree(workspace)
            logger.info(f"Cleared workspace: {workspace}")

    def get_workspace_snapshot(self, thread_id: str) -> Dict[str, object]:
        """Get snapshot of current workspace state."""
        workspace = self.get_thread_workspace(thread_id)
        files = []
        for filepath in workspace.rglob("*"):
            if filepath.is_file():
                stat = filepath.stat()
                files.append(
                    {
                        "path": str(filepath.relative_to(workspace)),
                        "size_bytes": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    }
                )
        return {
            "workspace_path": str(workspace),
            "file_count": len(files),
            "files": files,
        }

    def get_size_stats(self, thread_id: str) -> Dict[str, object]:
        """Get storage statistics for thread workspace."""
        workspace = self.get_thread_workspace(thread_id)
        total_size = 0
        file_count = 0
        for filepath in workspace.rglob("*"):
            if filepath.is_file():
                total_size += filepath.stat().st_size
                file_count += 1
        return {
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "file_count": file_count,
        }

    def _clean_old_files(self, workspace: Path) -> None:
        """Remove files older than the retention period."""
        if not workspace.exists():
            return
        cutoff_time = time.time() - (self.retention_hours * 3600)
        cleaned = 0
        for filepath in workspace.rglob("*"):
            if filepath.is_file() and filepath.stat().st_mtime < cutoff_time:
                try:
                    filepath.unlink()
                    cleaned += 1
                except Exception as exc:
                    logger.warning(f"Failed to clean old file {filepath}: {exc}")
        if cleaned:
            logger.info(f"Cleaned {cleaned} old files from {workspace}")


_workspace_manager: Optional[WorkspaceManager] = None


def get_workspace_manager() -> WorkspaceManager:
    """Get global workspace manager instance."""
    global _workspace_manager
    if _workspace_manager is None:
        _workspace_manager = WorkspaceManager()
    return _workspace_manager
