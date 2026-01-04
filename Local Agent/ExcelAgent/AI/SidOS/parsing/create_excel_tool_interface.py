#!/usr/bin/env python3
"""
Create Excel Tool Interface from Semantic Metadata

This converts semantic metadata into the tool interface format described in explanation.txt:
- Treats Excel as deterministic compute engine
- Creates tool definitions: get_excel_input, set_excel_input, get_design_summary, lookup_location
- Formats metadata for excel_tools.py API
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def convert_to_excel_tools_format(grouped_metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert grouped semantic metadata to flat format for excel_tools.py
    
    From:
    {
      "inputs": {
        "group_name": {
          "type": "group",
          "sheet": "SheetName",
          "cells": {"param": "B3"}
        }
      }
    }
    
    To:
    {
      "inputs": {
        "param": {"sheet": "SheetName", "address": "B3"}
      }
    }
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
    
    # Lookups (convert range format if needed)
    for lookup_name, lookup_data in grouped_metadata.get("lookups", {}).items():
        if lookup_data.get("type") == "table":
            flat_format["lookups"][lookup_name] = {
                "type": "table",
                "sheet": lookup_data.get("sheet", ""),
                "range": lookup_data.get("range", "")
            }
        else:
            flat_format["lookups"][lookup_name] = lookup_data
    
    return flat_format


def create_tool_interface_metadata(grouped_metadata: Dict[str, Any], workbook_path: str) -> Dict[str, Any]:
    """
    Create tool interface metadata as described in explanation.txt.
    
    This creates the structure that enables:
    - get_excel_input(name): Read input parameter
    - set_excel_input(name, value): Write input parameter  
    - get_design_summary(): Get key outputs
    - lookup_location(key): Execute lookup
    
    Returns metadata in format compatible with excel_tools.py
    """
    # Convert to flat format for excel_tools.py
    flat_metadata = convert_to_excel_tools_format(grouped_metadata)
    
    # Create tool interface description
    tool_interface = {
        "workbook_path": workbook_path,
        "workbook_name": Path(workbook_path).name,
        "semantic_interface": flat_metadata,
        "tool_descriptions": {
            "get_excel_input": {
                "description": "Read an input parameter value from Excel",
                "parameters": {
                    "name": "Semantic name of the input parameter (e.g., 'project_name', 'column_width')"
                },
                "returns": "The current value of the input parameter",
                "available_inputs": list(flat_metadata.get("inputs", {}).keys())
            },
            "set_excel_input": {
                "description": "Write a value to an input parameter in Excel. After writing, Excel must be recalculated.",
                "parameters": {
                    "name": "Semantic name of the input parameter",
                    "value": "The value to write (must match the parameter's data type)"
                },
                "returns": "Confirmation that the value was written",
                "available_inputs": list(flat_metadata.get("inputs", {}).keys())
            },
            "get_design_summary": {
                "description": "Get key design results and outputs from Excel calculations",
                "parameters": {
                    "output_group": "Optional: specific output group to retrieve (e.g., 'utilization_ratios', 'member_resistances')"
                },
                "returns": "Dictionary of output parameter names and their current values",
                "available_outputs": list(flat_metadata.get("outputs", {}).keys())
            },
            "lookup_location": {
                "description": "Look up location-specific data from lookup tables",
                "parameters": {
                    "key": "Location name or key to look up"
                },
                "returns": "Location data (snow loads, wind loads, etc.)",
                "available_lookups": list(flat_metadata.get("lookups", {}).keys())
            },
            "recalculate": {
                "description": "Trigger Excel to recalculate all formulas. MUST be called after set_excel_input operations.",
                "parameters": {},
                "returns": "Confirmation that recalculation completed"
            }
        },
        "input_groups": {},
        "output_groups": {}
    }
    
    # Preserve group information for better tool descriptions
    for group_name, group_data in grouped_metadata.get("inputs", {}).items():
        tool_interface["input_groups"][group_name] = {
            "description": group_data.get("description", ""),
            "parameters": list(group_data.get("cells", {}).keys())
        }
    
    for group_name, group_data in grouped_metadata.get("outputs", {}).items():
        tool_interface["output_groups"][group_name] = {
            "description": group_data.get("description", ""),
            "parameters": list(group_data.get("cells", {}).keys())
        }
    
    return tool_interface


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Create Excel tool interface from semantic metadata"
    )
    parser.add_argument("semantic_metadata", type=Path, help="Input semantic metadata JSON (grouped format)")
    parser.add_argument("workbook_path", type=str, help="Path to Excel workbook")
    parser.add_argument("-o", "--output", type=Path, help="Output JSON file")
    parser.add_argument("--flat-only", action="store_true", help="Output only flat format for excel_tools.py")
    
    args = parser.parse_args()
    
    if not args.semantic_metadata.exists():
        logger.error(f"Semantic metadata file not found: {args.semantic_metadata}")
        return
    
    logger.info(f"Loading semantic metadata from: {args.semantic_metadata}")
    with open(args.semantic_metadata, 'r', encoding='utf-8') as f:
        grouped_metadata = json.load(f)
    
    if args.flat_only:
        # Just convert to flat format
        flat_metadata = convert_to_excel_tools_format(grouped_metadata)
        output_path = args.output or args.semantic_metadata.parent / f"{args.semantic_metadata.stem}_flat.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(flat_metadata, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Flat format saved to: {output_path}")
        logger.info(f"   Inputs: {len(flat_metadata.get('inputs', {}))}")
        logger.info(f"   Outputs: {len(flat_metadata.get('outputs', {}))}")
        logger.info(f"   Lookups: {len(flat_metadata.get('lookups', {}))}")
    else:
        # Create full tool interface
        tool_interface = create_tool_interface_metadata(grouped_metadata, args.workbook_path)
        output_path = args.output or args.semantic_metadata.parent / f"{args.semantic_metadata.stem}_tool_interface.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(tool_interface, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Tool interface saved to: {output_path}")
        logger.info(f"   Available tools: get_excel_input, set_excel_input, get_design_summary, lookup_location, recalculate")
        logger.info(f"   Input parameters: {len(tool_interface['semantic_interface'].get('inputs', {}))}")
        logger.info(f"   Output parameters: {len(tool_interface['semantic_interface'].get('outputs', {}))}")
        logger.info(f"   Lookup tables: {len(tool_interface['semantic_interface'].get('lookups', {}))}")


if __name__ == "__main__":
    main()

