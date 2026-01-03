"""
Calculation tools - structural analysis, section properties, and general calculations.
Uses openseespy and sectionproperties libraries for structural engineering calculations.
"""

import math
from typing import Dict, List, Optional, Union, Any

# Try to import openseespy
try:
    import openseespy.opensees as ops
    HAS_OPENSEES = True
except ImportError:
    HAS_OPENSEES = False
    ops = None

# Try to import sectionproperties
try:
    from sectionproperties.pre.library import rectangular_section, circular_section, i_section
    from sectionproperties.analysis.section import Section
    HAS_SECTIONPROPERTIES = True
except ImportError:
    HAS_SECTIONPROPERTIES = False


def calculate_basic(expression: str) -> Dict:
    """
    Basic calculator - evaluates mathematical expressions safely.
    
    Args:
        expression: Mathematical expression as string (e.g., "2 + 2", "sqrt(16)", "50 * 100")
        
    Returns:
        Dictionary with:
        - result: Calculated result
        - expression: Original expression
        - error: Error message if calculation failed
        
    Example:
        calculate_basic("50 * 100")
        Returns: {"result": 5000, "expression": "50 * 100"}
        
        calculate_basic("sqrt(16) + 5")
        Returns: {"result": 9.0, "expression": "sqrt(16) + 5"}
    """
    try:
        # Safe evaluation with limited functions
        allowed_names = {
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "sum": sum,
            "pow": pow,
            "sqrt": math.sqrt,
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "pi": math.pi,
            "e": math.e,
            "log": math.log,
            "log10": math.log10,
            "exp": math.exp,
            "floor": math.floor,
            "ceil": math.ceil,
        }
        
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        return {
            "result": result,
            "expression": expression,
            "type": type(result).__name__
        }
    except Exception as e:
        return {
            "result": None,
            "expression": expression,
            "error": str(e)
        }


def calculate_section_properties(
    shape: str,
    dimensions: Dict[str, float],
    material: Optional[str] = None
) -> Dict:
    """
    Calculate section properties using sectionproperties library.
    
    Supports: rectangular, circular, I-section, and other standard shapes.
    
    Args:
        shape: Shape type ("rectangular", "circular", "i_section", etc.)
        dimensions: Dictionary with dimension values (e.g., {"width": 50, "height": 100})
        material: Optional material name (for future material property integration)
        
    Returns:
        Dictionary with section properties:
        - area: Cross-sectional area
        - perimeter: Perimeter
        - centroid: (x, y) centroid coordinates
        - Ixx: Second moment of area about x-axis
        - Iyy: Second moment of area about y-axis
        - Ixy: Product moment of area
        - J: Torsional constant
        - shape: Shape type used
        
    Example:
        calculate_section_properties("rectangular", {"width": 50, "height": 100})
        Returns: {
            "area": 5000,
            "Ixx": 4166666.67,
            "Iyy": 1041666.67,
            ...
        }
    """
    if not HAS_SECTIONPROPERTIES:
        return {
            "error": "sectionproperties library not installed. Install with: pip install sectionproperties",
            "shape": shape,
            "dimensions": dimensions
        }
    
    try:
        # Create geometry based on shape type
        if shape.lower() == "rectangular" or shape.lower() == "rectangle":
            width = dimensions.get("width", dimensions.get("b", dimensions.get("w", 0)))
            height = dimensions.get("height", dimensions.get("h", dimensions.get("d", 0)))
            geometry = rectangular_section(d=height, b=width)
            
        elif shape.lower() == "circular" or shape.lower() == "circle":
            diameter = dimensions.get("diameter", dimensions.get("d", 0))
            geometry = circular_section(d=diameter, n=64)
            
        elif shape.lower() == "i_section" or shape.lower() == "i-beam":
            d = dimensions.get("depth", dimensions.get("d", dimensions.get("height", 0)))
            b = dimensions.get("width", dimensions.get("b", dimensions.get("flange_width", 0)))
            t_f = dimensions.get("flange_thickness", dimensions.get("tf", 0))
            t_w = dimensions.get("web_thickness", dimensions.get("tw", dimensions.get("web_thickness", 0)))
            geometry = i_section(d=d, b=b, t_f=t_f, t_w=t_w, r=dimensions.get("root_radius", 0))
            
        else:
            return {
                "error": f"Unsupported shape type: {shape}. Supported: rectangular, circular, i_section",
                "shape": shape,
                "dimensions": dimensions
            }
        
        # Create section and calculate properties
        section = Section(geometry)
        section.calculate_geometric_properties()
        section.calculate_warping_properties()
        
        # Extract properties
        props = section.get_perimeter()
        area = section.get_area()
        centroid = section.get_c()
        Ixx, Iyy, Ixy = section.get_ic()
        J = section.get_j()
        
        return {
            "area": area,
            "perimeter": props,
            "centroid": {"x": centroid[0], "y": centroid[1]},
            "Ixx": Ixx,
            "Iyy": Iyy,
            "Ixy": Ixy,
            "J": J,
            "shape": shape,
            "dimensions": dimensions,
            "material": material
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "shape": shape,
            "dimensions": dimensions
        }


