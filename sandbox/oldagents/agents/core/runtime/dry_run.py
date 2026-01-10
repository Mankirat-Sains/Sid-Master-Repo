"""
Dry-run executor - walks the graph and simulates execution.
This is where the brain finally "does something".
"""

from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

from load_specs import ExecutionGraph, GraphNode, Intent, Specs


class ExecutionStatus(Enum):
    """Final execution status."""
    READY = "READY"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"
    BLOCKED = "BLOCKED"


@dataclass
class ExecutionStep:
    """Represents a single step in execution trace."""
    step_number: int
    intent_name: str
    location: str
    inputs: Dict[str, str]
    outputs: Dict[str, str]
    status: str  # "completed", "blocked", "skipped"
    branch_taken: Optional[str] = None


@dataclass
class ExecutionTrace:
    """Complete trace of dry-run execution."""
    steps: List[ExecutionStep] = field(default_factory=list)
    final_status: ExecutionStatus = ExecutionStatus.BLOCKED
    errors: List[str] = field(default_factory=list)


def simulate_output(intent_name: str, intent: Intent, inputs: Dict[str, str]) -> Dict[str, str]:
    """
    Simulate outputs for an intent based on its definition.
    This is where we generate mock data to prove data flow.
    """
    outputs = {}
    
    for output_name in intent.produced_outputs:
        # Generate mock output based on output name
        if 'id' in output_name.lower():
            outputs[output_name] = f"[simulated-{output_name}-123]"
        elif 'constraint' in output_name.lower() or 'criteria' in output_name.lower():
            # Extract from inputs if available
            if 'user_query' in inputs:
                query = inputs['user_query']
                # Try to extract dimensions
                import re
                dim_match = re.search(r'(\d+[\'"]?\s*x\s*\d+)', query)
                if dim_match:
                    # Dimensions found - mark as complete
                    outputs[output_name] = f"{{ dimensions: '{dim_match.group(1)}', complete: true }}"
                else:
                    # No dimensions found - mark as incomplete
                    outputs[output_name] = "{ dimensions: 'unknown', complete: false }"
            else:
                outputs[output_name] = "{ dimensions: 'unknown', complete: false }"
        elif 'score' in output_name.lower():
            outputs[output_name] = "[0.95, 0.87, 0.72]"
        elif 'summary' in output_name.lower() or 'metadata' in output_name.lower():
            outputs[output_name] = f"[{{ id: 'proj-123', name: 'Sample Project', ... }}]"
        elif 'text' in output_name.lower():
            outputs[output_name] = "[simulated extracted text content]"
        elif 'structure' in output_name.lower():
            outputs[output_name] = "[simulated document structure]"
        elif 'topic' in output_name.lower():
            outputs[output_name] = "['topic1', 'topic2', 'topic3']"
        elif 'document' in output_name.lower() or 'artifact' in output_name.lower():
            outputs[output_name] = "[simulated reference documents]"
        elif 'guidance' in output_name.lower() or 'suggestion' in output_name.lower():
            outputs[output_name] = "[simulated guidance content]"
        elif 'question' in output_name.lower():
            outputs[output_name] = "['What building type?', 'What material?']"
        else:
            outputs[output_name] = f"[simulated-{output_name}]"
    
    return outputs


def evaluate_branch_condition(condition: str, outputs: Dict[str, str]) -> bool:
    """
    Evaluate a branch condition against current outputs.
    Simple evaluation for now - can be enhanced.
    """
    condition_lower = condition.lower()
    
    # Check for "incomplete" conditions
    if 'incomplete' in condition_lower:
        # Extract the output name from condition (e.g., "dimension_constraints are incomplete")
        # Find which output the condition refers to
        for output_key in outputs.keys():
            if output_key.lower() in condition_lower:
                # Check this specific output
                output_value = outputs[output_key]
                if isinstance(output_value, str):
                    value_lower = output_value.lower()
                    # If it says complete: true, condition is NOT met (don't branch)
                    if 'complete: true' in value_lower:
                        return False
                    # If it says complete: false or incomplete, condition IS met (branch)
                    if 'complete: false' in value_lower or 'incomplete' in value_lower:
                        return True
        
        # Fallback: check all outputs for completeness markers
        for output_key, output_value in outputs.items():
            if isinstance(output_value, str):
                value_lower = output_value.lower()
                if 'complete: false' in value_lower or 'incomplete: true' in value_lower:
                    return True
                if 'complete: true' in value_lower:
                    return False
        
        # Default to not branching if we can't determine
        return False
    
    # Check for "no document_id" or similar
    if 'no ' in condition_lower or 'none' in condition_lower:
        # Check if key outputs are missing or None
        for key in outputs.keys():
            if 'id' in key.lower() and outputs[key] in ['none', 'None', '']:
                return True
        return False
    
    # Default: condition not met
    return False


