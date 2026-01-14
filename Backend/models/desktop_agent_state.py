"""
Desktop Agent State Definition
State for DesktopAgent subgraph - includes Excel cache for on-demand reading
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any


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
    
    # Excel Knowledge Base Cache (loaded on-demand, cleared after query)
    # Structure: {file_path: {parsed_data, metadata, last_accessed}}
    excel_cache: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Results
    desktop_result: Optional[str] = None
    desktop_citations: List[Dict] = field(default_factory=list)
