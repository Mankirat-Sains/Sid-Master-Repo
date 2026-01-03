"""Confidence scoring utilities"""
from typing import List, Dict, Any
from models.fact_result import FactValue


def compute_aggregate_confidence(fact_values: List[FactValue]) -> float:
    """
    Compute aggregate confidence from multiple fact values.
    
    Uses weighted average based on evidence count.
    
    Args:
        fact_values: List of FactValue objects
    
    Returns:
        Aggregate confidence (0.0 to 1.0)
    """
    if not fact_values:
        return 0.0
    
    total_weight = 0.0
    weighted_sum = 0.0
    
    for fv in fact_values:
        # Weight by evidence count (more evidence = higher weight)
        weight = 1.0 + len(fv.evidence) * 0.1
        weighted_sum += fv.confidence * weight
        total_weight += weight
    
    if total_weight == 0:
        return 0.0
    
    return min(1.0, weighted_sum / total_weight)


def compute_project_confidence(project_facts: Dict[str, Any]) -> float:
    """
    Compute overall confidence for a project.
    
    Args:
        project_facts: Project facts dict
    
    Returns:
        Project confidence (0.0 to 1.0)
    """
    # Collect all fact confidences
    confidences = []
    
    # Check element facts
    elements = project_facts.get("elements", {})
    for elem_type, materials in elements.items():
        # Confidence based on element count (more elements = higher confidence)
        total_elements = sum(materials.values()) if isinstance(materials, dict) else 0
        if total_elements > 0:
            # More elements = higher confidence (capped)
            elem_confidence = min(0.95, 0.5 + (total_elements / 100.0) * 0.45)
            confidences.append(elem_confidence)
    
    if not confidences:
        return 0.5  # Default moderate confidence
    
    # Average confidence
    return sum(confidences) / len(confidences)


def adjust_confidence_for_evidence_count(
    base_confidence: float,
    evidence_count: int
) -> float:
    """
    Adjust confidence based on evidence count.
    
    More evidence increases confidence (up to a limit).
    
    Args:
        base_confidence: Base confidence score
        evidence_count: Number of evidence items
    
    Returns:
        Adjusted confidence
    """
    # Each piece of evidence adds up to 0.05 confidence
    evidence_bonus = min(0.1, evidence_count * 0.02)
    return min(1.0, base_confidence + evidence_bonus)


def compute_uncertainty_level(confidence: float) -> str:
    """
    Convert confidence score to uncertainty level description.
    
    Args:
        confidence: Confidence score (0.0 to 1.0)
    
    Returns:
        Uncertainty description
    """
    if confidence >= 0.8:
        return "Low"
    elif confidence >= 0.6:
        return "Moderate"
    elif confidence >= 0.4:
        return "High"
    else:
        return "Very High"


