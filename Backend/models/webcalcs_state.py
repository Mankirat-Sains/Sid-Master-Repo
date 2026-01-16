"""
WebCalcs State Definition
Specialized state object for the WebCalcs subgraph.
Handles web-based calculations and Python tool execution.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class WebCalcsState:
    """
    State object specific to the WebCalcs subgraph.
    Contains fields needed for web-based calculations and Python tools.
    """
    # Inputs (from orchestration state)
    session_id: str = ""
    user_query: str = ""
    original_question: Optional[str] = None
    messages: List[Dict[str, str]] = field(default_factory=list)
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Routing (WebCalcs-specific)
    selected_routers: List[str] = field(default_factory=list)  # Should include "web"
    web_tools: List[str] = field(default_factory=list)  # Selected web tools
    web_reasoning: str = ""
    
    # Results
    webcalcs_result: Optional[Dict[str, Any]] = None
    webcalcs_citations: List[Dict[str, Any]] = field(default_factory=list)
    webcalcs_error: Optional[str] = None
    
    # Execution trace
    execution_trace: List[str] = field(default_factory=list)
    execution_trace_verbose: List[Dict[str, Any]] = field(default_factory=list)
