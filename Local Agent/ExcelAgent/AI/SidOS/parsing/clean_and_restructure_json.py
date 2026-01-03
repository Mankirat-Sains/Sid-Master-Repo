#!/usr/bin/env python3
"""
Clean and Restructure XLWings JSON Extract

This script:
1. Removes cells with no content (all null)
2. Hardcodes legend: S8=Input, S9=Output, S10=Calculation, S11=Override
3. Classifies cells by color matching legend
4. Restructures into semantic metadata format per COPY_PASTE_PROMPT.txt
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from collections import defaultdict
import re

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def get_legend_colors(data: Dict[str, Any], sheet_name: str = "Axial") -> Dict[str, str]:
    """
    Hardcoded legend extraction from S8-S11.
    Returns color to category mapping, including text color mappings.
    """
    if sheet_name not in data.get("sheets", {}):
        logger.warning(f"Sheet '{sheet_name}' not found")
        return {}, {}
    
    sheet_cells = data["sheets"][sheet_name]
    cell_map = {c.get("cell"): c for c in sheet_cells}
    
    # Hardcoded legend mapping
    legend_cells = {
        "S8": "user_input",      # Input (red text)
        "S9": "calculated_output", # Output (black text)
        "S10": "calculation",     # Calculation
        "S11": "override"         # Override
    }
    
    color_to_category = {}
    text_color_to_category = {}
    
    for addr, category in legend_cells.items():
        cell = cell_map.get(addr)
        if not cell:
            continue
        
        # Get fill color
        fill_color = cell.get("fill_color")
        if not fill_color:
            # Check adjacent T cell for color swatch
            t_addr = addr.replace("S", "T")
            t_cell = cell_map.get(t_addr)
            if t_cell:
                fill_color = t_cell.get("fill_color")
        
        # Get text color (this is key for Input vs Output differentiation)
        text_color = cell.get("text_color")
        text_color_rgb = cell.get("text_color_rgb")
        
        if fill_color:
            color_upper = fill_color.upper()
            color_to_category[color_upper] = category
        
        # Map text color to category (Input = red, Output = black/default)
        if text_color:
            text_color_upper = text_color.upper()
            # Red text typically indicates Input
            if text_color_rgb:
                r, g, b = text_color_rgb[0], text_color_rgb[1], text_color_rgb[2]
                # Red text (high R, low G, low B)
                if r > 200 and g < 100 and b < 100:
                    text_color_to_category[text_color_upper] = "user_input"
                # Black/default text (low values)
                elif r < 50 and g < 50 and b < 50:
                    text_color_to_category[text_color_upper] = "calculated_output"
            else:
                # Use hex to detect red
                if "FF" in text_color_upper[:2] or "F" in text_color_upper[:2]:
                    text_color_to_category[text_color_upper] = "user_input"
    
    logger.info(f"Legend fill color mappings: {color_to_category}")
    logger.info(f"Legend text color mappings: {text_color_to_category}")
    return color_to_category, text_color_to_category, legend_cells


def has_content(cell: Dict[str, Any]) -> bool:
    """Check if cell has any meaningful content."""
    content = cell.get("content")
    if content is not None and content != "" and str(content).strip() != "":
        return True
    # Also include cells with formulas (even if value appears empty)
    if cell.get("has_formula") and cell.get("formula"):
        return True
    return False


def classify_cell(cell: Dict[str, Any], color_mappings: Dict[str, str], 
                 text_color_mappings: Dict[str, str],
                 legend_categories: Dict[str, str]) -> Optional[str]:
    """
    Classify a cell based on its color matching legend colors.
    Hardcoded logic: S8=Input, S9=Output, S10=Calculation, S11=Override
    """
    fill_color = cell.get("fill_color")
    has_formula = cell.get("has_formula", False)
    formula = cell.get("formula")
    cell_addr = cell.get("cell", "")
    
    # Skip legend cells themselves
    if cell_addr in ["S8", "S9", "S10", "S11", "R6", "T8", "T9", "T10", "T11"]:
        return None
    
    # Hardcoded legend colors from S8-S11
    # S8 (Input): F2F2F2 fill, RED text
    # S9 (Output): F2F2F2 fill, BLACK text
    # S10 (Calculation): no fill color or white
    # S11 (Override): F2C1BC fill
    
    # First check text color (most reliable for Input vs Output)
    text_color = cell.get("text_color")
    text_color_rgb = cell.get("text_color_rgb")
    
    if text_color:
        text_color_upper = text_color.upper()
        if text_color_upper in text_color_mappings:
            return text_color_mappings[text_color_upper]
        
        # Check if text color indicates red (Input) or black (Output)
        if text_color_rgb:
            r, g, b = text_color_rgb[0], text_color_rgb[1], text_color_rgb[2]
            # Red text (high R, low G, low B) = Input
            if r > 200 and g < 100 and b < 100:
                return "user_input"
            # Black/default text (low values) = Output (if has formula)
            elif r < 50 and g < 50 and b < 50 and has_formula:
                return "calculated_output"
    
    # Then check fill color
    if fill_color:
        color_upper = fill_color.upper()
        
        # Override color (F2C1BC) - distinctive
        if color_upper == "F2C1BC":
            return "override"
        
        # F2F2F2 color - could be Input or Output
        # Use text color if available, otherwise use formula presence
        if color_upper == "F2F2F2":
            # If we have text color info, use it
            if text_color_rgb:
                r, g, b = text_color_rgb[0], text_color_rgb[1], text_color_rgb[2]
                if r > 200 and g < 100 and b < 100:
                    return "user_input"
                elif has_formula:
                    return "calculated_output"
            # Fallback: differentiate by formula
            elif has_formula:
                return "calculated_output"
            else:
                return "user_input"
        
        # Check other color mappings
        if color_upper in color_mappings:
            category = color_mappings[color_upper]
            if category == "user_input" and has_formula:
                return "calculated_output"
            return category
    
    # No fill color or white - likely Calculation
    if not fill_color or (fill_color and fill_color.upper() in ["FFFFFF", "NONE", ""]):
        if has_formula:
            return "calculation"
        # If no color and no formula, might be a label or empty - skip
    
    # Fallback: use formula to classify
    if has_formula and formula:
        # Complex formulas are calculations
        if any(func in formula.upper() for func in ["SUM", "IF", "MAX", "MIN", "VLOOKUP", "INDEX", "MATCH"]):
            return "calculation"
        # Simple formulas are outputs
        return "calculated_output"
    
    return None


def extract_parameter_name(cell: Dict[str, Any], sheet_cells: List[Dict], sheet_name: str) -> str:
    """
    Extract parameter name from nearby cells (labels to left or above).
    """
    cell_addr = cell.get("cell", "")
    if not cell_addr:
        return f"param_{cell_addr}"
    
    # Parse cell address
    col_match = re.match(r'([A-Z]+)(\d+)', cell_addr)
    if not col_match:
        return f"param_{cell_addr}"
    
    col_letters = col_match.group(1)
    row_num = int(col_match.group(2))
    
    # Create cell lookup
    cell_map = {c.get("cell"): c for c in sheet_cells}
    
    # Check left (previous column, same row)
    if len(col_letters) == 1 and col_letters > 'A':
        prev_col = chr(ord(col_letters) - 1)
        left_addr = f"{prev_col}{row_num}"
        left_cell = cell_map.get(left_addr)
        if left_cell and left_cell.get("content"):
            label = str(left_cell.get("content", "")).strip()
            if label and len(label) < 50:
                # Clean up parameter name
                param = re.sub(r'[^\w\s-]', '', label.lower())
                param = re.sub(r'\s+', '_', param)
                return param
    
    # Check above (same column, previous row)
    if row_num > 1:
        above_addr = f"{col_letters}{row_num - 1}"
        above_cell = cell_map.get(above_addr)
        if above_cell and above_cell.get("content"):
            label = str(above_cell.get("content", "")).strip()
            if label and len(label) < 50:
                param = re.sub(r'[^\w\s-]', '', label.lower())
                param = re.sub(r'\s+', '_', param)
                return param
    
    # Fallback: use cell address
    return f"param_{cell_addr.lower()}"


def create_semantic_groups(classified_cells: Dict[str, List[Dict]], sheet_name: str) -> Dict[str, Any]:
    """
    Create semantic groups from classified cells based on parameter names and context.
    """
    result = {
        "inputs": {},
        "outputs": {},
        "lookups": {}
    }
    
    # Group inputs semantically
    inputs = classified_cells.get("user_input", [])
    if inputs:
        input_groups = defaultdict(dict)
        
        for cell_info in inputs:
            param_name = cell_info.get("parameter_name", "")
            cell_addr = cell_info["cell"]
            content = str(cell_info.get("content", "")).lower()
            
            # Determine semantic group based on parameter name and content
            param_lower = param_name.lower()
            
            if any(word in param_lower or word in content for word in ["load", "force", "weight", "pressure"]):
                group_name = "load_parameters"
            elif any(word in param_lower or word in content for word in ["dimension", "size", "width", "height", "length", "span", "depth"]):
                group_name = "dimension_parameters"
            elif any(word in param_lower or word in content for word in ["material", "grade", "strength", "modulus", "density"]):
                group_name = "material_parameters"
            elif any(word in param_lower or word in content for word in ["location", "site", "ground", "snow", "wind", "rain"]):
                group_name = "location_parameters"
            elif any(word in param_lower or word in content for word in ["factor", "coefficient", "safety"]):
                group_name = "design_factors"
            else:
                group_name = "input_parameters"
            
            input_groups[group_name][param_name] = cell_addr
        
        # Create group entries
        for group_name, cells in input_groups.items():
            if cells:
                descriptions = {
                    "load_parameters": "Applied loads and forces",
                    "dimension_parameters": "Geometric dimensions and sizes",
                    "material_parameters": "Material properties and grades",
                    "location_parameters": "Location and environmental parameters",
                    "design_factors": "Design factors and coefficients",
                    "input_parameters": "User-editable input parameters"
                }
                result["inputs"][group_name] = {
                    "type": "group",
                    "sheet": sheet_name,
                    "cells": cells,
                    "description": descriptions.get(group_name, "Input parameters")
                }
    
    # Group outputs semantically
    outputs = classified_cells.get("calculated_output", [])
    calculations = classified_cells.get("calculation", [])
    overrides = classified_cells.get("override", [])
    
    # Group calculations separately
    if calculations:
        calc_groups = defaultdict(dict)
        for cell_info in calculations:
            param_name = cell_info.get("parameter_name", "")
            cell_addr = cell_info["cell"]
            content = str(cell_info.get("content", "")).lower()
            
            param_lower = param_name.lower()
            
            if any(word in param_lower or word in content for word in ["ratio", "utilization", "capacity"]):
                group_name = "capacity_ratios"
            elif any(word in param_lower or word in content for word in ["moment", "shear", "force", "stress"]):
                group_name = "force_results"
            elif any(word in param_lower or word in content for word in ["deflection", "displacement"]):
                group_name = "deflection_results"
            else:
                group_name = "intermediate_calculations"
            
            calc_groups[group_name][param_name] = cell_addr
        
        for group_name, cells in calc_groups.items():
            if cells:
                descriptions = {
                    "capacity_ratios": "Capacity utilization ratios (Mf/Mr, Vf/Vr, etc.)",
                    "force_results": "Force and moment calculation results",
                    "deflection_results": "Deflection and displacement results",
                    "intermediate_calculations": "Intermediate calculation cells"
                }
                result["outputs"][group_name] = {
                    "type": "group",
                    "sheet": sheet_name,
                    "cells": cells,
                    "description": descriptions.get(group_name, "Calculation results")
                }
    
    # Group outputs
    if outputs:
        output_groups = defaultdict(dict)
        for cell_info in outputs:
            param_name = cell_info.get("parameter_name", "")
            cell_addr = cell_info["cell"]
            content = str(cell_info.get("content", "")).lower()
            
            param_lower = param_name.lower()
            
            if any(word in param_lower or word in content for word in ["governing", "maximum", "minimum", "critical"]):
                group_name = "design_summary"
            elif any(word in param_lower or word in content for word in ["ratio", "utilization"]):
                group_name = "capacity_ratios"
            elif any(word in param_lower or word in content for word in ["member", "section", "size"]):
                group_name = "member_selection"
            else:
                group_name = "calculated_results"
            
            output_groups[group_name][param_name] = cell_addr
        
        for group_name, cells in output_groups.items():
            if cells:
                descriptions = {
                    "design_summary": "Key design results and governing values",
                    "capacity_ratios": "Capacity utilization ratios",
                    "member_selection": "Selected member sizes and sections",
                    "calculated_results": "Calculated output results"
                }
                result["outputs"][group_name] = {
                    "type": "group",
                    "sheet": sheet_name,
                    "cells": cells,
                    "description": descriptions.get(group_name, "Output results")
                }
    
    # Group overrides
    if overrides:
        override_cells = {}
        for cell_info in overrides:
            param_name = cell_info.get("parameter_name", "")
            override_cells[param_name] = cell_info["cell"]
        
        if override_cells:
            result["outputs"]["override_indicators"] = {
                "type": "group",
                "sheet": sheet_name,
                "cells": override_cells,
                "description": "Override cells indicating values that exceed limits"
            }
    
    return result


def process_workbook(input_path: Path, output_path: Path):
    """
    Process the XLWings extract JSON and create semantic metadata.
    """
    logger.info(f"Loading JSON from: {input_path}")
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Step 1: Get hardcoded legend colors
    logger.info("Extracting legend colors (hardcoded: S8-S11)...")
    color_mappings, text_color_mappings, legend_categories = get_legend_colors(data, sheet_name="Axial")
    
    # Step 2: Process each sheet
    all_semantic_groups = {
        "inputs": {},
        "outputs": {},
        "lookups": {}
    }
    
    for sheet_name, sheet_cells in data.get("sheets", {}).items():
        logger.info(f"\nProcessing sheet: {sheet_name}")
        
        # Filter cells with content (remove all null cells)
        cells_with_content = [c for c in sheet_cells if has_content(c)]
        logger.info(f"  Cells with content: {len(cells_with_content)} (out of {len(sheet_cells)})")
        
        # Classify cells
        classified_cells = defaultdict(list)
        for cell in cells_with_content:
            category = classify_cell(cell, color_mappings, text_color_mappings, legend_categories)
            if category:
                param_name = extract_parameter_name(cell, sheet_cells, sheet_name)
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
        
        # Merge into overall structure
        for category in ["inputs", "outputs", "lookups"]:
            all_semantic_groups[category].update(semantic_groups.get(category, {}))
    
    # Step 3: Create final metadata structure (exact format from prompt)
    metadata = {
        "inputs": all_semantic_groups["inputs"],
        "outputs": all_semantic_groups["outputs"],
        "lookups": all_semantic_groups["lookups"]
    }
    
    # Step 4: Save output
    logger.info(f"\nSaving cleaned and restructured JSON to: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\n✅ Processing complete!")
    logger.info(f"   Input groups: {len(metadata['inputs'])}")
    logger.info(f"   Output groups: {len(metadata['outputs'])}")
    logger.info(f"   Lookup groups: {len(metadata['lookups'])}")
    
    # Print summary
    total_inputs = sum(len(g["cells"]) for g in metadata["inputs"].values())
    total_outputs = sum(len(g["cells"]) for g in metadata["outputs"].values())
    logger.info(f"   Total input parameters: {total_inputs}")
    logger.info(f"   Total output parameters: {total_outputs}")
    
    return metadata


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Clean and restructure XLWings JSON extract into semantic metadata"
    )
    parser.add_argument("input", type=Path, help="Input JSON file from xlwings_excel_extractor")
    parser.add_argument("-o", "--output", type=Path, help="Output JSON file (default: input_cleaned.json)")
    
    args = parser.parse_args()
    
    if not args.input.exists():
        logger.error(f"Input file not found: {args.input}")
        return
    
    output_path = args.output or args.input.parent / f"{args.input.stem}_cleaned.json"
    
    process_workbook(args.input, output_path)


if __name__ == "__main__":
    main()

