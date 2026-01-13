"""
RAG State Definition

RAGState extends DBRetrievalState with doc-generation and desktop orchestration metadata.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .db_retrieval_state import DBRetrievalState


@dataclass
class RAGState(DBRetrievalState):
    """Extended state layering doc-generation metadata on top of DBRetrievalState."""
    selected_routers: List[str] = field(default_factory=list)
    workflow: Optional[str] = None  # "qa" | "docgen"
    desktop_policy: Optional[str] = None  # "required" | "optional" | "never"
    task_type: Optional[str] = None  # "qa" | "doc_section" | "doc_report"
    doc_type: Optional[str] = None
    section_type: Optional[str] = None
    doc_request: Optional[Dict[str, Any]] = None
    requires_desktop_action: bool = False
    desktop_action_plan: Optional[Dict[str, Any]] = None
    desktop_steps: List[Dict[str, Any]] = field(default_factory=list)
    desktop_execution: Optional[str] = None
    output_artifact_ref: Optional[Dict[str, Any]] = None
    doc_generation_result: Optional[Dict[str, Any]] = None
    doc_generation_warnings: List[str] = field(default_factory=list)
    execution_trace: List[Any] = field(default_factory=list)
    execution_trace_verbose: List[Dict[str, Any]] = field(default_factory=list)

    # =========================================================================
    # Deep Desktop Agent Fields (Phase 3)
    # =========================================================================
    desktop_plan_steps: List[Dict[str, Any]] = field(default_factory=list)
    desktop_current_step: int = field(default=0)
    desktop_iteration_count: int = field(default=0)
    desktop_workspace_dir: Optional[str] = field(default=None)
    desktop_workspace_files: List[str] = field(default_factory=list)
    desktop_memories: List[Dict[str, Any]] = field(default_factory=list)
    desktop_context: Dict[str, Any] = field(default_factory=dict)
    desktop_interrupt_pending: bool = field(default=False)
    desktop_approved_actions: List[str] = field(default_factory=list)
    desktop_interrupt_data: Optional[Dict[str, Any]] = field(default=None)
    tool_execution_log: List[Dict[str, Any]] = field(default_factory=list)
    large_output_refs: Dict[str, str] = field(default_factory=dict)
    desktop_loop_result: Optional[Dict[str, Any]] = field(default=None)
