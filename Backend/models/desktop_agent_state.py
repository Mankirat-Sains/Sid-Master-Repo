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
    Includes Excel cache that's loaded on-demand and cleared after query.
    """
    # Inputs (from parent state)
    session_id: str = ""
    user_query: str = ""
    original_question: Optional[str] = None
    user_role: Optional[str] = None
    messages: List[Dict[str, str]] = field(default_factory=list)
    selected_app: str = ""  # excel | word | revit
    operation_type: str = ""  # read | write | analyze
    file_path: str = ""
    verification_result: Dict[str, Any] = field(default_factory=dict)
    desktop_tools: List[str] = field(default_factory=list)
    desktop_reasoning: str = ""
    
    # Excel Knowledge Base Cache (loaded on-demand, cleared after query)
    # Structure: {file_path: {parsed_data, metadata, last_accessed}}
    excel_cache: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Results
    desktop_result: Optional[str] = None
    desktop_citations: List[Dict] = field(default_factory=list)
