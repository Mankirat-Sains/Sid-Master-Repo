"""
Routes user queries to scenarios and execution graphs.
This is the first real decision the system makes.
"""

import re
from typing import Optional, Tuple
from dataclasses import dataclass

from load_specs import Specs, Scenario, ExecutionGraph


@dataclass
class RoutingResult:
    """Result of routing a query to a scenario and graph."""
    scenario: Scenario
    graph: ExecutionGraph
    match_reason: str
    confidence: float


def match_query_to_scenario(query: str, specs: Specs) -> Optional[RoutingResult]:
    """
    Match a user query to a scenario using trigger patterns.
    Returns the matched scenario and its execution graph.
    """
    query_lower = query.lower()
    best_match = None
    best_score = 0.0
    
    for scenario_name, scenario in specs.scenarios.items():
        score = 0.0
        matched_triggers = []
        
        # Check each trigger pattern
        for trigger in scenario.triggers:
            trigger_lower = trigger.lower()
            
            # Simple keyword matching
            if trigger_lower in query_lower:
                score += 1.0
                matched_triggers.append(trigger)
            
            # Pattern matching for dimensions (e.g., "40x80", "40'x80'")
            elif 'dimension' in trigger_lower or 'x' in trigger_lower:
                # Look for dimension patterns
                if re.search(r'\d+[\'"]?\s*x\s*\d+', query_lower):
                    score += 1.0
                    matched_triggers.append(trigger)
            
            # Pattern matching for "past project" / "existing project"
            elif 'past' in trigger_lower or 'existing' in trigger_lower:
                if 'past' in query_lower or 'existing' in query_lower or 'previous' in query_lower:
                    score += 1.0
                    matched_triggers.append(trigger)
            
            # Pattern matching for RFP/proposal/report
            elif any(word in trigger_lower for word in ['rfp', 'proposal', 'report']):
                if any(word in query_lower for word in ['rfp', 'proposal', 'report', 'respond', 'write']):
                    score += 1.0
                    matched_triggers.append(trigger)
        
        # Normalize score by number of triggers
        if len(scenario.triggers) > 0:
            score = score / len(scenario.triggers)
        
        if score > best_score:
            best_score = score
            best_match = (scenario, matched_triggers, score)
    
    if best_match and best_score > 0:
        scenario, matched_triggers, score = best_match
        
        # Get the execution graph
        if not scenario.mapped_graph:
            raise ValueError(f"Scenario '{scenario.name}' has no mapped graph defined")
        
        # Extract graph name (remove .graph.md extension if present)
        graph_name = scenario.mapped_graph.replace('.graph.md', '').strip()
        graph = specs.graphs.get(graph_name)
        
        if not graph:
            available_graphs = ', '.join(specs.graphs.keys())
            raise ValueError(
                f"Scenario '{scenario.name}' maps to non-existent graph: '{scenario.mapped_graph}' "
                f"(extracted name: '{graph_name}'). Available graphs: {available_graphs}"
            )
        
        # Build match reason
        reason = f"Query matches {len(matched_triggers)} trigger(s): {', '.join(matched_triggers[:3])}"
        
        return RoutingResult(
            scenario=scenario,
            graph=graph,
            match_reason=reason,
            confidence=score
        )
    
    return None


def route_query(query: str, specs: Specs) -> RoutingResult:
    """
    Route a user query to a scenario and execution graph.
    This is the entry point for routing.
    """
    result = match_query_to_scenario(query, specs)
    
    if not result:
        raise ValueError(f"No matching scenario found for query: '{query}'")
    
    return result

