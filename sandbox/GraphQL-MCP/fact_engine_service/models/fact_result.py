"""Pydantic models for extracted facts"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Evidence(BaseModel):
    """Evidence supporting a fact extraction"""
    source: str = Field(..., description="Source of evidence (e.g., 'element.data.type', 'material.name')")
    value: Any = Field(..., description="The actual value found")
    path: str = Field(..., description="JSON path to the value")


class FactValue(BaseModel):
    """A single extracted fact value"""
    value: Any = Field(..., description="The extracted value")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0 to 1.0)"
    )
    evidence: List[Evidence] = Field(
        default_factory=list,
        description="Evidence supporting this extraction"
    )


class ElementFacts(BaseModel):
    """Facts extracted for a single element"""
    element_id: str
    facts: Dict[str, FactValue] = Field(
        default_factory=dict,
        description="Map of fact_name -> FactValue"
    )


class ProjectFacts(BaseModel):
    """Aggregated facts for a project"""
    project_id: str
    project_name: Optional[str] = None
    project_number: Optional[str] = None
    elements: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Nested structure: {element_type: {material: count, ...}}"
    )
    systems: Dict[str, bool] = Field(
        default_factory=dict,
        description="System presence: {system_type: exists}"
    )
    summary: Dict[str, Any] = Field(
        default_factory=dict,
        description="Project-level summary facts"
    )
    confidence: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Overall confidence for this project"
    )
    evidence: List[Evidence] = Field(
        default_factory=list,
        description="Aggregated evidence"
    )


class FactResult(BaseModel):
    """Complete result from fact extraction"""
    projects: Dict[str, ProjectFacts] = Field(
        default_factory=dict,
        description="Map of project_id -> ProjectFacts"
    )
    global_facts: Dict[str, Any] = Field(
        default_factory=dict,
        description="Global-level aggregated facts"
    )
    execution_time_ms: float = Field(..., description="Execution time in milliseconds")
    total_elements_processed: int = Field(..., description="Number of elements processed")


