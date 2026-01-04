#!/usr/bin/env python3
"""
Excel Tool API - Core Interface for Excel as Deterministic Compute Engine

This module implements the fixed tool API as specified in the gameplan:
- read_input(name): Read input parameter from Excel
- write_input(name, value): Write input parameter to Excel
- execute_lookup(name, key): Execute lookup operation
- recalculate(): Trigger Excel recalculation (CRITICAL - Excel does the math)
- read_output(name): Read output parameter from Excel

CRITICAL PRINCIPLE: Excel remains the source of truth for all calculations.
This API NEVER performs structural engineering calculations itself.
All mathematical operations happen inside Excel formulas, not in Python.

Author: Sidian Engineering Team
"""

import logging
import time
from typing import Dict, Any, Optional, Union
from pathlib import Path

try:
    import xlwings as xw
    XLWINGS_AVAILABLE = True
except ImportError:
    XLWINGS_AVAILABLE = False
    xw = None

# Configure logging
logger = logging.getLogger(__name__)


class ExcelToolAPIError(Exception):
    """Base exception for Excel Tool API errors"""
    pass


class ExcelToolAPI:
    """
    Excel Tool API - Implements the fixed tool interface for Excel interaction.
    
    This class provides a semantic abstraction layer over Excel workbooks.
    Instead of accessing cells directly (e.g., "B3"), we use semantic names
    (e.g., "span", "load", "moment") that are mapped to cell addresses via
    semantic metadata.
    
    This abstraction allows the system to work with any Excel layout without
    hardcoding cell addresses, as long as semantic metadata is provided.
    
    Attributes:
        wb: xlwings Book object representing the Excel workbook
        inputMap: Dictionary mapping input parameter names to cell locations
        outputMap: Dictionary mapping output parameter names to cell locations
        lookupMap: Dictionary mapping lookup names to lookup configurations
        workbook_path: Path to the Excel workbook file
    """
    
    def __init__(
        self, 
        workbook_path: Union[str, Path],
        semantic_metadata: Dict[str, Any],
        visible: bool = False,
        calculation_timeout: float = 2.0
    ):
        """
        Initialize Excel Tool API with workbook and semantic metadata.
        
        Args:
            workbook_path: Path to Excel workbook file (.xlsx, .xlsm, etc.)
            semantic_metadata: Dictionary containing semantic mappings:
                {
                    "inputs": {
                        "parameter_name": {
                            "sheet": "SheetName",
                            "address": "B3"
                        }
                    },
                    "outputs": {
                        "parameter_name": {
                            "sheet": "SheetName",
                            "address": "G12"
                        }
                    },
                    "lookups": {
                        "lookup_name": {
                            "type": "vlookup",
                            "sheet": "Tables",
                            "range": "A1:D100"
                        }
                    }
                }
            visible: Whether to show Excel application (default: False)
            calculation_timeout: Seconds to wait after triggering recalculation
        
        Raises:
            ExcelToolAPIError: If xlwings is not available or workbook cannot be opened
        """
        if not XLWINGS_AVAILABLE:
            raise ExcelToolAPIError(
                "xlwings is not available. Install with: pip install xlwings"
            )
        
        self.workbook_path = Path(workbook_path)
        if not self.workbook_path.exists():
            raise ExcelToolAPIError(f"Workbook not found: {workbook_path}")
        
        # Store semantic metadata mappings
        self.inputMap = semantic_metadata.get("inputs", {})
        self.outputMap = semantic_metadata.get("outputs", {})
        self.lookupMap = semantic_metadata.get("lookups", {})
        
        # Configuration
        self.visible = visible
        self.calculation_timeout = calculation_timeout
        
        # Open Excel workbook
        try:
            logger.info(f"Opening workbook: {workbook_path}")
            self.wb = xw.Book(str(workbook_path))
            if not visible:
                self.wb.app.visible = False
            logger.info(f"Successfully opened workbook: {self.wb.name}")
        except Exception as e:
            raise ExcelToolAPIError(f"Failed to open workbook: {e}") from e
    
    def read_input(self, name: str) -> Any:
        """
        Read an input parameter value from Excel.
        
        Input parameters are values that influence calculations (e.g., loads,
        dimensions, material properties). These are typically user-editable
        values that drive the engineering calculations in Excel.
        
        Args:
            name: Semantic name of the input parameter (e.g., "span", "load")
        
        Returns:
            The value from the Excel cell (can be int, float, str, etc.)
        
        Raises:
            ExcelToolAPIError: If input name is not found in semantic metadata
            ExcelToolAPIError: If cell cannot be read
        """
        if name not in self.inputMap:
            available = ", ".join(self.inputMap.keys())
            raise ExcelToolAPIError(
                f"Input '{name}' not found in semantic metadata. "
                f"Available inputs: {available}"
            )
        
        try:
            cell_info = self.inputMap[name]
            sheet_name = cell_info["sheet"]
            address = cell_info["address"]
            
            logger.debug(f"Reading input '{name}' from {sheet_name}!{address}")
            sheet = self.wb.sheets[sheet_name]
            value = sheet.range(address).value
            
            logger.info(f"Read input '{name}': {value}")
            return value
        
        except KeyError as e:
            raise ExcelToolAPIError(
                f"Invalid semantic metadata for input '{name}': missing {e}"
            ) from e
        except Exception as e:
            raise ExcelToolAPIError(
                f"Failed to read input '{name}': {e}"
            ) from e
    
    def write_input(self, name: str, value: Any) -> None:
        """
        Write an input parameter value to Excel.
        
        This updates a cell that influences calculations. After writing inputs,
        you MUST call recalculate() to trigger Excel to recompute all formulas
        based on the new input values.
        
        Args:
            name: Semantic name of the input parameter (e.g., "span", "load")
            value: Value to write (int, float, str, etc.)
        
        Raises:
            ExcelToolAPIError: If input name is not found in semantic metadata
            ExcelToolAPIError: If cell cannot be written
        """
        if name not in self.inputMap:
            available = ", ".join(self.inputMap.keys())
            raise ExcelToolAPIError(
                f"Input '{name}' not found in semantic metadata. "
                f"Available inputs: {available}"
            )
        
        try:
            cell_info = self.inputMap[name]
            sheet_name = cell_info["sheet"]
            address = cell_info["address"]
            
            logger.debug(f"Writing input '{name}' = {value} to {sheet_name}!{address}")
            sheet = self.wb.sheets[sheet_name]
            sheet.range(address).value = value
            
            logger.info(f"Wrote input '{name}': {value}")
        
        except KeyError as e:
            raise ExcelToolAPIError(
                f"Invalid semantic metadata for input '{name}': missing {e}"
            ) from e
        except Exception as e:
            raise ExcelToolAPIError(
                f"Failed to write input '{name}': {e}"
            ) from e
    
    def recalculate(self) -> None:
        """
        Trigger Excel recalculation.
        
        CRITICAL: This is where Excel performs all mathematical operations.
        After writing input values, you MUST call this method to trigger Excel
        to recalculate all formulas based on the new inputs.
        
        This method:
        1. Forces Excel to recalculate all formulas in the workbook
        2. Waits for calculation to complete (configurable timeout)
        
        IMPORTANT: The system NEVER performs calculations itself. All engineering
        math happens inside Excel formulas. This method simply triggers Excel
        to execute those formulas.
        
        Raises:
            ExcelToolAPIError: If recalculation fails
        """
        try:
            logger.info("Triggering Excel recalculation...")
            
            # Force full workbook recalculation
            # This ensures all formulas are recalculated, not just dirty cells
            self.wb.app.calculate()
            
            # Wait for calculation to complete
            # Excel calculations are asynchronous, so we need to wait
            # The timeout should be adjusted based on workbook complexity
            time.sleep(self.calculation_timeout)
            
            logger.info("Excel recalculation complete")
        
        except Exception as e:
            raise ExcelToolAPIError(f"Failed to trigger recalculation: {e}") from e
    
    def read_output(self, name: str) -> Any:
        """
        Read an output parameter value from Excel.
        
        Output parameters are calculated results (e.g., forces, moments,
        utilizations, pass/fail flags). These are typically formula cells
        that contain the results of engineering calculations.
        
        IMPORTANT: Outputs are read AFTER recalculation. The values come
        directly from Excel formulas, not from Python calculations.
        
        Args:
            name: Semantic name of the output parameter (e.g., "moment", "shear")
        
        Returns:
            The calculated value from the Excel cell (can be int, float, str, etc.)
        
        Raises:
            ExcelToolAPIError: If output name is not found in semantic metadata
            ExcelToolAPIError: If cell cannot be read
        """
        if name not in self.outputMap:
            available = ", ".join(self.outputMap.keys())
            raise ExcelToolAPIError(
                f"Output '{name}' not found in semantic metadata. "
                f"Available outputs: {available}"
            )
        
        try:
            cell_info = self.outputMap[name]
            sheet_name = cell_info["sheet"]
            address = cell_info["address"]
            
            logger.debug(f"Reading output '{name}' from {sheet_name}!{address}")
            sheet = self.wb.sheets[sheet_name]
            value = sheet.range(address).value
            
            logger.info(f"Read output '{name}': {value}")
            return value
        
        except KeyError as e:
            raise ExcelToolAPIError(
                f"Invalid semantic metadata for output '{name}': missing {e}"
            ) from e
        except Exception as e:
            raise ExcelToolAPIError(
                f"Failed to read output '{name}': {e}"
            ) from e
    
    def execute_lookup(self, name: str, key: Any) -> Any:
        """
        Execute a lookup operation (e.g., table lookup, VLOOKUP).
        
        Lookups are used to resolve inputs into derived parameters. For example,
        looking up a location name to get snow load values, or looking up a
        material grade to get strength properties.
        
        Args:
            name: Semantic name of the lookup operation
            key: Key value to look up
        
        Returns:
            The looked-up value
        
        Raises:
            ExcelToolAPIError: If lookup name is not found or lookup fails
        """
        if name not in self.lookupMap:
            available = ", ".join(self.lookupMap.keys())
            raise ExcelToolAPIError(
                f"Lookup '{name}' not found in semantic metadata. "
                f"Available lookups: {available}"
            )
        
        try:
            lookup_info = self.lookupMap[name]
            lookup_type = lookup_info.get("type", "vlookup")
            sheet_name = lookup_info["sheet"]
            
            logger.debug(f"Executing lookup '{name}' with key: {key}")
            
            # Implementation depends on lookup type
            # For now, support basic VLOOKUP-style operations
            if lookup_type == "vlookup":
                # This is a simplified implementation
                # In production, you'd implement full VLOOKUP logic
                sheet = self.wb.sheets[sheet_name]
                lookup_range = lookup_info.get("range", "A1:D100")
                
                # Find key in first column and return value from specified column
                # This is a placeholder - implement full VLOOKUP logic as needed
                logger.warning(f"Lookup implementation for '{name}' is simplified")
                return None
            
            else:
                raise ExcelToolAPIError(f"Unsupported lookup type: {lookup_type}")
        
        except KeyError as e:
            raise ExcelToolAPIError(
                f"Invalid semantic metadata for lookup '{name}': missing {e}"
            ) from e
        except Exception as e:
            raise ExcelToolAPIError(
                f"Failed to execute lookup '{name}': {e}"
            ) from e
    
    def close(self, save: bool = False) -> None:
        """
        Close the Excel workbook.
        
        Args:
            save: Whether to save the workbook before closing (default: False)
        
        Raises:
            ExcelToolAPIError: If closing fails
        """
        try:
            if save:
                logger.info("Saving workbook before closing...")
                self.wb.save()
            
            logger.info("Closing workbook...")
            self.wb.close()
            logger.info("Workbook closed successfully")
        
        except Exception as e:
            raise ExcelToolAPIError(f"Failed to close workbook: {e}") from e
    
    def __enter__(self):
        """Context manager entry - allows using 'with' statement"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - automatically closes workbook"""
        self.close(save=False)
        return False


