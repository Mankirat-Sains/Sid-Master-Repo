"""
Orchestration State Definition
Lightweight state object for the main graph that orchestrates subgraphs.
Contains only shared fields needed for orchestration and result aggregation.
Each subgraph has its own specialized state schema.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class OrchestrationState:
    """
    Orchestration state object that flows through the main LangGraph.
    Contains only shared fields needed for orchestration.
    Subgraphs have their own specialized state schemas.
    """
    # Session & Query (shared across all subgraphs)
    session_id: str = ""
    user_query: str = ""  # User's query (may be rewritten)
    original_question: Optional[str] = None  # Original user question
    user_role: Optional[str] = None  # User role for preferences
    data_sources: Optional[Dict[str, bool]] = None  # Database selection flags

    # Messages (persisted by checkpointer) - LangGraph pattern
    messages: List[Dict[str, str]] = field(default_factory=list)
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)

    # Routing (orchestration level)
    selected_routers: List[str] = field(default_factory=list)  # "database", "web", "desktop"

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

    # Results from subgraphs (aggregated outputs - minimal, only what's needed)
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

    # Final answer aggregation (for API response)
    final_answer: Optional[str] = None
    answer_citations: List[Dict[str, Any]] = field(default_factory=list)

    # Execution trace (optional, for debugging)
    execution_trace: List[str] = field(default_factory=list)
    execution_trace_verbose: List[Dict[str, Any]] = field(default_factory=list)
