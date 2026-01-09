"""
RAG State Definition

RAGState extends the DBRetrievalState used by the DBRetrieval subgraph with
doc-generation and desktop orchestration metadata.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

from .db_retrieval_state import DBRetrievalState


@dataclass
class RAGState(DBRetrievalState):
    """Extended state that layers doc-generation metadata on top of DBRetrievalState."""

    # Router selection (legacy, still used by doc classifier / desktop router)
    selected_routers: List[str] = field(default_factory=list)

    # Workflow and doc generation routing
    workflow: Optional[str] = None  # "qa" | "docgen"
    desktop_policy: Optional[str] = None  # "required" | "optional" | "never"
    task_type: Optional[str] = None  # "qa" | "doc_section" | "doc_report"
    doc_type: Optional[str] = None
    section_type: Optional[str] = None
    doc_request: Optional[Dict[str, Any]] = None  # Structured query from doc analyzer
    requires_desktop_action: bool = False
    desktop_action_plan: Optional[Dict[str, Any]] = None  # What desktop should do (open/save/etc.)
    desktop_steps: List[Dict[str, Any]] = field(default_factory=list)
    desktop_execution: Optional[str] = None
    output_artifact_ref: Optional[Dict[str, Any]] = None  # artifact/version/path for generated doc

    # Doc generation outputs
    doc_generation_result: Optional[Dict[str, Any]] = None
    doc_generation_warnings: List[str] = field(default_factory=list)

    # Execution trace (optional, used for debugging/tests)
    execution_trace: List[str] = field(default_factory=list)
    execution_trace_verbose: List[Dict[str, Any]] = field(default_factory=list)
