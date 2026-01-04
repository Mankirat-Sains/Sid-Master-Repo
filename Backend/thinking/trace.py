"""
Execution trace for thinking logs
"""
from dataclasses import dataclass, field
from typing import List

@dataclass
class ExecutionTrace:
    """Holds thinking logs during execution"""
    thinking_log: List[str] = field(default_factory=list)
    
    def add_thinking(self, message: str):
        """Add a thinking log entry"""
        if message and message.strip():
            self.thinking_log.append(message.strip())