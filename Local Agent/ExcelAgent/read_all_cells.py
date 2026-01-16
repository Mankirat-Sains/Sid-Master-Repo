#!/usr/bin/env python3
"""
Temporary script to read every single cell from specified Excel sheets.

This script reads all cells from:
- INFO 4-12 Ceil
- L(1)

And outputs information in the format:
Location: A11
Value: James is the best
Type: String
Formula: Null

Location: A12
Value: 12
Type: Number
Formula: A10*A30
"""

import xlwings as xw
from pathlib import Path
import sys
import json
from datetime import datetime

# Excel file path
EXCEL_FILE = "/Users/jameshinsperger/Desktop/Desktop - MacBook Pro (2)/Sidian/Vibeeng/Excel Templates/0 - Beam Design - Sidian - VBA (Template)6.xlsx"

# Sheets to read
SHEETS = ["INFO 4-12 Ceil", "L(1)"]


def get_cell_type(value):
    """Determine the type of a cell value."""
    if value is None:
        return "Empty"
    elif isinstance(value, (int, float)):
        return "Number"
    elif isinstance(value, str):
        return "String"
    elif isinstance(value, bool):
        return "Boolean"
    elif hasattr(value, 'date'):
        return "Date"
    else:
        return "Other"


def read_all_cells():
    """Read all cells from the specified sheets."""
    file_path = Path(EXCEL_FILE)
    
    if not file_path.exists():
        print(f"ERROR: File not found: {EXCEL_FILE}")
        sys.exit(1)
    
    file_name = file_path.name
    
    try:
        # Open the workbook
        print(f"Opening workbook: {file_name}")
        wb = xw.Book(str(file_path))
        wb.app.visible = False  # Run in background
        
        all_cells_data = []
        
        for sheet_name in SHEETS:
            if sheet_name not in wb.sheet_names:
                print(f"WARNING: Sheet '{sheet_name}' not found. Available sheets: {wb.sheet_names}")
                continue
            
            print(f"\nReading sheet: {sheet_name}")
            sheet = wb.sheets[sheet_name]
            
            # Get the used range
            try:
                used_range = sheet.used_range
                if used_range is None:
                    print(f"  No used cells found in sheet '{sheet_name}'")
                    continue
                
                # Get the range boundaries
                last_row = used_range.last_cell.row
                last_col = used_range.last_cell.column
                
                print(f"  Used range: {used_range.address}")
                print(f"  Rows: 1 to {last_row}, Columns: 1 to {last_col}")
                
                # Iterate through all cells in the used range
                cell_count = 0
                for row in range(1, last_row + 1):
                    for col in range(1, last_col + 1):
                        cell = sheet.cells(row, col)
                        
                        # Get cell address (e.g., A11)
                        cell_address = cell.address.replace("$", "")
                        
                        # Get cell value
                        try:
                            cell_value = cell.value
                        except Exception as e:
                            cell_value = None
                            print(f"  Warning: Could not read value for {cell_address}: {e}")
                        
                        # Skip cells with no value (null/None)
                        if cell_value is None:
                            continue
                        
                        # Get cell formula
                        try:
                            formula = cell.formula
                            if formula and formula.startswith("="):
                                formula_str = formula
                            else:
                                formula_str = None
                        except Exception:
                            formula_str = None
                        
                        # Determine cell type
                        cell_type = get_cell_type(cell_value)
                        
                        # Store cell information
                        cell_info = {
                            "file_name": file_name,
                            "sheet_name": sheet_name,
                            "location": cell_address,
                            "value": cell_value,
                            "type": cell_type,
                            "formula": formula_str if formula_str else "Null"
                        }
                        
                        all_cells_data.append(cell_info)
                        cell_count += 1
                
                print(f"  Read {cell_count} cells from sheet '{sheet_name}'")
                
            except Exception as e:
                print(f"  ERROR reading sheet '{sheet_name}': {e}")
                continue
        
        # Close the workbook
        wb.close()
        
        # Write JSON output file
        script_dir = Path(__file__).parent
        output_file = script_dir / "excel_cells_output.json"
        
        # Prepare JSON output with metadata
        json_output = {
            "source_file": file_name,
            "source_path": str(file_path),
            "sheets_read": SHEETS,
            "extraction_date": datetime.now().isoformat(),
            "total_cells": len(all_cells_data),
            "cells": all_cells_data
        }
        
        # Write JSON file
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(json_output, f, indent=2, ensure_ascii=False, default=str)
            print(f"\n✓ JSON output written to: {output_file}")
        except Exception as e:
            print(f"\n✗ ERROR writing JSON file: {e}")
        
        # Print summary to console
        print("\n" + "="*80)
        print("CELL INFORMATION SUMMARY")
        print("="*80)
        print(f"Total cells read: {len(all_cells_data)}")
        print(f"Output file: {output_file}")
        
        # Print all cell information
        print("\n" + "="*80)
        print("CELL INFORMATION")
        print("="*80)
        
        current_sheet = None
        for cell_info in all_cells_data:
            # Print sheet header when sheet changes
            if cell_info['sheet_name'] != current_sheet:
                current_sheet = cell_info['sheet_name']
                print(f"\n{'='*80}")
                print(f"File: {cell_info['file_name']}")
                print(f"Sheet: {cell_info['sheet_name']}")
                print(f"{'='*80}\n")
            
            # Print cell information in the requested format
            print(f"Location: {cell_info['location']}")
            print(f"Value: {cell_info['value']}")
            print(f"Type: {cell_info['type']}")
            print(f"Formula: {cell_info['formula']}")
            print()
        
        return all_cells_data
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    read_all_cells()
