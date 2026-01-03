#!/usr/bin/env python3
"""
Quick Test Script for Local Agent

This script demonstrates the local agent functionality with a simple example.
It shows how to use the Excel Tool API to interact with Excel workbooks.

Usage:
    python test_local_agent.py <workbook_path> <metadata_path>

Example:
    python test_local_agent.py "Design.xlsx" "semantic_metadata/examples/example_metadata.json"
"""

import sys
import json
from pathlib import Path

# Add local_agent to path
sys.path.insert(0, str(Path(__file__).parent))

from local_agent import ExcelToolAPI, load_metadata, execute_tool_sequence


def main():
    """Test the local agent with a simple example"""
    
    if len(sys.argv) < 3:
        print("Usage: python test_local_agent.py <workbook_path> <metadata_path>")
        print("\nExample:")
        print('  python test_local_agent.py "Design.xlsx" "semantic_metadata/examples/example_metadata.json"')
        sys.exit(1)
    
    workbook_path = Path(sys.argv[1])
    metadata_path = Path(sys.argv[2])
    
    if not workbook_path.exists():
        print(f"Error: Workbook not found: {workbook_path}")
        sys.exit(1)
    
    if not metadata_path.exists():
        print(f"Error: Metadata file not found: {metadata_path}")
        sys.exit(1)
    
    print("=" * 60)
    print("SidOS Local Agent - Test Script")
    print("=" * 60)
    print(f"Workbook: {workbook_path}")
    print(f"Metadata: {metadata_path}")
    print()
    
    try:
        # Load semantic metadata
        print("Loading semantic metadata...")
        metadata = load_metadata(metadata_path)
        print(f"✅ Loaded {len(metadata.get('inputs', {}))} inputs, "
              f"{len(metadata.get('outputs', {}))} outputs")
        print()
        
        # Example 1: Direct API usage
        print("Example 1: Direct API Usage")
        print("-" * 60)
        try:
            with ExcelToolAPI(workbook_path, metadata, visible=False) as api:
                # Read current inputs
                print("Reading current inputs...")
                if "span" in metadata.get("inputs", {}):
                    span = api.read_input("span")
                    print(f"  Current span: {span}")
                
                if "load" in metadata.get("inputs", {}):
                    load = api.read_input("load")
                    print(f"  Current load: {load}")
                
                # Write new inputs
                print("\nWriting new inputs...")
                if "span" in metadata.get("inputs", {}):
                    api.write_input("span", 15.0)
                    print("  ✅ Wrote span = 15.0 m")
                
                if "load" in metadata.get("inputs", {}):
                    api.write_input("load", 5.5)
                    print("  ✅ Wrote load = 5.5 kN/m")
                
                # Trigger recalculation (CRITICAL - Excel does the math!)
                print("\nTriggering Excel recalculation...")
                api.recalculate()
                print("  ✅ Recalculation complete")
                
                # Read outputs
                print("\nReading outputs from Excel...")
                if "moment" in metadata.get("outputs", {}):
                    moment = api.read_output("moment")
                    print(f"  ✅ Moment: {moment} kN⋅m")
                
                if "shear" in metadata.get("outputs", {}):
                    shear = api.read_output("shear")
                    print(f"  ✅ Shear: {shear} kN")
        
        except Exception as e:
            print(f"❌ Error in direct API usage: {e}")
            import traceback
            traceback.print_exc()
        
        print()
        
        # Example 2: Tool sequence execution
        print("Example 2: Tool Sequence Execution")
        print("-" * 60)
        
        tool_sequence = [
            {"tool": "read_input", "params": {"name": "span"}},
            {"tool": "read_input", "params": {"name": "load"}},
            {"tool": "write_input", "params": {"name": "span", "value": 12.0}},
            {"tool": "write_input", "params": {"name": "load", "value": 6.0}},
            {"tool": "recalculate", "params": {}},
            {"tool": "read_output", "params": {"name": "moment"}},
            {"tool": "read_output", "params": {"name": "shear"}}
        ]
        
        # Filter tool sequence to only include parameters that exist in metadata
        filtered_sequence = []
        for tool_call in tool_sequence:
            tool_name = tool_call["tool"]
            params = tool_call.get("params", {})
            
            if tool_name in ["read_input", "write_input"]:
                param_name = params.get("name")
                if param_name in metadata.get("inputs", {}):
                    filtered_sequence.append(tool_call)
            elif tool_name == "read_output":
                param_name = params.get("name")
                if param_name in metadata.get("outputs", {}):
                    filtered_sequence.append(tool_call)
            elif tool_name == "recalculate":
                filtered_sequence.append(tool_call)
        
        if filtered_sequence:
            print(f"Executing {len(filtered_sequence)} tool operations...")
            result = execute_tool_sequence(
                workbook_path=workbook_path,
                semantic_metadata=metadata,
                tool_sequence=filtered_sequence,
                visible=False
            )
            
            if result["success"]:
                print("✅ Tool sequence executed successfully")
                print("\nResults:")
                for tool_result in result["results"]:
                    tool_name = tool_result["tool"]
                    if tool_result["result"] is not None:
                        print(f"  {tool_name}: {tool_result['result']}")
                
                if result["outputs"]:
                    print("\nOutputs:")
                    for name, value in result["outputs"].items():
                        print(f"  {name}: {value}")
            else:
                print(f"❌ Tool sequence failed: {result['error']}")
        else:
            print("⚠️  No valid tool operations (check metadata)")
        
        print()
        print("=" * 60)
        print("Test Complete!")
        print("=" * 60)
    
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

