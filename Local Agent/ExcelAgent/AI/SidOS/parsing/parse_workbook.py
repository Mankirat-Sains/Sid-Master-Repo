#!/usr/bin/env python3
# Always use -B flag to avoid bytecode hangs with Python 3.13
# This script should be run with: python -B parse_workbook.py
"""
Quick Script to Parse Excel Workbook

This is a convenience script that:
1. Parses an Excel workbook using the intelligent parser
2. Converts output to local agent format
3. Saves metadata ready for use

Usage:
    python parse_workbook.py "workbook.xlsx"
    python parse_workbook.py "workbook.xlsx" -o "custom_metadata.json"
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from parsing import IntelligentExcelParser, convert_to_local_agent_format


def main():
    parser = argparse.ArgumentParser(
        description="Parse Excel workbook and generate semantic metadata"
    )
    parser.add_argument("workbook", type=Path, help="Path to Excel workbook")
    parser.add_argument("-o", "--output", type=Path, help="Output path for metadata")
    parser.add_argument("--flatten", action="store_true", default=True,
                       help="Flatten groups to individual cells (default: True)")
    parser.add_argument("--api-key", type=str, help="OpenAI API key")
    
    args = parser.parse_args()
    
    if not args.workbook.exists():
        print(f"❌ Workbook not found: {args.workbook}")
        sys.exit(1)
    
    # Set API key if provided
    if args.api_key:
        import os
        os.environ["OPENAI_API_KEY"] = args.api_key
    
    print("=" * 60)
    print("Intelligent Excel Parser")
    print("=" * 60)
    print(f"Workbook: {args.workbook}")
    print()
    
    try:
        # Create parser
        excel_parser = IntelligentExcelParser()
        
        # Parse workbook
        parser_output_path = args.output or (args.workbook.parent / f"{args.workbook.stem}_parser_output.json")
        metadata = excel_parser.parse_workbook(args.workbook, parser_output_path)
        
        # Convert to local agent format
        agent_metadata_path = args.output or (args.workbook.parent / f"{args.workbook.stem}_metadata.json")
        agent_metadata = convert_to_local_agent_format(metadata, flatten_groups=args.flatten)
        
        # Save agent metadata
        agent_metadata_path = Path(agent_metadata_path)
        agent_metadata_path.parent.mkdir(parents=True, exist_ok=True)
        
        import json
        with open(agent_metadata_path, 'w', encoding='utf-8') as f:
            json.dump(agent_metadata, f, indent=2, ensure_ascii=False)
        
        print()
        print("=" * 60)
        print("✅ Parsing Complete!")
        print("=" * 60)
        print(f"Parser output: {parser_output_path}")
        print(f"Agent metadata: {agent_metadata_path}")
        print()
        print(f"Input groups: {len(agent_metadata.get('inputs', {}))}")
        print(f"Output groups: {len(agent_metadata.get('outputs', {}))}")
        print()
        print("You can now use this metadata with the local agent:")
        print(f'  python test_local_agent.py "{args.workbook}" "{agent_metadata_path}"')
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

