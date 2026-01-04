#!/usr/bin/env python3
"""
Metadata Converter - Converts Parser Output to Local Agent Format

This module converts the intelligent parser's output into the semantic metadata
format required by the local agent's ExcelToolAPI.

The converter handles:
- Converting semantic groups to individual cell mappings
- Flattening groups for direct cell access
- Creating both grouped and flat representations
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union

logger = logging.getLogger(__name__)


def convert_to_local_agent_format(parser_output: Dict[str, Any], flatten_groups: bool = False) -> Dict[str, Any]:
    """
    Convert parser output to local agent semantic metadata format.
    
    The parser creates semantic groups (e.g., "location_data" with multiple cells).
    This converter can either:
    1. Keep groups (for high-level operations)
    2. Flatten to individual cells (for direct access)
    
    Args:
        parser_output: Output from IntelligentExcelParser.parse_workbook()
        flatten_groups: If True, flatten groups to individual cell mappings
    
    Returns:
        Metadata in local agent format:
        {
            "inputs": {
                "parameter_name": {
                    "sheet": "SheetName",
                    "address": "B3"
                }
            },
            "outputs": {...},
            "lookups": {...}
        }
    """
    semantic_interface = parser_output.get("semantic_interface", {})
    
    if flatten_groups:
        # Flatten groups to individual cell mappings
        return _flatten_groups(semantic_interface)
    else:
        # Keep groups but convert to local agent format
        return _convert_groups(semantic_interface)


def _flatten_groups(semantic_interface: Dict[str, Any]) -> Dict[str, Any]:
    """
    Flatten semantic groups to individual cell mappings.
    
    Converts:
    {
        "location_data": {
            "cells": {
                "location_name": "B2",
                "ground_snow_load": "B6"
            }
        }
    }
    
    To:
    {
        "location_name": {"sheet": "...", "address": "B2"},
        "ground_snow_load": {"sheet": "...", "address": "B6"}
    }
    """
    result = {
        "inputs": {},
        "outputs": {},
        "lookups": {}
    }
    
    # Process inputs
    for group_name, group_info in semantic_interface.get("inputs", {}).items():
        if group_info.get("type") == "group":
            sheet = group_info.get("sheet", "Sheet1")
            cells = group_info.get("cells", {})
            
            for param_name, cell_address in cells.items():
                result["inputs"][param_name] = {
                    "sheet": sheet,
                    "address": cell_address,
                    "group": group_name,
                    "description": group_info.get("description", "")
                }
    
    # Process outputs
    for group_name, group_info in semantic_interface.get("outputs", {}).items():
        if group_info.get("type") == "group":
            sheet = group_info.get("sheet", "Sheet1")
            cells = group_info.get("cells", {})
            
            for param_name, cell_address in cells.items():
                result["outputs"][param_name] = {
                    "sheet": sheet,
                    "address": cell_address,
                    "group": group_name,
                    "description": group_info.get("description", "")
                }
    
    # Process lookups
    for lookup_name, lookup_info in semantic_interface.get("lookups", {}).items():
        result["lookups"][lookup_name] = lookup_info
    
    return result


def _convert_groups(semantic_interface: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert groups to local agent format while preserving group structure.
    
    This allows the local agent to work with groups directly.
    """
    result = {
        "inputs": {},
        "outputs": {},
        "lookups": {}
    }
    
    # Convert inputs (preserve groups)
    for group_name, group_info in semantic_interface.get("inputs", {}).items():
        if group_info.get("type") == "group":
            result["inputs"][group_name] = {
                "type": "group",
                "sheet": group_info.get("sheet", "Sheet1"),
                "cells": group_info.get("cells", {}),
                "description": group_info.get("description", "")
            }
    
    # Convert outputs (preserve groups)
    for group_name, group_info in semantic_interface.get("outputs", {}).items():
        if group_info.get("type") == "group":
            result["outputs"][group_name] = {
                "type": "group",
                "sheet": group_info.get("sheet", "Sheet1"),
                "cells": group_info.get("cells", {}),
                "description": group_info.get("description", "")
            }
    
    # Convert lookups
    result["lookups"] = semantic_interface.get("lookups", {})
    
    return result


def convert_parser_output_to_metadata(
    parser_output_path: Union[str, Path],
    output_path: Union[str, Path],
    flatten: bool = True
) -> Dict[str, Any]:
    """
    Convert parser output file to local agent metadata format.
    
    Args:
        parser_output_path: Path to parser output JSON
        output_path: Path to save converted metadata
        flatten: Whether to flatten groups to individual cells
    
    Returns:
        Converted metadata dictionary
    """
    parser_output_path = Path(parser_output_path)
    if not parser_output_path.exists():
        raise FileNotFoundError(f"Parser output not found: {parser_output_path}")
    
    # Load parser output
    with open(parser_output_path, 'r', encoding='utf-8') as f:
        parser_output = json.load(f)
    
    # Convert
    metadata = convert_to_local_agent_format(parser_output, flatten_groups=flatten)
    
    # Save
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    logger.info(f"✅ Converted metadata saved to: {output_path}")
    
    return metadata


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Convert parser output to local agent metadata")
    parser.add_argument("parser_output", type=Path, help="Path to parser output JSON")
    parser.add_argument("-o", "--output", type=Path, help="Output path for metadata")
    parser.add_argument("--flatten", action="store_true", help="Flatten groups to individual cells")
    
    args = parser.parse_args()
    
    output_path = args.output or (args.parser_output.parent / f"{args.parser_output.stem}_agent_metadata.json")
    
    convert_parser_output_to_metadata(args.parser_output, output_path, flatten=args.flatten)

