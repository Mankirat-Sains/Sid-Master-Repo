"""
Building Model Generation State Definition
Specialized state object for the BuildingModelGen subgraph.
Handles building model generation and modification.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class BuildingModelGenState:
    """
    State object specific to the BuildingModelGen subgraph.
    Contains fields needed for building model generation.
    """
    # Inputs (from orchestration state)
    session_id: str = ""
    user_query: str = ""
    original_question: Optional[str] = None
    messages: List[Dict[str, str]] = field(default_factory=list)
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Model generation metadata
    model_type: Optional[str] = None  # Type of model to generate
    model_operation: Optional[str] = None  # "create" | "modify" | "verify"
    model_parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Results
    build_model_result: Optional[Dict[str, Any]] = None
    build_model_status: Optional[str] = None
    build_model_error: Optional[str] = None
    
    # Execution trace
    execution_trace: List[str] = field(default_factory=list)
    execution_trace_verbose: List[Dict[str, Any]] = field(default_factory=list)