def analyze_structure_opensees(
    structure_type: str,
    geometry: Dict[str, Any],
    loads: List[Dict[str, Any]],
    material_properties: Optional[Dict[str, float]] = None
) -> Dict:
    """
    Perform structural analysis using OpenSeesPy.
    
    Supports: beam, frame, truss analysis with various boundary conditions.
    
    Args:
        structure_type: Type of structure ("beam", "frame", "truss")
        geometry: Dictionary with geometry data (nodes, elements, supports)
        loads: List of load dictionaries (point loads, distributed loads, etc.)
        material_properties: Optional material properties (E, A, I, etc.)
        
    Returns:
        Dictionary with analysis results:
        - displacements: Node displacements
        - reactions: Support reactions
        - forces: Element forces
        - moments: Bending moments (for beams/frames)
        - structure_type: Type analyzed
        
    Example:
        analyze_structure_opensees(
            "beam",
            {"length": 100, "nodes": [0, 50, 100]},
            [{"type": "point", "location": 50, "magnitude": 1000}],
            {"E": 29000, "I": 1000}
        )
    """
    if not HAS_OPENSEES:
        return {
            "error": "openseespy library not installed. Install with: pip install openseespy",
            "structure_type": structure_type,
            "geometry": geometry
        }
    
    try:
        # Clear previous model
        ops.wipe()
        ops.model('basic', '-ndm', 2, '-ndf', 3)  # 2D model with 3 DOF
        
        # Set material properties
        E = material_properties.get("E", 29000) if material_properties else 29000
        A = material_properties.get("A", 100) if material_properties else 100
        I = material_properties.get("I", 1000) if material_properties else 1000
        
        # Create material
        ops.uniaxialMaterial('Elastic', 1, E)
        
        # Create nodes based on geometry
        nodes = geometry.get("nodes", [])
        if not nodes:
            # Generate nodes if not provided
            length = geometry.get("length", 100)
            num_nodes = geometry.get("num_nodes", 10)
            nodes = [i * length / (num_nodes - 1) for i in range(num_nodes)]
        
        node_tags = []
        for i, x in enumerate(nodes):
            if isinstance(x, (list, tuple)):
                ops.node(i + 1, x[0], x[1] if len(x) > 1 else 0)
            else:
                ops.node(i + 1, x, 0)
            node_tags.append(i + 1)
        
        # Create elements
        if structure_type.lower() == "beam" or structure_type.lower() == "frame":
            # Beam/Frame elements
            for i in range(len(node_tags) - 1):
                ops.element('elasticBeamColumn', i + 1, node_tags[i], node_tags[i + 1], A, E, I, 1)
        elif structure_type.lower() == "truss":
            # Truss elements
            for i in range(len(node_tags) - 1):
                ops.element('Truss', i + 1, node_tags[i], node_tags[i + 1], A, 1)
        
        # Apply boundary conditions
        supports = geometry.get("supports", [])
        for support in supports:
            node = support.get("node", 1)
            fix_x = support.get("fix_x", False)
            fix_y = support.get("fix_y", False)
            fix_rot = support.get("fix_rot", False)
            dof = []
            if fix_x:
                dof.append(1)
            if fix_y:
                dof.append(2)
            if fix_rot:
                dof.append(3)
            if dof:
                ops.fix(node, *dof)
        
        # Apply loads
        for load in loads:
            load_type = load.get("type", "point")
            node = load.get("node", 1)
            magnitude = load.get("magnitude", 0)
            direction = load.get("direction", "y")  # 'x', 'y', or 'moment'
            
            if direction == "x":
                ops.load(node, magnitude, 0, 0)
            elif direction == "y":
                ops.load(node, 0, magnitude, 0)
            elif direction == "moment":
                ops.load(node, 0, 0, magnitude)
        
        # Perform analysis
        ops.system('BandGeneral')
        ops.numberer('RCM')
        ops.constraints('Plain')
        ops.integrator('LoadControl', 1.0)
        ops.algorithm('Linear')
        ops.analysis('Static')
        ops.analyze(1)
        
        # Extract results
        displacements = []
        reactions = []
        forces = []
        
        for node_tag in node_tags:
            # Get displacements
            disp = ops.nodeDisp(node_tag)
            displacements.append({
                "node": node_tag,
                "ux": disp[0],
                "uy": disp[1],
                "rot": disp[2] if len(disp) > 2 else 0
            })
            
            # Get reactions
            react = ops.nodeReaction(node_tag)
            if react:
                reactions.append({
                    "node": node_tag,
                    "Fx": react[0],
                    "Fy": react[1],
                    "M": react[2] if len(react) > 2 else 0
                })
        
        # Get element forces
        for i in range(len(node_tags) - 1):
            elem_forces = ops.eleResponse(i + 1, 'forces')
            forces.append({
                "element": i + 1,
                "forces": elem_forces
            })
        
        return {
            "displacements": displacements,
            "reactions": reactions,
            "forces": forces,
            "structure_type": structure_type,
            "geometry": geometry,
            "loads": loads
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "structure_type": structure_type,
            "geometry": geometry
        }
    finally:
        # Clean up
        if HAS_OPENSEES:
            ops.wipe()


