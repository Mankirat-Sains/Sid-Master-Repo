"""
Parent State Definition
Lightweight state object for the parent graph that orchestrates subgraphs
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional


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
    original_question: Optional[str] = None  # Original user question (for storing in messages)
    user_role: Optional[str] = None  # User role for role-based preferences
    
    # Messages (persisted by checkpointer) - Follows LangGraph's pattern
    # Simple format: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
    messages: List[Dict[str, str]] = field(default_factory=list)
    
    # Routing (orchestration level)
    selected_routers: List[str] = field(default_factory=list)  # List of selected routers: "rag", "web", "desktop"
    
    # Image inputs (shared, but primarily used by DBRetrieval)
    images_base64: Optional[List[str]] = None  # Base64 encoded images from frontend
    
    # Results from subgraphs (aggregated outputs)
    db_retrieval_result: Optional[str] = None  # final_answer from DBRetrieval subgraph
    db_retrieval_citations: List[Dict] = field(default_factory=list)  # Citations from DBRetrieval
    db_retrieval_follow_up_questions: List[str] = field(default_factory=list)  # Follow-up questions
    db_retrieval_follow_up_suggestions: List[str] = field(default_factory=list)  # Follow-up suggestions
    db_retrieval_selected_projects: List[str] = field(default_factory=list)  # Projects from retrieval
    webcalcs_result: Optional[Dict] = None  # Results from WebCalcs subgraph (future)
    desktop_result: Optional[Dict] = None  # Results from DesktopAgent subgraph (future)
    build_model_result: Optional[Dict] = None  # Results from BuildModelGen subgraph (future)
