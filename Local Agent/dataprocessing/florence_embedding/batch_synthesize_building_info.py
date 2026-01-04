#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch processor for building synthesis on new projects
This script runs synthesize_building_info.py on projects that have structured JSON but no building_info yet.
"""

import os
import sys
from pathlib import Path

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    BASE_DIR = r"C:\Users\brian\OneDrive\Desktop\dataprocessing"
    env_path = Path(BASE_DIR) / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        # Fallback: try to find .env in current or parent directories
        load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, will use environment variables directly

# Configuration
BASE_DIR = r"C:\Users\brian\OneDrive\Desktop\dataprocessing"
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
STRUCTURED_JSON_DIR = os.path.join(BASE_DIR, "florence_embedding", "structured_json")
BUILDING_SYNTHESIS_DIR = os.path.join(BASE_DIR, "florence_embedding", "building_synthesis")

# Add the script directory to path so we can import synthesize_building_info
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

def find_projects_needing_synthesis():
    """Find projects that have structured JSON but no building_info yet"""
    structured_path = Path(STRUCTURED_JSON_DIR)
    building_synthesis_path = Path(BUILDING_SYNTHESIS_DIR)
    
    if not structured_path.exists():
        print(f"❌ Structured JSON directory not found: {structured_path}")
        return []
    
    # Find all projects with structured JSON
    projects_with_structured = []
    for project_dir in structured_path.iterdir():
        if project_dir.is_dir():
            structured_file = project_dir / f"structured_{project_dir.name}.json"
            if structured_file.exists():
                projects_with_structured.append(project_dir.name)
    
    # Check which ones already have building_info
    projects_needing_synthesis = []
    projects_already_done = []
    
    for project_id in projects_with_structured:
        building_info_file = building_synthesis_path / f"building_info_{project_id}.json"
        if building_info_file.exists():
            projects_already_done.append(project_id)
        else:
            projects_needing_synthesis.append(project_id)
    
    return sorted(projects_needing_synthesis), sorted(projects_already_done)

def run_synthesis_for_project(project_id):
    """Run the building synthesis script for a single project"""
    print(f"\n{'='*60}")
    print(f"Synthesizing building info for project: {project_id}")
    print(f"{'='*60}")
    
    original_env = None
    try:
        # Reload .env file to ensure API_KEY is available
        try:
            from dotenv import load_dotenv
            env_path = Path(BASE_DIR) / ".env"
            if env_path.exists():
                load_dotenv(env_path, override=True)
        except ImportError:
            pass
        
        # Set environment variable to override input directory
        original_env = os.environ.get("PROJECT_INPUT_DIR")
        os.environ["PROJECT_INPUT_DIR"] = OUTPUT_DIR
        
        # Import the synthesis module
        import importlib
        if 'synthesize_building_info' in sys.modules:
            importlib.reload(sys.modules['synthesize_building_info'])
        import synthesize_building_info
        
        # Initialize the client if needed
        if synthesize_building_info.client is None:
            from openai import OpenAI
            # Check API_KEY first (from .env), then OPENAI_API_KEY, then the module's API_KEY
            api_key = os.getenv("API_KEY") or os.getenv("OPENAI_API_KEY") or synthesize_building_info.API_KEY
            if not api_key or len(api_key.strip()) < 20:
                print("❌ ERROR: OpenAI API key not set or invalid!")
                print("   Set API_KEY or OPENAI_API_KEY in .env file or environment variable")
                return False
            synthesize_building_info.client = OpenAI(api_key=api_key)
        
        # Call process_project directly
        synthesize_building_info.process_project(project_id, synthesize_building_info.client)
        
        return True
            
    except Exception as e:
        print(f"❌ Error processing {project_id}: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Restore original env var
        if original_env is not None:
            os.environ["PROJECT_INPUT_DIR"] = original_env
        elif "PROJECT_INPUT_DIR" in os.environ:
            del os.environ["PROJECT_INPUT_DIR"]

def main():
    """Main entry point"""
    print("="*60)
    print("Batch Building Synthesis: New projects only")
    print("="*60)
    
    # Find projects needing synthesis
    print(f"\nChecking for projects needing building synthesis...")
    projects_to_process, projects_done = find_projects_needing_synthesis()
    
    if not projects_to_process and not projects_done:
        print(f"❌ No projects with structured JSON found in {STRUCTURED_JSON_DIR}")
        return
    
    # Display summary
    print(f"\n{'='*60}")
    print("PROJECT STATUS SUMMARY")
    print(f"{'='*60}")
    
    if projects_done:
        print(f"\n✅ ALREADY SYNTHESIZED ({len(projects_done)} projects) - Will be skipped:")
        for proj_id in projects_done[:20]:  # Show first 20
            print(f"   {proj_id}")
        if len(projects_done) > 20:
            print(f"   ... and {len(projects_done) - 20} more")
    
    if projects_to_process:
        print(f"\n🆕 NEEDS SYNTHESIS ({len(projects_to_process)} projects) - Will process:")
        for proj_id in projects_to_process[:20]:  # Show first 20
            print(f"   {proj_id}")
        if len(projects_to_process) > 20:
            print(f"   ... and {len(projects_to_process) - 20} more")
    
    print(f"\n{'='*60}")
    print(f"SUMMARY:")
    print(f"   Total projects with structured JSON: {len(projects_to_process) + len(projects_done)}")
    print(f"   Will process: {len(projects_to_process)} projects")
    print(f"   Will skip: {len(projects_done)} projects (already synthesized)")
    print(f"{'='*60}")
    
    # Ask for confirmation
    if len(projects_to_process) == 0:
        print("\n✅ All projects already have building synthesis! Nothing to process.")
        return
    
    print(f"\n⚠️  This will synthesize building info for {len(projects_to_process)} project(s).")
    response = input("Continue? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("Cancelled.")
        return
    
    # Process each project
    successful = 0
    failed = 0
    
    for project_id in projects_to_process:
        if run_synthesis_for_project(project_id):
            successful += 1
        else:
            failed += 1
    
    # Summary
    print(f"\n{'='*60}")
    print("✨ Batch Synthesis Complete!")
    print(f"   Successful: {successful}")
    print(f"   Failed: {failed}")
    print(f"   Total processed: {len(projects_to_process)}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()