def validate_graph(graph: ExecutionGraph, specs: Specs) -> List[str]:
    """
    Validate that a graph is legally runnable.
    Returns list of errors (empty if valid).
    """
    errors = []
    
    # Check all intents exist
    for node in graph.nodes:
        if node.intent_name not in specs.intents:
            errors.append(f"Intent '{node.intent_name}' not found in catalog")
    
    # Check input dependencies
    available_outputs: Set[str] = set()
    available_outputs.add('user_query')  # Always available from initial query
    
    for node in graph.nodes:
        # Clarification/terminal nodes are special - they can ask for missing info
        # They don't need all inputs upfront because they're requesting them from the user
        is_clarification_node = (
            node.intent_name == 'request_clarification' or 
            node.is_terminal
        )
        
        # Check if required inputs are available (skip for clarification nodes)
        if not is_clarification_node:
            for required_input in node.inputs:
                if required_input not in available_outputs:
                    errors.append(f"Node '{node.intent_name}' requires input '{required_input}' which is not available")
        
        # Add this node's outputs to available outputs
        intent = specs.intents.get(node.intent_name)
        if intent:
            available_outputs.update(intent.produced_outputs)
        else:
            available_outputs.update(node.outputs)
    
    return errors


def execute_dry_run(graph: ExecutionGraph, user_query: str, specs: Specs, ai_executor=None) -> ExecutionTrace:
    """
    Execute a dry-run of the graph - walk it step by step without real execution.
    """
    trace = ExecutionTrace()
    
    # Validate graph first
    validation_errors = validate_graph(graph, specs)
    if validation_errors:
        trace.errors.extend(validation_errors)
        trace.final_status = ExecutionStatus.BLOCKED
        return trace
    
    # Initialize execution state
    available_outputs: Dict[str, str] = {'user_query': user_query}
    step_number = 1
    visited_nodes: Set[int] = set()
    
    # Walk the graph
    i = 0
    while i < len(graph.nodes):
        if i in visited_nodes:
            trace.errors.append(f"Circular dependency detected at node {i}")
            trace.final_status = ExecutionStatus.BLOCKED
            break
        
        visited_nodes.add(i)
        node = graph.nodes[i]
        intent = specs.intents.get(node.intent_name)
        
        if not intent:
            trace.errors.append(f"Intent '{node.intent_name}' not found in catalog")
            trace.final_status = ExecutionStatus.BLOCKED
            break
        
        # Check if inputs are available
        missing_inputs = []
        node_inputs = {}
        
        # Clarification nodes can generate their inputs dynamically
        is_clarification = node.intent_name == 'request_clarification'
        
        for required_input in node.inputs:
            if required_input in available_outputs:
                node_inputs[required_input] = available_outputs[required_input]
            else:
                missing_inputs.append(required_input)
        
        # For clarification nodes, generate missing_fields if needed
        if is_clarification and 'missing_fields' in missing_inputs:
            node_inputs['missing_fields'] = "dimensions, building type, material"
            missing_inputs.remove('missing_fields')
        
        if missing_inputs and not is_clarification:
            step = ExecutionStep(
                step_number=step_number,
                intent_name=node.intent_name,
                location=node.location,
                inputs=node_inputs,
                outputs={},
                status="blocked",
            )
            trace.steps.append(step)
            trace.errors.append(f"Node '{node.intent_name}' blocked: missing inputs {missing_inputs}")
            trace.final_status = ExecutionStatus.BLOCKED
            break
        
        # Execute intent (AI if available, otherwise simulate)
        if ai_executor and ai_executor.enabled:
            # Try AI execution first
            ai_outputs = ai_executor.execute_intent(node.intent_name, intent, node_inputs)
            if ai_outputs:
                simulated_outputs = ai_outputs
            else:
                # Fall back to simulation
                simulated_outputs = simulate_output(node.intent_name, intent, node_inputs)
        else:
            # Use simulation
            simulated_outputs = simulate_output(node.intent_name, intent, node_inputs)
        
        # Update available outputs
        available_outputs.update(simulated_outputs)
        
        # Check for terminal node
        if node.is_terminal:
            step = ExecutionStep(
                step_number=step_number,
                intent_name=node.intent_name,
                location=node.location,
                inputs=node_inputs,
                outputs=simulated_outputs,
                status="completed",
            )
            trace.steps.append(step)
            
            # Determine final status
            if node.intent_name == 'request_clarification':
                trace.final_status = ExecutionStatus.NEEDS_CLARIFICATION
            else:
                trace.final_status = ExecutionStatus.READY
            break
        
        # Check for branch condition
        branch_taken = None
        if node.branch_condition:
            condition_met = evaluate_branch_condition(node.branch_condition, simulated_outputs)
            
            # Debug: log branch evaluation (commented out for production)
            # print(f"DEBUG: Node {node.intent_name}, condition: {node.branch_condition}, met: {condition_met}, outputs: {simulated_outputs}")
            
            if condition_met and node.branch_target:
                # Condition is TRUE - take the branch
                # Find the target node
                target_found = False
                for j, target_node in enumerate(graph.nodes):
                    if target_node.intent_name == node.branch_target:
                        # Generate missing_fields if branching to request_clarification
                        if target_node.intent_name == 'request_clarification':
                            # Generate missing_fields based on what's incomplete
                            available_outputs['missing_fields'] = "dimensions, building type, material"
                        
                        step = ExecutionStep(
                            step_number=step_number,
                            intent_name=node.intent_name,
                            location=node.location,
                            inputs=node_inputs,
                            outputs=simulated_outputs,
                            status="completed",
                            branch_taken=node.branch_target,
                        )
                        trace.steps.append(step)
                        step_number += 1
                        i = j
                        target_found = True
                        break
                
                if not target_found:
                    trace.errors.append(f"Branch target '{node.branch_target}' not found")
                    trace.final_status = ExecutionStatus.BLOCKED
                    break
                
                continue
            elif not condition_met and node.branch_target:
                # Condition is FALSE - don't take the branch
                # Complete current step and continue to next node (which should NOT be branch target)
                # But first, check if next node IS the branch target - if so, skip it
                step = ExecutionStep(
                    step_number=step_number,
                    intent_name=node.intent_name,
                    location=node.location,
                    inputs=node_inputs,
                    outputs=simulated_outputs,
                    status="completed",
                )
                trace.steps.append(step)
                step_number += 1
                i += 1
                
                # Skip the branch target node if it's the next sequential node
                while i < len(graph.nodes) and graph.nodes[i].intent_name == node.branch_target:
                    # Skip this node (branch target) - condition was false, so don't execute it
                    i += 1
                
                # Continue with next node (which should be the "else" path)
                continue
        
        # Normal step completion
        step = ExecutionStep(
            step_number=step_number,
            intent_name=node.intent_name,
            location=node.location,
            inputs=node_inputs,
            outputs=simulated_outputs,
            status="completed",
        )
        trace.steps.append(step)
        step_number += 1
        i += 1
    
    # If we completed without terminal, check status
    if trace.final_status == ExecutionStatus.BLOCKED and not trace.errors:
        # Check if last node was clarification
        if trace.steps and trace.steps[-1].intent_name == 'request_clarification':
            trace.final_status = ExecutionStatus.NEEDS_CLARIFICATION
        else:
            trace.final_status = ExecutionStatus.READY
    
    return trace

