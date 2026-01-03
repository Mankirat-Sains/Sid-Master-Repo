"""
Execution trace structures - for transparency and orchestration.
Based on the old dry_run.py structure but adapted for multi-agent system.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any


class StepStatus(Enum):
    """Status of an execution step."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"
    ERROR = "error"


class ExecutionStatus(Enum):
    """Final execution status."""
    READY = "READY"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"
    BLOCKED = "BLOCKED"
    IN_PROGRESS = "IN_PROGRESS"


@dataclass
class ExecutionStep:
    """
    Represents a single step in execution trace.
    This provides transparency and enables orchestration.
    """
    step_number: int
    tool_name: str
    location: str  # "cloud" or "local"
    inputs: Dict[str, Any]  # Inputs to the tool
    outputs: Dict[str, Any]  # Outputs from the tool
    status: StepStatus
    thinking: Optional[str] = None  # Why this step was taken
    branch_taken: Optional[str] = None  # If branching occurred, which branch
    error: Optional[str] = None
    duration_ms: Optional[int] = None  # How long this step took


@dataclass
class ExecutionTrace:
    """
    Complete trace of execution.
    Provides full transparency and enables orchestration.
    """
    steps: List[ExecutionStep] = field(default_factory=list)
    final_status: ExecutionStatus = ExecutionStatus.IN_PROGRESS
    errors: List[str] = field(default_factory=list)
    available_outputs: Dict[str, Any] = field(default_factory=dict)  # Track data flow
    thinking_log: List[str] = field(default_factory=list)  # Overall thinking process


def create_step(
    step_number: int,
    tool_name: str,
    location: str,
    inputs: Dict[str, Any],
    outputs: Dict[str, Any] = None,
    status: StepStatus = StepStatus.COMPLETED,
    thinking: str = None,
    branch_taken: str = None,
    error: str = None
) -> ExecutionStep:
    """Helper to create an execution step."""
    return ExecutionStep(
        step_number=step_number,
        tool_name=tool_name,
        location=location,
        inputs=inputs,
        outputs=outputs or {},
        status=status,
        thinking=thinking,
        branch_taken=branch_taken,
        error=error
    )