# Convenience function for quick operations
def execute_tool_sequence(
    workbook_path: Union[str, Path],
    semantic_metadata: Dict[str, Any],
    tool_sequence: list,
    visible: bool = False
) -> Dict[str, Any]:
    """
    Execute a sequence of tool operations on an Excel workbook.
    
    This is a convenience function that opens a workbook, executes a sequence
    of tool operations, and returns the results.
    
    Args:
        workbook_path: Path to Excel workbook
        semantic_metadata: Semantic metadata mapping
        tool_sequence: List of tool operations:
            [
                {"tool": "write_input", "params": {"name": "span", "value": 15.0}},
                {"tool": "recalculate", "params": {}},
                {"tool": "read_output", "params": {"name": "moment"}}
            ]
        visible: Whether to show Excel (default: False)
    
    Returns:
        Dictionary containing results:
            {
                "success": True/False,
                "results": [...],
                "outputs": {...},
                "error": None or error message
            }
    """
    results = []
    outputs = {}
    error = None
    
    try:
        with ExcelToolAPI(workbook_path, semantic_metadata, visible=visible) as api:
            for tool_call in tool_sequence:
                tool_name = tool_call["tool"]
                params = tool_call.get("params", {})
                
                if tool_name == "read_input":
                    result = api.read_input(params["name"])
                    results.append({
                        "tool": tool_name,
                        "success": True,
                        "result": result
                    })
                
                elif tool_name == "write_input":
                    api.write_input(params["name"], params["value"])
                    results.append({
                        "tool": tool_name,
                        "success": True,
                        "result": None
                    })
                
                elif tool_name == "recalculate":
                    api.recalculate()
                    results.append({
                        "tool": tool_name,
                        "success": True,
                        "result": None
                    })
                
                elif tool_name == "read_output":
                    result = api.read_output(params["name"])
                    results.append({
                        "tool": tool_name,
                        "success": True,
                        "result": result
                    })
                    # Store in outputs dict for easy access
                    outputs[params["name"]] = result
                
                elif tool_name == "execute_lookup":
                    result = api.execute_lookup(params["name"], params["key"])
                    results.append({
                        "tool": tool_name,
                        "success": True,
                        "result": result
                    })
                
                else:
                    raise ValueError(f"Unknown tool: {tool_name}")
        
        return {
            "success": True,
            "results": results,
            "outputs": outputs,
            "error": None
        }
    
    except Exception as e:
        logger.error(f"Tool sequence execution failed: {e}")
        return {
            "success": False,
            "results": results,
            "outputs": outputs,
            "error": str(e)
        }

