"""
Desktop Agent State Definition
State for DesktopAgent subgraph - includes Excel cache for on-demand reading.
Structure aligned with commit 32b6666 (see CODEBASE_STRUCTURE_32b6666.md) while
remaining backward compatible with the current desktop agent implementation.
"""
from dataclasses import dataclass, field
from typing import Annotated, List, Dict, Optional, Any, TypedDict

from langgraph.graph.message import add_messages


class DesktopAgentStateSchema(TypedDict, total=False):
    """
    Lightweight schema for desktop agent routing/verification flows.
    Matches the 32b6666-era structure (see CODEBASE_STRUCTURE_32b6666.md) and
    can be used for TypedDict-style state passing.
    """

    messages: Annotated[list, add_messages]
    selected_app: str  # excel, word, revit
    operation_type: str  # read, write, analyze
    file_path: str
    verification_result: dict
    desktop_tools: List[str]
    desktop_reasoning: str


@dataclass
class DesktopAgentState:
    """
    State object for DesktopAgent subgraph.
    Contains all desktop-specific fields including Excel, Word, and Revit operations.
    Includes Excel cache that's loaded on-demand and cleared after query.
    """
    # Inputs (from orchestration state)
    session_id: str = ""
    user_query: str = ""
    original_question: Optional[str] = None
    user_role: Optional[str] = None
    messages: List[Dict[str, str]] = field(default_factory=list)
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Desktop routing
    selected_app: str = ""  # excel | word | revit
    operation_type: str = ""  # read | write | analyze
    file_path: str = ""
    verification_result: Dict[str, Any] = field(default_factory=dict)
    desktop_tools: List[str] = field(default_factory=list)
    desktop_reasoning: str = ""
    
    # Workflow and task classification
    workflow: Optional[str] = None  # "qa" | "docgen"
    desktop_policy: Optional[str] = None  # "required" | "optional" | "never"
    task_type: Optional[str] = None  # "qa" | "doc_section" | "doc_report"
    doc_type: Optional[str] = None
    section_type: Optional[str] = None
    doc_request: Optional[Dict[str, Any]] = None
    
    # Desktop action planning
    requires_desktop_action: bool = False
    desktop_action_plan: Optional[Dict[str, Any]] = None
    desktop_steps: List[Dict[str, Any]] = field(default_factory=list)
    desktop_execution: Optional[str] = None
    output_artifact_ref: Optional[Dict[str, Any]] = None
    
    # Deep desktop agent fields
    desktop_plan_steps: List[Dict[str, Any]] = field(default_factory=list)
    desktop_current_step: int = 0
    desktop_iteration_count: int = 0
    desktop_workspace_dir: Optional[str] = None
    desktop_workspace_files: List[str] = field(default_factory=list)
    desktop_memories: List[Dict[str, Any]] = field(default_factory=list)
    desktop_context: Dict[str, Any] = field(default_factory=dict)
    desktop_interrupt_pending: bool = False
    desktop_approved_actions: List[str] = field(default_factory=list)
    desktop_interrupt_data: Optional[Dict[str, Any]] = None
    tool_execution_log: List[Dict[str, Any]] = field(default_factory=list)
    large_output_refs: Dict[str, str] = field(default_factory=dict)
    desktop_loop_result: Optional[Dict[str, Any]] = None
    
    # Doc generation fields
    doc_generation_result: Optional[Dict[str, Any]] = None
    doc_generation_warnings: List[str] = field(default_factory=list)
    needs_retrieval: bool = True
    retrieval_completed: bool = False
    
    # Excel Knowledge Base Cache (loaded on-demand, cleared after query)
    # Structure: {file_path: {parsed_data, metadata, last_accessed}}
    excel_cache: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Results
    desktop_result: Optional[Dict[str, Any]] = None
    desktop_citations: List[Dict] = field(default_factory=list)
    final_answer: Optional[str] = None
    answer_citations: List[Dict[str, Any]] = field(default_factory=list)
    
    # Execution trace
    execution_trace: List[str] = field(default_factory=list)
    execution_trace_verbose: List[Dict[str, Any]] = field(default_factory=list)