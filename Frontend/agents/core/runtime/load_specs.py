"""
Loads MD specifications into in-memory objects.
This is the compiler - MD stops being "the thing" here.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field


@dataclass
class Intent:
    """Represents a single intent from the catalog."""
    name: str
    description: str = ""
    execution_plane: str = ""  # "local" or "cloud"
    capability_required: str = ""
    required_inputs: List[str] = field(default_factory=list)
    produced_outputs: List[str] = field(default_factory=list)
    safety: str = ""


@dataclass
class GraphNode:
    """Represents a single node in an execution graph."""
    intent_name: str
    location: str = ""  # "local" or "cloud" - parsed from graph
    capability: str = ""
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    is_terminal: bool = False
    branch_condition: Optional[str] = None
    branch_target: Optional[str] = None


@dataclass
class ExecutionGraph:
    """Represents a complete execution graph."""
    name: str
    nodes: List[GraphNode] = field(default_factory=list)
    validation_status: str = ""


@dataclass
class Scenario:
    """Represents a scenario definition."""
    name: str
    description: str = ""
    triggers: List[str] = field(default_factory=list)
    mapped_plan: str = ""
    mapped_graph: str = ""
    execution_mode: str = ""


@dataclass
class Specs:
    """Container for all loaded specifications."""
    intents: Dict[str, Intent] = field(default_factory=dict)
    scenarios: Dict[str, Scenario] = field(default_factory=dict)
    graphs: Dict[str, ExecutionGraph] = field(default_factory=dict)


def load_intent_catalog(catalog_path: Path) -> Dict[str, Intent]:
    """Parse intent_catalog.md into Intent objects."""
    intents = {}
    
    if not catalog_path.exists():
        raise FileNotFoundError(f"Intent catalog not found: {catalog_path}")
    
    content = catalog_path.read_text()
    
    # Split by "Intent:" markers
    intent_blocks = re.split(r'^Intent:\s*(\w+)', content, flags=re.MULTILINE)
    
    # Skip first empty block
    for i in range(1, len(intent_blocks), 2):
        if i + 1 >= len(intent_blocks):
            break
            
        intent_name = intent_blocks[i].strip()
        intent_body = intent_blocks[i + 1]
        
        intent = Intent(name=intent_name)
        
        # Parse fields
        desc_match = re.search(r'Description\s*\n(.+?)(?=\n[A-Z]|\Z)', intent_body, re.DOTALL)
        if desc_match:
            intent.description = desc_match.group(1).strip()
        
        plane_match = re.search(r'Execution Plane\s*\n(.+?)(?=\n[A-Z]|\Z)', intent_body, re.MULTILINE)
        if plane_match:
            intent.execution_plane = plane_match.group(1).strip().lower()
        
        cap_match = re.search(r'Capability Required\s*\n(.+?)(?=\n[A-Z]|\Z)', intent_body, re.MULTILINE)
        if cap_match:
            intent.capability_required = cap_match.group(1).strip()
        
        inputs_match = re.search(r'Required Inputs\s*\n(.+?)(?=\n[A-Z]|\Z)', intent_body, re.MULTILINE | re.DOTALL)
        if inputs_match:
            inputs_text = inputs_match.group(1).strip()
            if inputs_text.lower() not in ['none', '']:
                intent.required_inputs = [inp.strip() for inp in inputs_text.split('\n') if inp.strip()]
        
        outputs_match = re.search(r'Produced Outputs\s*\n(.+?)(?=\n[A-Z]|\Z)', intent_body, re.MULTILINE | re.DOTALL)
        if outputs_match:
            outputs_text = outputs_match.group(1).strip()
            intent.produced_outputs = [out.strip() for out in outputs_text.split('\n') if out.strip()]
        
        safety_match = re.search(r'Safety\s*\n(.+?)(?=\n[A-Z]|\Z)', intent_body, re.MULTILINE)
        if safety_match:
            intent.safety = safety_match.group(1).strip()
        
        intents[intent_name] = intent
    
    return intents


def load_scenario_router(router_path: Path) -> Dict[str, Scenario]:
    """Parse scenario_router.md into Scenario objects."""
    scenarios = {}
    
    if not router_path.exists():
        raise FileNotFoundError(f"Scenario router not found: {router_path}")
    
    content = router_path.read_text()
    
    # Split by scenario headers
    scenario_blocks = re.split(r'^## Scenario:\s*(\w+)', content, flags=re.MULTILINE)
    
    # Skip first empty block
    for i in range(1, len(scenario_blocks), 2):
        if i + 1 >= len(scenario_blocks):
            break
        
        scenario_name = scenario_blocks[i].strip()
        scenario_body = scenario_blocks[i + 1]
        
        scenario = Scenario(name=scenario_name)
        
        # Parse fields
        desc_match = re.search(r'\*\*Description\*\*\s*\n(.+?)(?=\n\*\*|\n---|\Z)', scenario_body, re.DOTALL)
        if desc_match:
            scenario.description = desc_match.group(1).strip()
        
        triggers_match = re.search(r'\*\*Triggers\*\*\s*\n(.+?)(?=\n\*\*|\n---|\Z)', scenario_body, re.DOTALL)
        if triggers_match:
            triggers_text = triggers_match.group(1).strip()
            scenario.triggers = [t.strip().lstrip('- ') for t in triggers_text.split('\n') if t.strip()]
        
        plan_match = re.search(r'\*\*Mapped Plan\*\*\s*\n([^\n]+)', scenario_body, re.MULTILINE)
        if plan_match:
            scenario.mapped_plan = plan_match.group(1).strip()
        
        graph_match = re.search(r'\*\*Mapped Execution Graph\*\*\s*\n([^\n]+)', scenario_body, re.MULTILINE)
        if graph_match:
            scenario.mapped_graph = graph_match.group(1).strip()
        
        mode_match = re.search(r'\*\*Execution Mode\*\*\s*\n([^\n]+)', scenario_body, re.MULTILINE)
        if mode_match:
            scenario.execution_mode = mode_match.group(1).strip()
        
        scenarios[scenario_name] = scenario
    
    return scenarios


def load_execution_graph(graph_path: Path) -> ExecutionGraph:
    """Parse a *.graph.md file into an ExecutionGraph object."""
    graph_name = graph_path.stem.replace('.graph', '')
    graph = ExecutionGraph(name=graph_name)
    
    if not graph_path.exists():
        raise FileNotFoundError(f"Execution graph not found: {graph_path}")
    
    content = graph_path.read_text()
    lines = content.split('\n')
    
    i = 0
    current_node = None
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines, validation notes, etc.
        if not line or line.startswith('#') or line.startswith('Validation'):
            i += 1
            continue
        
        # Check if this is a numbered step (e.g., "1.")
        if re.match(r'^\d+\.', line):
            i += 1
            continue
        
        # Check if this is an IF condition (can come after empty line, attach to previous node)
        if line.startswith('IF'):
            if current_node:
                current_node.branch_condition = line
                # Next line should be the branch target
                if i + 1 < len(lines):
                    branch_line = lines[i + 1].strip()
                    if branch_line.startswith('→'):
                        current_node.branch_target = branch_line.lstrip('→').strip()
                        i += 1
            i += 1
            continue
        
        # Check if this is an intent name (starts with word, no colon)
        if re.match(r'^[a-z_]+$', line) and ':' not in line:
            intent_name = line
            node = GraphNode(intent_name=intent_name)
            current_node = node
            
            # Parse attributes from following lines
            i += 1
            while i < len(lines):
                next_line = lines[i].strip()
                
                # Empty line or next intent - done with this node
                if not next_line or (re.match(r'^[a-z_]+$', next_line) and ':' not in next_line):
                    break
                
                # Parse location
                if next_line.startswith('location:'):
                    node.location = next_line.split(':', 1)[1].strip()
                
                # Parse capability
                elif next_line.startswith('capability:'):
                    node.capability = next_line.split(':', 1)[1].strip()
                
                # Parse input
                elif next_line.startswith('input:'):
                    inputs_str = next_line.split(':', 1)[1].strip()
                    # Handle inputs with parentheses (descriptions) - don't split on commas inside parens
                    # Simple approach: if there's a paren, treat everything before it as the input name
                    if '(' in inputs_str:
                        # Extract input name before parentheses
                        input_name = inputs_str.split('(')[0].strip()
                        node.inputs = [input_name]
                    else:
                        # Split on commas for multiple inputs
                        node.inputs = [inp.strip() for inp in inputs_str.split(',')]
                
                # Parse produces/output
                elif next_line.startswith('produces:'):
                    outputs_str = next_line.split(':', 1)[1].strip()
                    # Handle "produces: x | none" pattern
                    if '|' in outputs_str:
                        outputs_str = outputs_str.split('|')[0].strip()
                    node.outputs = [out.strip() for out in outputs_str.split(',')]
                elif next_line.startswith('output:'):
                    outputs_str = next_line.split(':', 1)[1].strip()
                    node.outputs = [out.strip() for out in outputs_str.split(',')]
                
                # Parse terminal
                elif next_line.startswith('terminal:'):
                    node.is_terminal = next_line.split(':', 1)[1].strip().lower() == 'true'
                
                # Parse IF condition (handled above, but keep for inline IFs)
                elif next_line.startswith('IF'):
                    node.branch_condition = next_line
                    # Next line should be the branch target
                    if i + 1 < len(lines):
                        branch_line = lines[i + 1].strip()
                        if branch_line.startswith('→'):
                            node.branch_target = branch_line.lstrip('→').strip()
                            i += 1
                
                i += 1
            
            graph.nodes.append(node)
        else:
            i += 1
    
    return graph


def load_all_specs(base_path: Path) -> Specs:
    """
    Load all specifications from the core directory.
    This runs at startup - compile once, use many times.
    """
    specs = Specs()
    
    planner_path = base_path / "planner"
    graphs_path = base_path / "execution_graphs"
    
    # Load intent catalog
    catalog_path = planner_path / "intent_catalog.md"
    specs.intents = load_intent_catalog(catalog_path)
    
    # Load scenario router
    router_path = planner_path / "scenario_router.md"
    specs.scenarios = load_scenario_router(router_path)
    
    # Load all execution graphs
    if graphs_path.exists():
        for graph_file in graphs_path.glob("*.graph.md"):
            graph = load_execution_graph(graph_file)
            specs.graphs[graph.name] = graph
    
    return specs

