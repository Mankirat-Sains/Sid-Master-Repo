#!/usr/bin/env python3
"""
Create Semantic Metadata for Excel Tool API

This script:
1. Reads XLWings extract JSON
2. Classifies cells (Input/Output/Calculation/Override) using hardcoded legend
3. Creates semantic groups per COPY_PASTE_PROMPT.txt
4. Outputs format compatible with excel_tools.py
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from collections import defaultdict
import re

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def has_content(cell: Dict[str, Any]) -> bool:
    """Check if cell has meaningful content."""
    content = cell.get("content")
    if content is not None and content != "" and str(content).strip() != "":
        return True
    if cell.get("has_formula") and cell.get("formula"):
        return True
    return False


def classify_cell(cell: Dict[str, Any]) -> Optional[str]:
    """
    Classify cell based on hardcoded legend:
    - S8 = Input (F2F2F2 fill, no formula typically)
    - S9 = Output (F2F2F2 fill, has formula)
    - S10 = Calculation (no fill/white, has formula)
    - S11 = Override (F2C1BC fill)
    """
    fill_color = cell.get("fill_color")
    has_formula = cell.get("has_formula", False)
    cell_addr = cell.get("cell", "")
    
    # Skip legend cells
    if cell_addr in ["S8", "S9", "S10", "S11", "R6", "T8", "T9", "T10", "T11"]:
        return None
    
    # Override: distinctive pink color
    if fill_color and fill_color.upper() == "F2C1BC":
        return "override"
    
    # F2F2F2 color: Input (no formula) or Output (has formula)
    if fill_color and fill_color.upper() == "F2F2F2":
        if has_formula:
            return "calculated_output"
        else:
            return "user_input"
    
    # No fill or white: likely Calculation if has formula
    if not fill_color or (fill_color and fill_color.upper() in ["FFFFFF", "NONE", ""]):
        if has_formula:
            return "calculation"
    
    # Fallback: use formula to classify
    if has_formula:
        formula = cell.get("formula", "")
        if any(func in formula.upper() for func in ["SUM", "IF", "MAX", "MIN", "VLOOKUP", "INDEX", "MATCH"]):
            return "calculation"
        return "calculated_output"
    
    return None


def extract_parameter_name(cell: Dict[str, Any], sheet_cells: List[Dict]) -> Optional[str]:
    """Extract parameter name from nearby cells. Returns None if no good label found."""
    cell_addr = cell.get("cell", "")
    if not cell_addr:
        return None
    
    col_match = re.match(r'([A-Z]+)(\d+)', cell_addr)
    if not col_match:
        return None
    
    col_letters = col_match.group(1)
    row_num = int(col_match.group(2))
    
    cell_map = {c.get("cell"): c for c in sheet_cells}
    
    # Check left (most common: label in column A, value in column B)
    if len(col_letters) == 1 and col_letters > 'A':
        prev_col = chr(ord(col_letters) - 1)
        left_addr = f"{prev_col}{row_num}"
        left_cell = cell_map.get(left_addr)
        if left_cell and left_cell.get("content"):
            label = str(left_cell.get("content", "")).strip()
            # Skip if label looks like a number or is too short/long
            if label and 3 <= len(label) <= 50 and not label.replace('.', '').replace('-', '').isdigit():
                # Clean up: remove special chars, convert to snake_case
                param = re.sub(r'[^\w\s-]', '', label.lower())
                param = re.sub(r'\s+', '_', param)
                param = re.sub(r'_+', '_', param).strip('_')
                if param and len(param) >= 3:
                    return param
    
    # Check above (header row)
    if row_num > 1:
        above_addr = f"{col_letters}{row_num - 1}"
        above_cell = cell_map.get(above_addr)
        if above_cell and above_cell.get("content"):
            label = str(above_cell.get("content", "")).strip()
            if label and 3 <= len(label) <= 50 and not label.replace('.', '').replace('-', '').isdigit():
                param = re.sub(r'[^\w\s-]', '', label.lower())
                param = re.sub(r'\s+', '_', param)
                param = re.sub(r'_+', '_', param).strip('_')
                if param and len(param) >= 3:
                    return param
    
    # Check diagonal (top-left)
    if row_num > 1 and len(col_letters) == 1 and col_letters > 'A':
        diag_col = chr(ord(col_letters) - 1)
        diag_addr = f"{diag_col}{row_num - 1}"
        diag_cell = cell_map.get(diag_addr)
        if diag_cell and diag_cell.get("content"):
            label = str(diag_cell.get("content", "")).strip()
            if label and 3 <= len(label) <= 50 and not label.replace('.', '').replace('-', '').isdigit():
                param = re.sub(r'[^\w\s-]', '', label.lower())
                param = re.sub(r'\s+', '_', param)
                param = re.sub(r'_+', '_', param).strip('_')
                if param and len(param) >= 3:
                    return param
    
    return None


def create_semantic_groups(classified_cells: Dict[str, List[Dict]], sheet_name: str) -> Dict[str, Any]:
    """Create semantic groups from classified cells."""
    result = {
        "inputs": {},
        "outputs": {},
        "lookups": {}
    }
    
    # Group inputs
    inputs = classified_cells.get("user_input", [])
    if inputs:
        input_groups = defaultdict(dict)
        for cell_info in inputs:
            param_name = cell_info.get("parameter_name", "")
            cell_addr = cell_info["cell"]
            content = str(cell_info.get("content", "")).lower()
            
            param_lower = param_name.lower()
            
            # More specific grouping
            if any(word in param_lower for word in ["project", "name", "number", "date", "designer", "administration"]):
                group_name = "project_administration"
            elif any(word in param_lower for word in ["load", "force", "weight", "pressure", "kpa", "kn"]):
                if any(word in param_lower for word in ["dead", "live", "snow", "wind", "rain"]):
                    group_name = "loading_parameters"
                else:
                    group_name = "loading_parameters"
            elif any(word in param_lower for word in ["tributary", "width", "length", "area"]):
                group_name = "loading_parameters"
            elif any(word in param_lower for word in ["wood", "species", "grade", "stress", "treatment", "fire", "service"]):
                group_name = "material_selection"
            elif any(word in param_lower for word in ["width", "depth", "length", "height", "b", "d", "l", "unbraced", "effective", "factor", "kx", "ky"]):
                group_name = "column_geometry"
            elif any(word in param_lower for word in ["location", "site", "ground", "snow", "wind", "rain", "environmental"]):
                group_name = "location_parameters"
            elif any(word in param_lower for word in ["factor", "coefficient", "safety", "adjustment"]):
                group_name = "design_factors"
            else:
                group_name = "input_parameters"
            
            input_groups[group_name][param_name] = cell_addr
        
        for group_name, cells in input_groups.items():
            if cells:
                descriptions = {
                    "project_administration": "General project tracking and administrative context.",
                    "loading_parameters": "Area-based loading and tributary dimensions used to calculate axial force.",
                    "material_selection": "Wood properties and environmental adjustment factors.",
                    "column_geometry": "Section dimensions and stability/buckling parameters.",
                    "location_parameters": "Location and environmental parameters.",
                    "design_factors": "Design factors and coefficients.",
                    "input_parameters": "User-editable input parameters."
                }
                result["inputs"][group_name] = {
                    "type": "group",
                    "sheet": sheet_name,
                    "cells": cells,
                    "description": descriptions.get(group_name, "Input parameters.")
                }
    
    # Group outputs (combine calculated_output and calculation)
    outputs = classified_cells.get("calculated_output", [])
    calculations = classified_cells.get("calculation", [])
    overrides = classified_cells.get("override", [])
    
    all_outputs = outputs + calculations
    
    if all_outputs:
        output_groups = defaultdict(dict)
        for cell_info in all_outputs:
            param_name = cell_info.get("parameter_name", "")
            cell_addr = cell_info["cell"]
            content = str(cell_info.get("content", "")).lower()
            
            param_lower = param_name.lower()
            
            # More specific grouping
            if any(word in param_lower for word in ["utilization", "ratio", "capacity"]):
                group_name = "utilization_ratios"
            elif any(word in param_lower for word in ["unfactored", "factored", "axial", "load", "pn", "pf"]):
                group_name = "calculated_force_effects"
            elif any(word in param_lower for word in ["resistance", "pr", "tr", "compressive", "tensile"]):
                group_name = "member_resistances"
            elif any(word in param_lower for word in ["moment", "shear", "force", "stress", "bending"]):
                group_name = "calculated_force_effects"
            elif any(word in param_lower for word in ["deflection", "displacement"]):
                group_name = "deflection_results"
            elif any(word in param_lower for word in ["governing", "maximum", "minimum", "critical", "summary"]):
                group_name = "design_summary"
            elif any(word in param_lower for word in ["member", "section", "size", "selection"]):
                group_name = "member_selection"
            else:
                group_name = "calculated_results"
            
            output_groups[group_name][param_name] = cell_addr
        
        for group_name, cells in output_groups.items():
            if cells:
                descriptions = {
                    "utilization_ratios": "Efficiency ratios (Demand/Capacity). Values > 1.0 indicate failure.",
                    "calculated_force_effects": "Calculated demand based on input loads and tributary area.",
                    "member_resistances": "The ultimate capacity of the member as calculated by the engine.",
                    "deflection_results": "Deflection and displacement calculation results.",
                    "design_summary": "Key design results and governing values.",
                    "member_selection": "Selected member sizes and sections.",
                    "calculated_results": "Calculated output results."
                }
                result["outputs"][group_name] = {
                    "type": "group",
                    "sheet": sheet_name,
                    "cells": cells,
                    "description": descriptions.get(group_name, "Output results.")
                }
    
    # Overrides (add to utilization_ratios if exists, otherwise separate)
    if overrides:
        override_cells = {}
        for cell_info in overrides:
            param_name = cell_info.get("parameter_name", "")
            override_cells[param_name] = cell_info["cell"]
        
        if override_cells:
            # Add to utilization_ratios if it exists
            if "utilization_ratios" in result["outputs"]:
                result["outputs"]["utilization_ratios"]["cells"].update(override_cells)
            else:
                result["outputs"]["override_indicators"] = {
                    "type": "group",
                    "sheet": sheet_name,
                    "cells": override_cells,
                    "description": "Override cells indicating values that exceed limits."
                }
    
    return result


def convert_to_excel_tools_format(grouped_metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert grouped format to flat format expected by excel_tools.py:
    inputs: {"param_name": {"sheet": "...", "address": "..."}}
    outputs: {"param_name": {"sheet": "...", "address": "..."}}
    lookups: {"lookup_name": {"type": "...", "sheet": "...", "range": "..."}}
    """
    flat_format = {
        "inputs": {},
        "outputs": {},
        "lookups": {}
    }
    
    # Flatten inputs
    for group_name, group_data in grouped_metadata.get("inputs", {}).items():
        sheet = group_data.get("sheet", "")
        cells = group_data.get("cells", {})
        for param_name, cell_addr in cells.items():
            flat_format["inputs"][param_name] = {
                "sheet": sheet,
                "address": cell_addr
            }
    
    # Flatten outputs
    for group_name, group_data in grouped_metadata.get("outputs", {}).items():
        sheet = group_data.get("sheet", "")
        cells = group_data.get("cells", {})
        for param_name, cell_addr in cells.items():
            flat_format["outputs"][param_name] = {
                "sheet": sheet,
                "address": cell_addr
            }
    
    # Lookups (already in correct format)
    flat_format["lookups"] = grouped_metadata.get("lookups", {})
    
    return flat_format


