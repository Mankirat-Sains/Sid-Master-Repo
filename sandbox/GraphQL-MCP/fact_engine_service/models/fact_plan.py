"""Pydantic models for FactPlan (LLM output)"""
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field


class Filter(BaseModel):
    """A filter condition for a fact"""
    fact: str = Field(..., description="The fact type to filter on (e.g., 'element_type', 'material')")
    op: Literal["=", "!=", ">", "<", ">=", "<=", "in", "not_in", "contains", "not_contains"] = Field(
        "=", 
        description="Comparison operator"
    )
    value: Any = Field(..., description="The value to compare against")


class Aggregation(BaseModel):
    """An aggregation operation"""
    type: Literal["count", "sum", "avg", "min", "max", "distinct"] = Field(
        ..., 
        description="Aggregation type"
    )
    by: Optional[str] = Field(None, description="Group by this fact (e.g., 'project', 'material')")
    fact: Optional[str] = Field(None, description="Fact to aggregate (for sum/avg/min/max)")


class FactPlan(BaseModel):
    """
    Structured plan for fact extraction.
    
    This is the ONLY output from the semantic planner.
    No SQL, no table names, no Speckle-specific details.
    """
    scope: Literal["project", "element", "system", "global"] = Field(
        ..., 
        description="Scope of the query"
    )
    filters: List[Filter] = Field(
        default_factory=list,
        description="Filters to apply (AND logic)"
    )
    aggregations: List[Aggregation] = Field(
        default_factory=list,
        description="Aggregations to perform"
    )
    outputs: List[str] = Field(
        default_factory=list,
        description="Facts to include in output (e.g., 'project_name', 'material', 'confidence')"
    )
    limit: int = Field(
        50,
        ge=1,
        le=1000,
        description="Maximum number of results to return"
    )
    order_by: Optional[str] = Field(
        None,
        description="Fact to order by (e.g., 'count', 'project_name')"
    )
    order_direction: Literal["asc", "desc"] = Field(
        "desc",
        description="Sort direction"
    )


