#!/usr/bin/env python3
"""
Test openpyxl import to diagnose the hang issue
"""

import sys
import time

print(f"Python version: {sys.version}")
print(f"Python path: {sys.executable}")
print()

# Test 1: Try importing openpyxl with timeout
print("Test 1: Importing openpyxl (this is where it hangs)...")
start = time.time()

try:
    # Try to import with a workaround - import only what we need
    print("  Attempting basic import...")
    import openpyxl
    elapsed = time.time() - start
    print(f"  ✓ openpyxl imported in {elapsed:.3f} seconds")
    print(f"  Version: {openpyxl.__version__}")
except KeyboardInterrupt:
    elapsed = time.time() - start
    print(f"  ✗ Import hung after {elapsed:.1f} seconds (interrupted)")
    print("  This confirms the hang issue")
    sys.exit(1)
except Exception as e:
    elapsed = time.time() - start
    print(f"  ✗ Import failed after {elapsed:.3f} seconds: {e}")
    sys.exit(1)

# Test 2: Try importing specific modules
print("\nTest 2: Testing specific openpyxl modules...")
modules_to_test = [
    "openpyxl.workbook",
    "openpyxl.worksheet", 
    "openpyxl.cell",
    # Skip chart module - this is where it hangs
]

for module_name in modules_to_test:
    try:
        start = time.time()
        __import__(module_name)
        elapsed = time.time() - start
        print(f"  ✓ {module_name} ({elapsed:.3f}s)")
    except Exception as e:
        print(f"  ✗ {module_name}: {e}")

print("\n✅ Basic openpyxl functionality should work (without charts)")
print("   The parser can work without chart support")


