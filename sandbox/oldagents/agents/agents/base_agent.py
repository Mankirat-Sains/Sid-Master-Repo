"""
Base agent classes - abstract foundation for all agents.
Following the structure from explain.txt.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class AgentState:
    """Current state of an agent."""
    task: str
    context: Dict[str, Any]
    completed_steps: List[str]
    current_step: Optional[str] = None
    results: Dict[str, Any] = None


class BaseAgent(ABC):
    """
    Abstract base class for all agents.
    All agents inherit from this and implement execute().
    """
    
    def __init__(self, name: str, tools: List = None):
        self.name = name
        self.tools = tools or []
        self.state: Optional[AgentState] = None
    
    @abstractmethod
    def execute(self, task: str, context: Dict = None) -> Dict:
        """
        Execute a task. Must be implemented by subclasses.
        
        Args:
            task: The task to execute
            context: Additional context for the task
            
        Returns:
            Dict with execution results
        """
        pass
    
    def get_available_tools(self) -> List:
        """Return list of available tools for this agent."""
        return self.tools
    
    def update_state(self, **kwargs):
        """Update agent state."""
        if self.state:
            for key, value in kwargs.items():
                if hasattr(self.state, key):
                    setattr(self.state, key, value)




