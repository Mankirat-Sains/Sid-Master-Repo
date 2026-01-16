"""
Parent State Definition
Lightweight state object for the parent graph that orchestrates subgraphs.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ParentState:
    """
    Parent state object that flows through the main LangGraph.
    Contains only shared fields needed for orchestration.
    Subgraphs have their own specialized state schemas.
    """
    # Session & Query (shared across all subgraphs)
    session_id: str = ""
    user_query: str = ""  # User's query
    original_question: Optional[str] = None  # Original user question
    user_role: Optional[str] = None  # User role for preferences
    data_sources: Optional[Dict[str, bool]] = None  # Database selection flags

    # Messages (persisted by checkpointer) - LangGraph pattern
    messages: List[Dict[str, str]] = field(default_factory=list)
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)

    # Routing (orchestration level)
    selected_routers: List[str] = field(default_factory=list)  # "rag", "web", "desktop"
    selected_app: str = ""  # excel | word | revit
    operation_type: str = ""  # read | write | analyze
    file_path: str = ""
    verification_result: Dict[str, Any] = field(default_factory=dict)
    desktop_tools: List[str] = field(default_factory=list)
    desktop_reasoning: str = ""

    # Image inputs (shared, primarily for DBRetrieval)
    images_base64: Optional[List[str]] = None
    image_embeddings: Optional[List[List[float]]] = None
    image_similarity_results: List[Dict] = field(default_factory=list)
    use_image_similarity: bool = False
    query_intent: Optional[str] = None
    project_filter: Optional[str] = None
    selected_projects: List[str] = field(default_factory=list)
    needs_clarification: bool = False
    clarification_question: Optional[str] = None

    # Results from subgraphs (aggregated outputs)
    db_retrieval_result: Optional[str] = None  # final_answer from DBRetrieval subgraph
    db_retrieval_citations: List[Dict] = field(default_factory=list)
    db_retrieval_code_answer: Optional[str] = None
    db_retrieval_code_citations: List[Dict] = field(default_factory=list)
    db_retrieval_coop_answer: Optional[str] = None
    db_retrieval_coop_citations: List[Dict] = field(default_factory=list)
    db_retrieval_follow_up_questions: List[str] = field(default_factory=list)
    db_retrieval_follow_up_suggestions: List[str] = field(default_factory=list)
    db_retrieval_selected_projects: List[str] = field(default_factory=list)
    db_retrieval_route: Optional[str] = None
    db_retrieval_image_similarity_results: List[Dict] = field(default_factory=list)
    db_retrieval_expanded_queries: List[str] = field(default_factory=list)
    db_retrieval_support_score: float = 0.0
    webcalcs_result: Optional[Dict] = None
    desktop_result: Optional[Dict] = None
    build_model_result: Optional[Dict] = None

    # Doc generation / workflow metadata
    workflow: Optional[str] = None  # "qa" | "docgen"
    desktop_policy: Optional[str] = None  # "required" | "optional" | "never"
    task_type: Optional[str] = None  # "qa" | "doc_section" | "doc_report"
    doc_type: Optional[str] = None
    doc_type_variant: Optional[str] = None
    template_id: Optional[str] = None
    template_sections: List[Dict[str, Any]] = field(default_factory=list)
    section_queue: List[Dict[str, Any]] = field(default_factory=list)
    approved_sections: List[Dict[str, Any]] = field(default_factory=list)
    current_section_id: Optional[str] = None
    section_type: Optional[str] = None
    doc_request: Optional[Dict[str, Any]] = None
    requires_desktop_action: bool = False
    desktop_action_plan: Optional[Dict[str, Any]] = None
    desktop_steps: List[Dict[str, Any]] = field(default_factory=list)
    desktop_execution: Optional[str] = None
    output_artifact_ref: Optional[Dict[str, Any]] = None
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

    # Doc generation outputs
    doc_generation_result: Optional[Dict[str, Any]] = None
    doc_generation_warnings: List[str] = field(default_factory=list)
    final_answer: Optional[str] = None
    answer_citations: List[Dict[str, Any]] = field(default_factory=list)

    # Execution trace (optional)
    execution_trace: List[str] = field(default_factory=list)
    execution_trace_verbose: List[Dict[str, Any]] = field(default_factory=list)