def identify_lookup_tables(sheet_cells: List[Dict], sheet_name: str) -> Dict[str, Any]:
    """Identify lookup tables in the sheet."""
    lookups = {}
    
    # Look for patterns that suggest lookup tables:
    # - Dense data regions (many cells with content in a grid)
    # - Headers followed by data rows
    # - Common in "Guidance Tables" or "Tables" sheets
    
    if "table" in sheet_name.lower() or "guidance" in sheet_name.lower():
        # Find data regions
        cell_map = {c.get("cell"): c for c in sheet_cells if has_content(c)}
        
        # Group cells by proximity to find table regions
        # Simple heuristic: find rectangular regions with many filled cells
        # For now, return empty - can be enhanced later
        pass
    
    return lookups


def process_workbook(input_path: Path, output_path: Path, grouped_format: bool = True):
    """Process XLWings extract and create semantic metadata."""
    logger.info(f"Loading JSON from: {input_path}")
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    all_semantic_groups = {
        "inputs": {},
        "outputs": {},
        "lookups": {}
    }
    
    for sheet_name, sheet_cells in data.get("sheets", {}).items():
        logger.info(f"\nProcessing sheet: {sheet_name}")
        
        # Filter cells with content
        cells_with_content = [c for c in sheet_cells if has_content(c)]
        logger.info(f"  Cells with content: {len(cells_with_content)} (out of {len(sheet_cells)})")
        
        # Classify cells
        classified_cells = defaultdict(list)
        for cell in cells_with_content:
            category = classify_cell(cell)
            if category:
                param_name = extract_parameter_name(cell, sheet_cells)
                # Only include cells with good parameter names
                if param_name:
                    cell_info = {
                        "cell": cell.get("cell"),
                        "content": cell.get("content"),
                        "category": category,
                        "parameter_name": param_name,
                        "has_formula": cell.get("has_formula", False),
                        "fill_color": cell.get("fill_color")
                    }
                    classified_cells[category].append(cell_info)
        
        logger.info(f"  Classified: {sum(len(v) for v in classified_cells.values())} cells")
        for cat, cells in classified_cells.items():
            logger.info(f"    {cat}: {len(cells)}")
        
        # Create semantic groups
        semantic_groups = create_semantic_groups(classified_cells, sheet_name)
        
        # Identify lookup tables
        lookup_tables = identify_lookup_tables(sheet_cells, sheet_name)
        semantic_groups["lookups"].update(lookup_tables)
        
        # Merge
        for category in ["inputs", "outputs", "lookups"]:
            all_semantic_groups[category].update(semantic_groups.get(category, {}))
    
    # Use grouped format
    final_metadata = all_semantic_groups
    
    # Save
    logger.info(f"\nSaving to: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_metadata, f, indent=2, ensure_ascii=False)
    
    # Count total parameters
    total_inputs = sum(len(g.get("cells", {})) for g in final_metadata.get("inputs", {}).values())
    total_outputs = sum(len(g.get("cells", {})) for g in final_metadata.get("outputs", {}).values())
    
    logger.info(f"\n✅ Complete!")
    logger.info(f"   Input groups: {len(final_metadata.get('inputs', {}))} ({total_inputs} parameters)")
    logger.info(f"   Output groups: {len(final_metadata.get('outputs', {}))} ({total_outputs} parameters)")
    logger.info(f"   Lookups: {len(final_metadata.get('lookups', {}))}")
    
    return final_metadata


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Create semantic metadata from XLWings extract")
    parser.add_argument("input", type=Path, help="Input JSON from xlwings_excel_extractor")
    parser.add_argument("-o", "--output", type=Path, help="Output JSON file")
    parser.add_argument("--flat", action="store_true", help="Output flat format for excel_tools (default: grouped)")
    
    args = parser.parse_args()
    
    if not args.input.exists():
        logger.error(f"Input file not found: {args.input}")
        return
    
    output_path = args.output or args.input.parent / f"{args.input.stem}_semantic.json"
    
    metadata = process_workbook(args.input, output_path, grouped_format=not args.flat)
    
    # If flat format requested, convert and save
    if args.flat:
        flat_metadata = convert_to_excel_tools_format(metadata)
        flat_path = output_path.parent / f"{output_path.stem}_flat.json"
        with open(flat_path, 'w', encoding='utf-8') as f:
            json.dump(flat_metadata, f, indent=2, ensure_ascii=False)
        logger.info(f"Also saved flat format to: {flat_path}")


if __name__ == "__main__":
    main()

