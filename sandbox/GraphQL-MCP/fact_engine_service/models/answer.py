"""Pydantic models for final answers"""
from typing import List, Optional
from pydantic import BaseModel, Field


class Answer(BaseModel):
    """Final answer to a user question"""
    answer: str = Field(..., description="Human-readable answer")
    explanation: str = Field(..., description="Explanation of how the answer was derived")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall confidence in the answer"
    )
    uncertainty: Optional[str] = Field(
        None,
        description="Description of any uncertainty or limitations"
    )
    supporting_facts: List[str] = Field(
        default_factory=list,
        description="List of key facts that support this answer"
    )
    project_count: Optional[int] = Field(
        None,
        description="Number of projects involved"
    )


