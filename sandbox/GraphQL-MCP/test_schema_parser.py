#!/usr/bin/env python3
"""
Test script to run schema_parser.py on raw_schema.graphql
"""

import sys
from pathlib import Path

# Import the schema parser
sys.path.insert(0, str(Path(__file__).parent))
from schema_parser import parse_schema_summary, format_schema_for_llm

def test_with_real_schema():
    """Test the parser with the actual raw_schema.graphql file"""
    
    schema_path = Path(__file__).parent / "raw_schema.graphql"
    
    if not schema_path.exists():
        print(f"❌ Schema file not found: {schema_path}")
        return
    
    print(f"📖 Reading schema from: {schema_path}")
    print(f"📊 File size: {schema_path.stat().st_size:,} bytes")
    print()
    
    # Read the schema
    with open(schema_path, 'r') as f:
        schema_text = f.read()
    
    print(f"✅ Read {len(schema_text):,} characters")
    print()
    
    # Parse it
    print("🔍 Parsing schema...")
    summary = parse_schema_summary(schema_text)
    
    print(f"✅ Found {len(summary.get('queries', []))} queries")
    print()
    
    # Show first few queries
    print("=" * 80)
    print("FIRST 10 QUERIES FOUND:")
    print("=" * 80)
    for i, query in enumerate(summary.get('queries', [])[:10], 1):
        print(f"\n{i}. {query['name']}")
        print(f"   Returns: {query.get('return_type', 'Unknown')}")
        if query.get('arguments'):
            print(f"   Arguments:")
            for arg in query['arguments']:
                req = " (required)" if arg.get('required') else " (optional)"
                print(f"     - {arg['name']}: {arg['type']}{req}")
    
    print("\n" + "=" * 80)
    print("EXAMPLE QUERIES GENERATED:")
    print("=" * 80)
    for i, example in enumerate(summary.get('query_examples', [])[:5], 1):
        print(f"\n{i}. {example}")
    
    print("\n" + "=" * 80)
    print("FORMATTED OUTPUT FOR LLM (first 2000 chars):")
    print("=" * 80)
    formatted = format_schema_for_llm(summary)
    # Print first 2000 chars to avoid overwhelming output
    print(formatted[:2000])
    if len(formatted) > 2000:
        print(f"\n... (truncated, total length: {len(formatted):,} chars)")
    
    # Save full output to file
    output_path = Path(__file__).parent / "schema_analysis_output.txt"
    with open(output_path, 'w') as f:
        f.write(formatted)
    print(f"\n✅ Full output saved to: {output_path}")
    
    # Also save raw summary as JSON for inspection
    import json
    json_path = Path(__file__).parent / "schema_summary.json"
    with open(json_path, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"✅ Raw summary saved to: {json_path}")

if __name__ == "__main__":
    test_with_real_schema()


