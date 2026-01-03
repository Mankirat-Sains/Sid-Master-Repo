#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch processor for all projects starting with "25-01"
This script runs extract_structured_info.py on all matching projects in the output directory.
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

# Configuration - override the input directory
BASE_DIR = r"C:\Users\brian\OneDrive\Desktop\dataprocessing"
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# Add the script directory to path so we can import extract_structured_info
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

def find_25_01_projects():
    """Find all project directories starting with '25-01' in the output directory"""
    output_path = Path(OUTPUT_DIR)
    if not output_path.exists():
        print(f"❌ Output directory not found: {OUTPUT_DIR}")
        return []
    
    projects = []
    for item in output_path.iterdir():
        if item.is_dir() and item.name.startswith("25-01"):
            projects.append(item.name)
    
    return sorted(projects)

def check_project_status(project_id):
    """Check the processing status of a project"""
    import json
    
    project_dir = Path(OUTPUT_DIR) / project_id
    output_dir = Path(BASE_DIR) / "florence_embedding" / "structured_json" / project_id
    output_file = output_dir / f"structured_{project_id}.json"
    
    if not project_dir.exists():
        return "missing", 0, 0
    
    # Find all region images (same logic as extract_structured_info.py)
    region_images = []
    for page_dir in sorted(project_dir.glob("page_*")):
        if page_dir.is_dir():
            for img_path in sorted(page_dir.glob("region_*_red_box.png")):
                region_images.append(img_path.name)
    
    total_images = len(region_images)
    
    if total_images == 0:
        return "no_images", 0, 0
    
    if not output_file.exists():
        return "new", 0, total_images
    
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
            processed_count = len(existing_data.get("images", []))
        
        if processed_count == 0:
            return "new", 0, total_images
        elif processed_count >= total_images:
            return "complete", processed_count, total_images
        else:
            return "partial", processed_count, total_images
    except Exception:
        return "error", 0, total_images

def run_extraction_for_project(project_id):
    """Run the extraction script for a single project"""
    print(f"\n{'='*60}")
    print(f"Processing project: {project_id}")
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
        
        # Reload the module to pick up the new environment variable
        import importlib
        if 'extract_structured_info' in sys.modules:
            importlib.reload(sys.modules['extract_structured_info'])
        import extract_structured_info
        
        # Initialize the client if needed
        if extract_structured_info.client is None:
            from openai import OpenAI
            # Check API_KEY first (from .env), then OPENAI_API_KEY, then the module's API_KEY
            api_key = os.getenv("API_KEY") or os.getenv("OPENAI_API_KEY") or extract_structured_info.API_KEY
            if not api_key or len(api_key.strip()) < 20:
                print("❌ ERROR: OpenAI API key not set or invalid!")
                print("   Set API_KEY or OPENAI_API_KEY in .env file or environment variable")
                return False
            extract_structured_info.client = OpenAI(api_key=api_key)
        
        # Call process_project directly
        extract_structured_info.process_project(project_id)
        
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
    print("Batch Processing: All projects starting with '25-01'")
    print("="*60)
    
    # Find all matching projects
    projects = find_25_01_projects()
    
    if not projects:
        print(f"❌ No projects starting with '25-01' found in {OUTPUT_DIR}")
        return
    
    # Check status of all projects
    print(f"\nChecking status of {len(projects)} projects...")
    complete_projects = []
    partial_projects = []
    new_projects = []
    error_projects = []
    no_image_projects = []
    
    for project_id in projects:
        status, processed, total = check_project_status(project_id)
        if status == "complete":
            complete_projects.append((project_id, processed, total))
        elif status == "partial":
            partial_projects.append((project_id, processed, total))
        elif status == "new":
            new_projects.append((project_id, processed, total))
        elif status == "no_images":
            no_image_projects.append((project_id, processed, total))
        else:
            error_projects.append((project_id, processed, total))
    
    # Display summary
    print(f"\n{'='*60}")
    print("PROJECT STATUS SUMMARY")
    print(f"{'='*60}")
    
    if complete_projects:
        print(f"\n✅ COMPLETE ({len(complete_projects)} projects) - Will be skipped:")
        for proj_id, proc, tot in complete_projects[:10]:  # Show first 10
            print(f"   {proj_id}: {proc}/{tot} images")
        if len(complete_projects) > 10:
            print(f"   ... and {len(complete_projects) - 10} more")
    
    if partial_projects:
        print(f"\n🔄 PARTIAL ({len(partial_projects)} projects) - Will resume:")
        for proj_id, proc, tot in partial_projects[:10]:  # Show first 10
            print(f"   {proj_id}: {proc}/{tot} images (will process {tot - proc} remaining)")
        if len(partial_projects) > 10:
            print(f"   ... and {len(partial_projects) - 10} more")
    
    if new_projects:
        print(f"\n🆕 NEW ({len(new_projects)} projects) - Will start from scratch:")
        for proj_id, proc, tot in new_projects[:10]:  # Show first 10
            print(f"   {proj_id}: 0/{tot} images")
        if len(new_projects) > 10:
            print(f"   ... and {len(new_projects) - 10} more")
    
    if no_image_projects:
        print(f"\n⚠️  NO IMAGES ({len(no_image_projects)} projects) - No region images found:")
        for proj_id, proc, tot in no_image_projects[:5]:
            print(f"   {proj_id}")
        if len(no_image_projects) > 5:
            print(f"   ... and {len(no_image_projects) - 5} more")
    
    if error_projects:
        print(f"\n⚠️  ERROR ({len(error_projects)} projects) - May need attention:")
        for proj_id, proc, tot in error_projects:
            print(f"   {proj_id}")
    
    # Calculate what will actually be processed
    will_process = len(partial_projects) + len(new_projects) + len(error_projects)
    will_skip = len(complete_projects) + len(no_image_projects)
    
    print(f"\n{'='*60}")
    print(f"SUMMARY:")
    print(f"   Total projects: {len(projects)}")
    print(f"   Will process: {will_process} projects")
    print(f"   Will skip: {will_skip} projects (already complete)")
    print(f"{'='*60}")
    
    # Ask for confirmation
    if will_process == 0:
        print("\n✅ All projects are already complete! Nothing to process.")
        return
    
    print(f"\n⚠️  This will process {will_process} project(s).")
    response = input("Continue? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("Cancelled.")
        return
    
    # Process each project
    successful = 0
    failed = 0
    
    for project_id in projects:
        if run_extraction_for_project(project_id):
            successful += 1
        else:
            failed += 1
    
    # Summary
    print(f"\n{'='*60}")
    print("✨ Batch Processing Complete!")
    print(f"   Successful: {successful}")
    print(f"   Failed: {failed}")
    print(f"   Total: {len(projects)}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()

