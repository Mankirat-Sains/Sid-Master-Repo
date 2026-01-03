#!/usr/bin/env python3
"""
Semantic Metadata Loader

This module handles loading and validation of semantic metadata files.
Semantic metadata defines the mapping between semantic parameter names
(e.g., "span", "load", "moment") and their physical locations in Excel
workbooks (sheet name + cell address).

The semantic abstraction layer allows the system to work with any Excel
layout without hardcoding cell addresses, as long as semantic metadata
is provided.

Author: Sidian Engineering Team
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union

logger = logging.getLogger(__name__)


class SemanticMetadataError(Exception):
    """Base exception for semantic metadata errors"""
    pass


def load_metadata(metadata_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load semantic metadata from a JSON file.
    
    Semantic metadata defines the semantic interface for an Excel workbook:
    - inputs: Parameters that influence calculations (user-editable)
    - outputs: Calculated results from Excel formulas
    - lookups: Lookup tables and operations
    
    Expected JSON structure:
    {
        "inputs": {
            "parameter_name": {
                "sheet": "SheetName",
                "address": "B3",
                "description": "Optional description"
            }
        },
        "outputs": {
            "parameter_name": {
                "sheet": "SheetName",
                "address": "G12",
                "description": "Optional description"
            }
        },
        "lookups": {
            "lookup_name": {
                "type": "vlookup",
                "sheet": "Tables",
                "range": "A1:D100",
                "description": "Optional description"
            }
        }
    }
    
    Args:
        metadata_path: Path to JSON metadata file
    
    Returns:
        Dictionary containing semantic metadata
    
    Raises:
        SemanticMetadataError: If file cannot be loaded or is invalid
    """
    metadata_path = Path(metadata_path)
    
    if not metadata_path.exists():
        raise SemanticMetadataError(f"Metadata file not found: {metadata_path}")
    
    try:
        logger.info(f"Loading semantic metadata from: {metadata_path}")
        
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        # Validate metadata structure
        validate_metadata(metadata)
        
        logger.info(
            f"Loaded metadata: {len(metadata.get('inputs', {}))} inputs, "
            f"{len(metadata.get('outputs', {}))} outputs, "
            f"{len(metadata.get('lookups', {}))} lookups"
        )
        
        return metadata
    
    except json.JSONDecodeError as e:
        raise SemanticMetadataError(
            f"Invalid JSON in metadata file: {e}"
        ) from e
    except Exception as e:
        raise SemanticMetadataError(
            f"Failed to load metadata: {e}"
        ) from e


def validate_metadata(metadata: Dict[str, Any]) -> None:
    """
    Validate semantic metadata structure.
    
    Ensures that metadata has the correct structure and required fields
    for each parameter definition.
    
    Args:
        metadata: Metadata dictionary to validate
    
    Raises:
        SemanticMetadataError: If metadata structure is invalid
    """
    if not isinstance(metadata, dict):
        raise SemanticMetadataError("Metadata must be a dictionary")
    
    # Validate inputs
    if "inputs" in metadata:
        if not isinstance(metadata["inputs"], dict):
            raise SemanticMetadataError("'inputs' must be a dictionary")
        
        for param_name, param_info in metadata["inputs"].items():
            if not isinstance(param_info, dict):
                raise SemanticMetadataError(
                    f"Input '{param_name}' must be a dictionary"
                )
            
            if "sheet" not in param_info:
                raise SemanticMetadataError(
                    f"Input '{param_name}' missing required field: 'sheet'"
                )
            
            if "address" not in param_info:
                raise SemanticMetadataError(
                    f"Input '{param_name}' missing required field: 'address'"
                )
    
    # Validate outputs
    if "outputs" in metadata:
        if not isinstance(metadata["outputs"], dict):
            raise SemanticMetadataError("'outputs' must be a dictionary")
        
        for param_name, param_info in metadata["outputs"].items():
            if not isinstance(param_info, dict):
                raise SemanticMetadataError(
                    f"Output '{param_name}' must be a dictionary"
                )
            
            if "sheet" not in param_info:
                raise SemanticMetadataError(
                    f"Output '{param_name}' missing required field: 'sheet'"
                )
            
            if "address" not in param_info:
                raise SemanticMetadataError(
                    f"Output '{param_name}' missing required field: 'address'"
                )
    
    # Validate lookups
    if "lookups" in metadata:
        if not isinstance(metadata["lookups"], dict):
            raise SemanticMetadataError("'lookups' must be a dictionary")
        
        for lookup_name, lookup_info in metadata["lookups"].items():
            if not isinstance(lookup_info, dict):
                raise SemanticMetadataError(
                    f"Lookup '{lookup_name}' must be a dictionary"
                )
            
            if "sheet" not in lookup_info:
                raise SemanticMetadataError(
                    f"Lookup '{lookup_name}' missing required field: 'sheet'"
                )


def save_metadata(metadata: Dict[str, Any], metadata_path: Union[str, Path]) -> None:
    """
    Save semantic metadata to a JSON file.
    
    Args:
        metadata: Metadata dictionary to save
        metadata_path: Path where to save the metadata file
    
    Raises:
        SemanticMetadataError: If metadata cannot be saved
    """
    metadata_path = Path(metadata_path)
    
    try:
        # Validate before saving
        validate_metadata(metadata)
        
        logger.info(f"Saving semantic metadata to: {metadata_path}")
        
        # Create parent directory if it doesn't exist
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        logger.info("Metadata saved successfully")
    
    except Exception as e:
        raise SemanticMetadataError(f"Failed to save metadata: {e}") from e


def create_empty_metadata() -> Dict[str, Any]:
    """
    Create an empty semantic metadata template.
    
    Returns:
        Empty metadata dictionary with proper structure
    """
    return {
        "inputs": {},
        "outputs": {},
        "lookups": {}
    }