def quick_calc(operation: str, values: Dict[str, Union[float, str]]) -> Dict:
    """
    Quick calculation wrapper - routes to appropriate calculation tool.
    
    Args:
        operation: Type of calculation ("basic", "section", "structure", "area", "volume", etc.)
        values: Dictionary with values needed for the calculation
        
    Returns:
        Dictionary with calculation results
        
    Example:
        quick_calc("basic", {"expression": "50 * 100"})
        quick_calc("section", {"shape": "rectangular", "width": 50, "height": 100})
    """
    if operation == "basic" or operation == "calculator":
        expression = values.get("expression", "")
        return calculate_basic(expression)
    
    elif operation == "section" or operation == "section_properties":
        shape = values.get("shape", "rectangular")
        dimensions = {k: v for k, v in values.items() if k != "shape"}
        material = values.get("material")
        return calculate_section_properties(shape, dimensions, material)
    
    elif operation == "structure" or operation == "structural_analysis":
        structure_type = values.get("structure_type", "beam")
        geometry = values.get("geometry", {})
        loads = values.get("loads", [])
        material_properties = values.get("material_properties")
        return analyze_structure_opensees(structure_type, geometry, loads, material_properties)
    
    elif operation == "area":
        # Quick area calculations
        shape = values.get("shape", "rectangle")
        if shape == "rectangle":
            return calculate_basic(f"{values.get('width', 0)} * {values.get('height', 0)}")
        elif shape == "circle":
            radius = values.get("radius", values.get("diameter", 0) / 2)
            return calculate_basic(f"pi * {radius} ** 2")
        elif shape == "triangle":
            return calculate_basic(f"0.5 * {values.get('base', 0)} * {values.get('height', 0)}")
    
    elif operation == "volume":
        # Quick volume calculations
        shape = values.get("shape", "box")
        if shape == "box" or shape == "rectangular":
            return calculate_basic(f"{values.get('length', 0)} * {values.get('width', 0)} * {values.get('height', 0)}")
        elif shape == "cylinder":
            radius = values.get("radius", values.get("diameter", 0) / 2)
            return calculate_basic(f"pi * {radius} ** 2 * {values.get('height', 0)}")
    
    else:
        return {
            "error": f"Unknown operation: {operation}",
            "supported_operations": ["basic", "section", "structure", "area", "volume"]
        }


# Export all calculation tools
ALL_CALCULATION_TOOLS = [
    calculate_basic,
    calculate_section_properties,
    analyze_structure_opensees,
    quick_calc
]




