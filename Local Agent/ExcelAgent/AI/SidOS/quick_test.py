#!/usr/bin/env python3
"""
Quick lightweight test script - just tests basic Python functionality
and file I/O without any heavy dependencies.
"""

import sys
import time
from pathlib import Path

def test_basic():
    """Test basic Python operations"""
    print("Test 1: Basic Python operations...")
    result = 2 + 2
    assert result == 4, "Math failed!"
    print("  ✓ Basic math works")
    
    print("Test 2: String operations...")
    test_str = "Hello World"
    assert len(test_str) == 11, "String length failed!"
    print("  ✓ String operations work")
    
    print("Test 3: List operations...")
    test_list = [1, 2, 3]
    assert sum(test_list) == 6, "List sum failed!"
    print("  ✓ List operations work")

def test_file_io():
    """Test file I/O operations"""
    print("\nTest 4: File I/O...")
    test_file = Path(__file__).parent / "semantic_metadata" / "examples" / "example_metadata.json"
    
    if test_file.exists():
        with open(test_file, 'r') as f:
            content = f.read()
        assert len(content) > 0, "File read failed!"
        print(f"  ✓ File read works (read {len(content)} bytes)")
    else:
        print(f"  ⚠ Test file not found: {test_file}")

def test_imports():
    """Test importing local modules"""
    print("\nTest 5: Module imports...")
    try:
        # Import directly from the file to avoid triggering __init__.py
        # which imports excel_tools (and xlwings, which can hang)
        import importlib.util
        semantic_loader_path = Path(__file__).parent / "local_agent" / "semantic_loader.py"
        
        if not semantic_loader_path.exists():
            print(f"  ✗ Module file not found: {semantic_loader_path}")
            return False
        
        spec = importlib.util.spec_from_file_location("semantic_loader", semantic_loader_path)
        semantic_loader = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(semantic_loader)
        
        load_metadata = semantic_loader.load_metadata
        validate_metadata = semantic_loader.validate_metadata
        
        print("  ✓ Module imports work (direct import)")
        
        # Try loading the example metadata
        metadata_path = Path(__file__).parent / "semantic_metadata" / "examples" / "example_metadata.json"
        if metadata_path.exists():
            print("\nTest 6: Loading semantic metadata...")
            metadata = load_metadata(metadata_path)
            print(f"  ✓ Loaded metadata: {len(metadata.get('inputs', {}))} inputs, "
                  f"{len(metadata.get('outputs', {}))} outputs")
        else:
            print("\nTest 6: Skipped (metadata file not found)")
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def main():
    """Run all tests"""
    print("=" * 60)
    print("Quick Lightweight Test")
    print("=" * 60)
    print(f"Python version: {sys.version}")
    print(f"Working directory: {Path.cwd()}")
    print()
    
    start_time = time.time()
    
    try:
        test_basic()
        test_file_io()
        success = test_imports()
        
        elapsed = time.time() - start_time
        print("\n" + "=" * 60)
        if success:
            print(f"✅ All tests passed! (took {elapsed:.3f} seconds)")
        else:
            print(f"⚠️  Some tests had issues (took {elapsed:.3f} seconds)")
        print("=" * 60)
        return 0
    except Exception as e:
        elapsed = time.time() - start_time
        print("\n" + "=" * 60)
        print(f"❌ Test failed after {elapsed:.3f} seconds: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())


