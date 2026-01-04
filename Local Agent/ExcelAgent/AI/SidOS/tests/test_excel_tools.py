#!/usr/bin/env python3
"""
Test Suite for Excel Tool API

This test suite verifies that the Excel Tool API correctly implements
the gameplan's principle: Excel is the source of truth for calculations.

Author: Sidian Engineering Team
"""

import unittest
import tempfile
import json
import sys
from pathlib import Path

# Add SidOS directory to path so we can import local_agent
sys.path.insert(0, str(Path(__file__).parent.parent))

# Note: These tests require xlwings and Excel to be installed
# They are integration tests that actually interact with Excel


class TestExcelToolAPI(unittest.TestCase):
    """Test cases for ExcelToolAPI"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a temporary Excel file for testing
        # In a real test, you'd create a test workbook with known formulas
        self.temp_dir = tempfile.mkdtemp()
        self.test_workbook = Path(self.temp_dir) / "test.xlsx"
        
        # Create minimal semantic metadata
        self.semantic_metadata = {
            "inputs": {
                "span": {
                    "sheet": "Sheet1",
                    "address": "B3"
                },
                "load": {
                    "sheet": "Sheet1",
                    "address": "B4"
                }
            },
            "outputs": {
                "moment": {
                    "sheet": "Sheet1",
                    "address": "G12"
                }
            },
            "lookups": {}
        }
    
    def test_read_input(self):
        """Test reading input parameters"""
        # This test would require a real Excel file
        # For now, it's a placeholder
        pass
    
    def test_write_input(self):
        """Test writing input parameters"""
        # This test would require a real Excel file
        # For now, it's a placeholder
        pass
    
    def test_recalculate(self):
        """Test triggering Excel recalculation"""
        # This test would require a real Excel file with formulas
        # For now, it's a placeholder
        pass
    
    def test_read_output(self):
        """Test reading output parameters"""
        # This test would require a real Excel file with formulas
        # For now, it's a placeholder
        pass


class TestSemanticLoader(unittest.TestCase):
    """Test cases for semantic metadata loader"""
    
    def test_load_metadata(self):
        """Test loading semantic metadata from JSON"""
        from local_agent.semantic_loader import load_metadata, create_empty_metadata
        
        # Create temporary metadata file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            metadata = create_empty_metadata()
            metadata["inputs"]["test"] = {
                "sheet": "Sheet1",
                "address": "B3"
            }
            json.dump(metadata, f)
            temp_path = f.name
        
        try:
            loaded = load_metadata(temp_path)
            self.assertIn("inputs", loaded)
            self.assertIn("test", loaded["inputs"])
            self.assertEqual(loaded["inputs"]["test"]["address"], "B3")
        finally:
            Path(temp_path).unlink()
    
    def test_validate_metadata(self):
        """Test metadata validation"""
        from local_agent.semantic_loader import validate_metadata, SemanticMetadataError
        
        # Valid metadata
        valid_metadata = {
            "inputs": {
                "span": {
                    "sheet": "Sheet1",
                    "address": "B3"
                }
            },
            "outputs": {},
            "lookups": {}
        }
        validate_metadata(valid_metadata)  # Should not raise
        
        # Invalid metadata - missing required field
        invalid_metadata = {
            "inputs": {
                "span": {
                    "sheet": "Sheet1"
                    # Missing "address"
                }
            }
        }
        with self.assertRaises(SemanticMetadataError):
            validate_metadata(invalid_metadata)


if __name__ == "__main__":
    unittest.main()

