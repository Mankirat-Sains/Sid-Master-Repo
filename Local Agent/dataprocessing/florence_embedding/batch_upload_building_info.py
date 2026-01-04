#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch uploader for building info to Supabase
This script runs upload_project_descriptions_to_supabase.py on new building_info JSON files.
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
BUILDING_SYNTHESIS_DIR = os.path.join(BASE_DIR, "florence_embedding", "building_synthesis")

# Add the script directory to path so we can import upload_project_descriptions_to_supabase
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

def check_project_in_supabase(project_id, supabase_client):
    """Check if a project already exists in Supabase"""
    try:
        response = supabase_client.table("project_description").select("project_id").eq("project_id", project_id).execute()
        return len(response.data) > 0 if response.data else False
    except Exception as e:
        print(f"      ⚠️ Error checking status for {project_id}: {e}")
        return None  # Unknown status

def find_projects_needing_upload():
    """Find building_info JSON files and check their upload status"""
    synthesis_path = Path(BUILDING_SYNTHESIS_DIR)
    
    if not synthesis_path.exists():
        print(f"❌ Building synthesis directory not found: {synthesis_path}")
        return [], []
    
    # Find all building_info JSON files
    json_files = sorted(synthesis_path.glob("building_info_*.json"))
    
    projects_with_files = []
    for json_file in json_files:
        # Extract project_id from filename (building_info_25-01-001.json -> 25-01-001)
        project_id = json_file.stem.replace("building_info_", "")
        projects_with_files.append((project_id, json_file))
    
    return projects_with_files

def main():
    """Main entry point"""
    print("="*60)
    print("Batch Upload: Building Info to Supabase")
    print("="*60)
    
    # Find projects with building_info files
    print(f"\nFinding building_info JSON files...")
    projects_with_files = find_projects_needing_upload()
    
    if not projects_with_files:
        print(f"❌ No building_info JSON files found in {BUILDING_SYNTHESIS_DIR}")
        return
    
    # Initialize Supabase client to check status
    print(f"\nChecking upload status for {len(projects_with_files)} projects...")
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
    projects_already_uploaded = []
    projects_error = []
    
    for project_id, json_file in projects_with_files:
        if supabase_client:
            exists = check_project_in_supabase(project_id, supabase_client)
            
            if exists is None:
                projects_error.append((project_id, json_file))
            elif exists:
                projects_already_uploaded.append((project_id, json_file))
            else:
                projects_to_upload.append((project_id, json_file))
        else:
            # Can't check status, assume all need upload
            projects_to_upload.append((project_id, json_file))
    
    # Display summary
    print(f"\n{'='*60}")
    print("PROJECT STATUS SUMMARY")
    print(f"{'='*60}")
    
    if projects_already_uploaded:
        print(f"\n✅ ALREADY UPLOADED ({len(projects_already_uploaded)} projects) - Will be skipped:")
        for proj_id, json_file in projects_already_uploaded[:20]:
            print(f"   {proj_id}")
        if len(projects_already_uploaded) > 20:
            print(f"   ... and {len(projects_already_uploaded) - 20} more")
    
    if projects_to_upload:
        print(f"\n🆕 NEW ({len(projects_to_upload)} projects) - Will upload:")
        for proj_id, json_file in projects_to_upload[:20]:
            print(f"   {proj_id}")
        if len(projects_to_upload) > 20:
            print(f"   ... and {len(projects_to_upload) - 20} more")
    
    if projects_error:
        print(f"\n⚠️  ERROR ({len(projects_error)} projects) - Could not check status:")
        for proj_id, json_file in projects_error:
            print(f"   {proj_id}")
    
    # Calculate what will actually be processed
    will_process = len(projects_to_upload)
    will_skip = len(projects_already_uploaded)
    
    print(f"\n{'='*60}")
    print(f"SUMMARY:")
    print(f"   Total projects with building_info: {len(projects_with_files)}")
    print(f"   Will upload: {will_process} projects")
    print(f"   Will skip: {will_skip} projects (already uploaded)")
    print(f"{'='*60}")
    
    # Ask for confirmation
    if will_process == 0:
        print("\n✅ All projects already uploaded! Nothing to process.")
        return
    
    print(f"\n⚠️  This will upload building info for {will_process} project(s).")
    print(f"   (Existing projects will be updated if they already exist)")
    response = input("Continue? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("Cancelled.")
        return
    
    # Import and initialize the upload module
    try:
        import upload_project_descriptions_to_supabase
        import importlib
        importlib.reload(upload_project_descriptions_to_supabase)
        
        # Initialize clients
        upload_project_descriptions_to_supabase.init_clients()
    except Exception as e:
        print(f"❌ Error initializing upload module: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Process each project
    successful = 0
    failed = 0
    
    for project_id, json_file in projects_to_upload:
        print(f"\n--- Processing: {json_file.name} ---")
        
        try:
            # Load JSON data
            data = upload_project_descriptions_to_supabase.load_building_synthesis_json(json_file)
            if not data:
                failed += 1
                continue
            
            print(f"   Project ID: {project_id}")
            
            # Prepare record
            record = upload_project_descriptions_to_supabase.prepare_record(data)
            
            # Upload to Supabase
            if upload_project_descriptions_to_supabase.upload_project_description(record):
                successful += 1
            else:
                failed += 1
            
            # Small delay to avoid rate limiting
            import time
            time.sleep(0.5)
            
        except Exception as e:
            print(f"❌ Error processing {project_id}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    # Summary
    print(f"\n{'='*60}")
    print("✨ Batch Upload Complete!")
    print(f"   Successful: {successful}")
    print(f"   Failed: {failed}")
    print(f"   Total processed: {len(projects_to_upload)}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()




