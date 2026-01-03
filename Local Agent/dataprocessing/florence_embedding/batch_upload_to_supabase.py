#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch uploader for image descriptions to Supabase
This script runs json_to_supabase.py on projects that have structured JSON but haven't been uploaded yet.
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
STRUCTURED_JSON_DIR = os.path.join(BASE_DIR, "florence_embedding", "structured_json")

# Add the script directory to path so we can import json_to_supabase
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

def check_project_upload_status(project_id, supabase_client):
    """Check how many images from a project are already in Supabase"""
    try:
        response = supabase_client.table("image_descriptions").select("id").eq("project_key", project_id).execute()
        return len(response.data) if response.data else 0
    except Exception as e:
        print(f"      ⚠️ Error checking status for {project_id}: {e}")
        return -1  # Error status

def find_projects_needing_upload():
    """Find projects that have structured JSON and check their upload status"""
    structured_path = Path(STRUCTURED_JSON_DIR)
    
    if not structured_path.exists():
        print(f"❌ Structured JSON directory not found: {structured_path}")
        return [], []
    
    # Find all projects with structured JSON
    projects_with_structured = []
    for project_dir in structured_path.iterdir():
        if project_dir.is_dir():
            structured_file = project_dir / f"structured_{project_dir.name}.json"
            if structured_file.exists():
                projects_with_structured.append(project_dir.name)
    
    return sorted(projects_with_structured)

def count_images_in_json(project_id):
    """Count how many images are in the structured JSON file"""
    import json
    json_file = Path(STRUCTURED_JSON_DIR) / project_id / f"structured_{project_id}.json"
    
    if not json_file.exists():
        return 0
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return len(data.get("images", []))
    except Exception:
        return 0


def main():
    """Main entry point"""
    print("="*60)
    print("Batch Upload: Image Descriptions to Supabase")
    print("="*60)
    
    # Find projects with structured JSON
    print(f"\nFinding projects with structured JSON...")
    projects = find_projects_needing_upload()
    
    if not projects:
        print(f"❌ No projects with structured JSON found in {STRUCTURED_JSON_DIR}")
        return
    
    # Initialize Supabase client to check status
    print(f"\nChecking upload status for {len(projects)} projects...")
    try:
        from dotenv import load_dotenv
        from supabase import create_client
        
        env_path = Path(BASE_DIR) / ".env"
        if env_path.exists():
            load_dotenv(env_path, override=True)
        
        SUPABASE_URL = os.getenv("SUPABASE_URL", "https://nxrhvostwdtixojqyvro.supabase.co")
        SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
        
        if not SUPABASE_KEY:
            print("❌ SUPABASE_KEY not set in .env file!")
            return
        
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"❌ Error initializing Supabase client: {e}")
        print("   Will proceed without status check...")
        supabase_client = None
    
    # Check status of all projects
    projects_to_upload = []
    projects_complete = []
    projects_partial = []
    projects_error = []
    
    for project_id in projects:
        json_count = count_images_in_json(project_id)
        
        if supabase_client:
            uploaded_count = check_project_upload_status(project_id, supabase_client)
            
            if uploaded_count == -1:
                projects_error.append((project_id, json_count, 0))
            elif uploaded_count == 0:
                projects_to_upload.append((project_id, json_count, 0))
            elif uploaded_count >= json_count:
                projects_complete.append((project_id, json_count, uploaded_count))
            else:
                projects_partial.append((project_id, json_count, uploaded_count))
        else:
            # Can't check status, assume all need upload
            projects_to_upload.append((project_id, json_count, 0))
    
    # Display summary
    print(f"\n{'='*60}")
    print("PROJECT STATUS SUMMARY")
    print(f"{'='*60}")
    
    if projects_complete:
        print(f"\n✅ COMPLETE ({len(projects_complete)} projects) - All images uploaded:")
        for proj_id, json_count, uploaded_count in projects_complete[:10]:
            print(f"   {proj_id}: {uploaded_count}/{json_count} images")
        if len(projects_complete) > 10:
            print(f"   ... and {len(projects_complete) - 10} more")
    
    if projects_partial:
        print(f"\n🔄 PARTIAL ({len(projects_partial)} projects) - Some images uploaded:")
        for proj_id, json_count, uploaded_count in projects_partial[:10]:
            print(f"   {proj_id}: {uploaded_count}/{json_count} images (will upload {json_count - uploaded_count} remaining)")
        if len(projects_partial) > 10:
            print(f"   ... and {len(projects_partial) - 10} more")
    
    if projects_to_upload:
        print(f"\n🆕 NEW ({len(projects_to_upload)} projects) - No images uploaded yet:")
        for proj_id, json_count, uploaded_count in projects_to_upload[:10]:
            print(f"   {proj_id}: 0/{json_count} images")
        if len(projects_to_upload) > 10:
            print(f"   ... and {len(projects_to_upload) - 10} more")
    
    if projects_error:
        print(f"\n⚠️  ERROR ({len(projects_error)} projects) - Could not check status:")
        for proj_id, json_count, uploaded_count in projects_error:
            print(f"   {proj_id}")
    
    # Calculate what will actually be processed
    will_process = len(projects_to_upload) + len(projects_partial)
    will_skip = len(projects_complete)
    
    print(f"\n{'='*60}")
    print(f"SUMMARY:")
    print(f"   Total projects with structured JSON: {len(projects)}")
    print(f"   Will process: {will_process} projects")
    print(f"   Will skip: {will_skip} projects (already complete)")
    print(f"{'='*60}")
    
    # Ask for confirmation
    if will_process == 0:
        print("\n✅ All projects already uploaded! Nothing to process.")
        return
    
    print(f"\n⚠️  This will upload image descriptions for {will_process} project(s).")
    print(f"   (Duplicate detection is enabled - only new images will be uploaded)")
    response = input("Continue? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("Cancelled.")
        return
    
    # Process each project
    successful = 0
    failed = 0
    total_uploaded = 0
    
    # Combine projects to process
    projects_to_process = [p[0] for p in projects_to_upload + projects_partial]
    
    for project_id in projects_to_process:
        try:
            # Import and initialize
            import json_to_supabase
            import importlib
            importlib.reload(json_to_supabase)
            
            # Initialize clients if needed
            if json_to_supabase.openai_client is None or json_to_supabase.supabase is None:
                json_to_supabase.init_clients()
            
            # Process project and get count
            count = json_to_supabase.process_project(project_id, skip_existing=True)
            if count >= 0:  # Success (even if 0 new records)
                successful += 1
                total_uploaded += count
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Error processing {project_id}: {e}")
            failed += 1
    
    # Summary
    print(f"\n{'='*60}")
    print("✨ Batch Upload Complete!")
    print(f"   Successful: {successful}")
    print(f"   Failed: {failed}")
    print(f"   Total records uploaded: {total_uploaded}")
    print(f"   Total projects processed: {len(projects_to_process)}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()

