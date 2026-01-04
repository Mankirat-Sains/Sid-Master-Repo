#!/usr/bin/env python3
"""
XLWings Excel Extractor - Extract cell information using XLWings

This script extracts Excel information using XLWings (instead of AI):
- Cell addresses (e.g., A11)
- Cell content/text
- Cell colors (fill color)

XLWings provides direct access to Excel's native properties, making it
more reliable for color extraction than openpyxl in some cases.

Author: Sidian Engineering Team
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

try:
    import xlwings as xw
except ImportError:
    print("ERROR: xlwings is not installed. Install it with: pip install xlwings")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class XLWingsExcelExtractor:
    """
    Extract Excel cell information using XLWings.
    
    Extracts:
    - Cell address (e.g., A11)
    - Cell content/text
    - Cell fill color (RGB)
    """
    
    def __init__(self):
        """Initialize the extractor."""
        self.app = None
    
    def rgb_to_hex(self, rgb: tuple) -> str:
        """
        Convert RGB tuple to hex string.
        
        Args:
            rgb: RGB tuple (R, G, B) with values 0-255
        
        Returns:
            Hex string (e.g., "FF00FF00" for green)
        """
        if not rgb or len(rgb) < 3:
            return None
        
        # XLWings returns RGB as (R, G, B) with values 0-255
        r, g, b = int(rgb[0]), int(rgb[1]), int(rgb[2])
        return f"{r:02X}{g:02X}{b:02X}"
    
    def extract_cell_info(self, cell) -> Dict[str, Any]:
        """
        Extract information from a single cell.
        
        Args:
            cell: XLWings cell object
        
        Returns:
            Dictionary with cell information:
            {
                "cell": "A11",
                "content": "Some text",
                "fill_color": "FF00FF00",
                "fill_color_rgb": (255, 0, 255),
                "text_color": "00000000",
                "text_color_rgb": (0, 0, 0),
                "has_formula": False,
                "formula": "=SUM(A1:A10)"
            }
        """
        try:
            cell_info = {
                "cell": cell.address.replace("$", ""),  # Remove $ from absolute references
                "content": None,
                "fill_color": None,
                "fill_color_rgb": None,
                "text_color": None,
                "text_color_rgb": None,
                "has_formula": False,
                "formula": None
            }
            
            # Get cell content
            try:
                value = cell.value
                if value is not None:
                    cell_info["content"] = str(value)
            except Exception as e:
                logger.debug(f"Could not get value for {cell_info['cell']}: {e}")
            
            # Check if cell has formula
            try:
                formula = cell.formula
                if formula and formula.startswith("="):
                    cell_info["has_formula"] = True
                    cell_info["formula"] = formula
            except Exception as e:
                logger.debug(f"Could not get formula for {cell_info['cell']}: {e}")
            
            # Get fill color (background color)
            try:
                # Method 1: Try XLWings .color property (works on some platforms)
                fill_color_rgb = None
                try:
                    fill_color_rgb = cell.color
                except:
                    pass
                
                # Method 2: If .color doesn't work, use Excel API directly
                if fill_color_rgb is None:
                    try:
                        interior_color = cell.api.Interior.Color
                        if interior_color and interior_color != -4142:  # -4142 = xlNone
                            # Excel uses BGR format internally
                            b = interior_color & 0xFF
                            g = (interior_color >> 8) & 0xFF
                            r = (interior_color >> 16) & 0xFF
                            fill_color_rgb = (r, g, b)
                    except:
                        pass
                
                # Convert to hex if we got a color
                if fill_color_rgb:
                    if isinstance(fill_color_rgb, (list, tuple)) and len(fill_color_rgb) >= 3:
                        cell_info["fill_color_rgb"] = tuple(int(x) for x in fill_color_rgb[:3])
                        cell_info["fill_color"] = self.rgb_to_hex(fill_color_rgb[:3])
            except Exception as e:
                logger.debug(f"Could not get fill color for {cell_info['cell']}: {e}")
            
            # Get text/font color
            try:
                # XLWings: access font color via .api
                # Try multiple methods to get font color
                font_color = None
                
                # Method 1: Direct API access
                try:
                    font_color = cell.api.Font.Color
                except:
                    pass
                
                # Method 2: Try via Font object
                if font_color is None:
                    try:
                        font_obj = cell.api.Font
                        if hasattr(font_obj, 'Color'):
                            font_color = font_obj.Color
                    except:
                        pass
                
                # Method 3: Try via Interior/Font properties
                if font_color is None:
                    try:
                        # Sometimes need to access differently on macOS
                        font_color = cell.api.Font.ColorIndex
                        if font_color and font_color > 0:
                            # ColorIndex is not the same as Color, but indicates non-default
                            # Try to get actual color
                            try:
                                font_color = cell.api.Font.Color
                            except:
                                pass
                    except:
                        pass
                
                if font_color and font_color != -4142:  # -4142 = xlNone in Excel
                    # Excel's Color property returns a long integer in BGR format
                    # Convert to RGB
                    if isinstance(font_color, (int, float)):
                        b = int(font_color) & 0xFF
                        g = (int(font_color) >> 8) & 0xFF
                        r = (int(font_color) >> 16) & 0xFF
                        text_color_rgb = (r, g, b)
                        cell_info["text_color_rgb"] = text_color_rgb
                        cell_info["text_color"] = self.rgb_to_hex(text_color_rgb)
            except Exception as e:
                logger.debug(f"Could not get text color for {cell_info['cell']}: {e}")
            
            return cell_info
        
        except Exception as e:
            logger.warning(f"Error extracting info for cell: {e}")
            return {
                "cell": cell.address.replace("$", "") if hasattr(cell, 'address') else "unknown",
                "content": None,
                "error": str(e)
            }
    
    def _extract_sheet_from_workbook(self, wb, sheet_name: str, 
                                    max_rows: Optional[int] = None, max_cols: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Extract all cell information from a sheet using an already-open workbook.
        Internal method - use extract_sheet() for standalone extraction.
        """
        try:
            # Get the sheet
            if sheet_name not in [s.name for s in wb.sheets]:
                raise ValueError(f"Sheet '{sheet_name}' not found in workbook")
            
            ws = wb.sheets[sheet_name]
            logger.info(f"Extracting from sheet: {sheet_name}")
            
            # Get used range
            used_range = ws.used_range
            if used_range is None:
                logger.warning(f"No used range found in sheet {sheet_name}")
                return []
            
            # Determine range to extract
            last_row = used_range.last_cell.row
            last_col = used_range.last_cell.column
            
            if max_rows:
                last_row = min(last_row, max_rows)
            if max_cols:
                last_col = min(last_col, max_cols)
            
            # Helper function to convert column number to letter
            def col_num_to_letter(n):
                result = ""
                while n > 0:
                    n -= 1
                    result = chr(65 + (n % 26)) + result
                    n //= 26
                return result
            
            logger.info(f"Extracting cells from range: A1 to {col_num_to_letter(last_col)}{last_row}")
            
            # Extract all cells in the range
            cells_data = []
            for row in range(1, last_row + 1):
                for col in range(1, last_col + 1):
                    try:
                        cell = ws.cells(row, col)
                        cell_info = self.extract_cell_info(cell)
                        cells_data.append(cell_info)
                    except Exception as e:
                        logger.debug(f"Error extracting cell at row {row}, col {col}: {e}")
                        continue
                
                # Progress indicator
                if row % 50 == 0:
                    logger.info(f"  Processed {row} rows...")
            
            logger.info(f"Extracted {len(cells_data)} cells from sheet {sheet_name}")
            return cells_data
        
        except Exception as e:
            logger.error(f"Error extracting sheet: {e}")
            raise
    
    def extract_sheet(self, workbook_path: Union[str, Path], sheet_name: str, 
                     max_rows: Optional[int] = None, max_cols: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Extract all cell information from a sheet.
        
        Args:
            workbook_path: Path to Excel workbook
            sheet_name: Name of sheet to extract
            max_rows: Maximum number of rows to extract (None = all)
            max_cols: Maximum number of columns to extract (None = all)
        
        Returns:
            List of cell information dictionaries
        """
        workbook_path = Path(workbook_path)
        if not workbook_path.exists():
            raise FileNotFoundError(f"Workbook not found: {workbook_path}")
        
        logger.info(f"Opening workbook: {workbook_path}")
        
        wb = None
        try:
            # Open workbook with XLWings
            wb = xw.Book(str(workbook_path))
            logger.info(f"Workbook opened successfully")
            
            # Use internal method to extract
            return self._extract_sheet_from_workbook(wb, sheet_name, max_rows, max_cols)
        
        finally:
            # Close workbook safely
            if wb:
                try:
                    wb.close()
                    logger.info("Workbook closed")
                except Exception as close_error:
                    logger.debug(f"Error closing workbook (may already be closed): {close_error}")
    
    def extract_workbook(self, workbook_path: Union[str, Path], 
                        output_path: Optional[Union[str, Path]] = None,
                        max_rows: Optional[int] = None,
                        max_cols: Optional[int] = None,
                        sheet_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Extract cell information from entire workbook.
        
        Args:
            workbook_path: Path to Excel workbook
            output_path: Optional path to save JSON output
            max_rows: Maximum rows per sheet to extract
            max_cols: Maximum columns per sheet to extract
            sheet_names: List of sheet names to extract (None = all sheets)
        
        Returns:
            Dictionary with extracted data:
            {
                "workbook_path": "...",
                "workbook_name": "...",
                "sheets": {
                    "Sheet1": [...],
                    "Sheet2": [...]
                }
            }
        """
        workbook_path = Path(workbook_path)
        if not workbook_path.exists():
            raise FileNotFoundError(f"Workbook not found: {workbook_path}")
        
        logger.info(f"\n📄 Extracting from workbook: {workbook_path.name}")
        
        wb = None
        try:
            # Open workbook once for all extractions
            wb = xw.Book(str(workbook_path))
            all_sheet_names = [s.name for s in wb.sheets]
            
            # Determine which sheets to extract
            if sheet_names is None:
                sheet_names = all_sheet_names
            else:
                # Validate sheet names
                invalid_sheets = [s for s in sheet_names if s not in all_sheet_names]
                if invalid_sheets:
                    logger.warning(f"Invalid sheet names: {invalid_sheets}")
                sheet_names = [s for s in sheet_names if s in all_sheet_names]
            
            logger.info(f"Extracting from {len(sheet_names)} sheet(s): {', '.join(sheet_names)}")
            
            # Extract each sheet using the already-open workbook
            result = {
                "workbook_path": str(workbook_path),
                "workbook_name": workbook_path.name,
                "sheets": {}
            }
            
            for sheet_name in sheet_names:
                logger.info(f"\n📊 Extracting sheet: {sheet_name}")
                try:
                    cells_data = self._extract_sheet_from_workbook(wb, sheet_name, max_rows, max_cols)
                    result["sheets"][sheet_name] = cells_data
                    logger.info(f"✅ Extracted {len(cells_data)} cells from {sheet_name}")
                except Exception as e:
                    logger.error(f"❌ Error extracting sheet {sheet_name}: {e}")
                    result["sheets"][sheet_name] = []
            
            # Save to file if output path provided
            if output_path:
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                
                logger.info(f"\n✅ Data saved to: {output_path}")
            
            # Summary
            total_cells = sum(len(cells) for cells in result["sheets"].values())
            logger.info(f"\n✅ Extraction complete:")
            logger.info(f"   Total cells extracted: {total_cells}")
            logger.info(f"   Sheets processed: {len(result['sheets'])}")
            
            return result
        
        except Exception as e:
            logger.error(f"❌ Extraction failed: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        finally:
            # Close workbook safely
            if wb:
                try:
                    wb.close()
                    logger.info("Workbook closed")
                except Exception as close_error:
                    logger.debug(f"Error closing workbook (may already be closed): {close_error}")


def main():
    """Main entry point for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="XLWings Excel Extractor - Extract cell addresses, content, and colors"
    )
    parser.add_argument("workbook", type=Path, help="Path to Excel workbook")
    parser.add_argument("-o", "--output", type=Path, help="Output path for JSON file")
    parser.add_argument("--sheet", type=str, help="Specific sheet name to extract (default: all sheets)")
    parser.add_argument("--max-rows", type=int, help="Maximum rows per sheet to extract")
    parser.add_argument("--max-cols", type=int, help="Maximum columns per sheet to extract")
    
    args = parser.parse_args()
    
    # Create extractor
    extractor = XLWingsExcelExtractor()
    
    # Determine output path
    output_path = args.output
    if not output_path:
        output_path = args.workbook.parent / f"{args.workbook.stem}_xlwings_extract.json"
    
    # Extract
    sheet_names = [args.sheet] if args.sheet else None
    result = extractor.extract_workbook(
        args.workbook,
        output_path=output_path,
        max_rows=args.max_rows,
        max_cols=args.max_cols,
        sheet_names=sheet_names
    )
    
    print(f"\n✅ Success! Data extracted to: {output_path}")
    print(f"   Total cells: {sum(len(cells) for cells in result['sheets'].values())}")


if __name__ == "__main__":
    main()

