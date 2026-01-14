#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Upload Structured JSON to Supabase test_google_embeddings_table

This script:
1. Reads structured JSON files (with embeddings already generated)
2. Converts arrays to comma-separated strings
3. Maps field names (project_id -> project_key, page_number -> page_num)
4. Uploads to test_google_embeddings_table in Supabase
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from supabase import create_client, Client
import time

# Load environment variables
try:
    from dotenv import load_dotenv
    BASE_DIR = Path(r"C:\Users\shine\Testing-2025-01-07\Local Agent\dataprocessing")
    env_path = BASE_DIR / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

# ================= CONFIGURATION =================
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://nxrhvostwdtixojqyvro.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")  # Your Supabase service role key
STRUCTURED_JSON_DIR = r"C:\Users\shine\Testing-2025-01-07\Local Agent\dataprocessing\google\structured_json"
TABLE_NAME = "test_google_embeddings_table"  # Test table name
BATCH_SIZE = 50  # Insert records in batches
# =================================================

# Initialize Supabase client
supabase: Optional[Client] = None


def init_supabase():
    """Initialize Supabase client"""
    global supabase
    
    if not SUPABASE_KEY:
        raise ValueError("SUPABASE_KEY not set! Set it in .env file or environment variable.")
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Supabase client initialized")


def array_to_comma_separated(arr: List[Any]) -> Optional[str]:
    """Convert array to comma-separated string, return None if empty"""
    if not arr or len(arr) == 0:
        return None
    return ", ".join(str(item) for item in arr if item is not None)


def convert_json_to_table_row(img: Dict[str, Any]) -> Dict[str, Any]:
    """Convert JSON image object to table row format"""
    row = {
        # Map field names: project_id -> project_key, page_number -> page_num
        "project_key": img.get("project_id"),
        "page_num": img.get("page_number"),  # Should be integer
        "region_number": img.get("region_number"),  # Should be integer or null
        "image_id": img.get("image_id"),  # Full filename like "region_01_red_box.png"
        "relative_path": None,  # User said this can be empty
        "classification": img.get("classification"),
        "location": img.get("location"),
        "level": img.get("level"),
        "orientation": img.get("orientation"),
        "element_type": img.get("element_type"),
        # Convert arrays to comma-separated strings
        "grid_references": array_to_comma_separated(img.get("grid_references", [])),
        "section_callouts": array_to_comma_separated(img.get("section_callouts", [])),
        "element_callouts": array_to_comma_separated(img.get("element_callouts", [])),
        "key_components": array_to_comma_separated(img.get("key_components", [])),
        "text_verbatim": img.get("text_verbatim"),
        "summary": img.get("summary"),
        # Embeddings should already be 1536 dimensions
        "text_verbatim_embedding": img.get("text_verbatim_embedding"),
        "summary_embedding": img.get("summary_embedding"),
    }
    
    # Remove None values (Supabase will use NULL for missing fields)
    # But keep empty strings and empty arrays (they'll be converted to None above)
    cleaned_row = {}
    for k, v in row.items():
        if v is not None:
            cleaned_row[k] = v
    
    return cleaned_row


def validate_row(row: Dict[str, Any]) -> tuple[bool, List[str]]:
    """Validate row before inserting"""
    errors = []
    
    # Check required fields
    if not row.get("project_key"):
        errors.append("Missing required field: project_key")
    if row.get("page_num") is None:
        errors.append("Missing required field: page_num (must be integer)")
    elif not isinstance(row["page_num"], int):
        errors.append(f"page_num must be integer, got {type(row['page_num']).__name__}")
    if not row.get("image_id"):
        errors.append("Missing required field: image_id")
    
    # Check region_number is integer if present
    if "region_number" in row and row["region_number"] is not None:
        if not isinstance(row["region_number"], int):
            errors.append(f"region_number must be integer, got {type(row['region_number']).__name__}")
    
    # Check embedding dimensions (if present)
    if "text_verbatim_embedding" in row and row["text_verbatim_embedding"] is not None:
        emb = row["text_verbatim_embedding"]
        if isinstance(emb, list):
            if len(emb) != 1536:
                errors.append(f"text_verbatim_embedding must be 1536 dimensions, got {len(emb)}")
        else:
            errors.append(f"text_verbatim_embedding must be list, got {type(emb).__name__}")
    
    if "summary_embedding" in row and row["summary_embedding"] is not None:
        emb = row["summary_embedding"]
        if isinstance(emb, list):
            if len(emb) != 1536:
                errors.append(f"summary_embedding must be 1536 dimensions, got {len(emb)}")
        else:
            errors.append(f"summary_embedding must be list, got {type(emb).__name__}")
    
    return len(errors) == 0, errors


def process_project(project_id: str, skip_existing: bool = True) -> int:
    """Process a single project and return number of records uploaded"""
    print(f"\n--- Processing Project: {project_id} ---")
    
    # Load structured JSON
    json_file = Path(STRUCTURED_JSON_DIR) / project_id / f"structured_{project_id}.json"
    
    if not json_file.exists():
        print(f"❌ JSON file not found: {json_file}")
        return 0
    
    print(f"📂 Loading: {json_file}")
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading JSON: {e}")
        return 0
    
    images = data.get("images", [])
    if not images:
        print(f"⚠️ No images found in JSON")
        return 0
    
    print(f"📸 Found {len(images)} images")
    
    # Check existing records if skip_existing is True
    existing_keys = set()
    if skip_existing:
        try:
            response = supabase.table(TABLE_NAME).select("project_key,image_id").eq("project_key", project_id).execute()
            if response.data:
                existing_keys = {(r["project_key"], r["image_id"]) for r in response.data}
            print(f"📊 Found {len(existing_keys)} existing records (will skip)")
        except Exception as e:
            print(f"⚠️ Could not check existing records: {e}")
            existing_keys = set()
    
    # Convert and filter images
    rows_to_insert = []
    skipped = 0
    errors = 0
    
    for img in images:
        # Check if already exists
        project_key = img.get("project_id")
        image_id = img.get("image_id")
        
        if skip_existing and (project_key, image_id) in existing_keys:
            skipped += 1
            continue
        
        # Convert to table row format
        row = convert_json_to_table_row(img)
        
        # Validate row
        is_valid, validation_errors = validate_row(row)
        if not is_valid:
            print(f"  ⚠️ Validation failed for {image_id}: {', '.join(validation_errors)}")
            errors += 1
            continue
        
        rows_to_insert.append(row)
    
    if not rows_to_insert:
        print(f"✅ All images already processed (skipped: {skipped})")
        return 0
    
    print(f"⚙️ Preparing to insert {len(rows_to_insert)} new records (skipped: {skipped}, errors: {errors})")
    
    # Insert in batches
    inserted = 0
    failed = 0
    
    for i in range(0, len(rows_to_insert), BATCH_SIZE):
        batch = rows_to_insert[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        total_batches = (len(rows_to_insert) + BATCH_SIZE - 1) // BATCH_SIZE
        
        print(f"  📤 Inserting batch {batch_num}/{total_batches} ({len(batch)} records)...")
        
        try:
            response = supabase.table(TABLE_NAME).insert(batch).execute()
            inserted += len(batch)
            print(f"     ✅ Inserted {len(batch)} records")
        except Exception as e:
            print(f"     ❌ Error inserting batch: {e}")
            failed += len(batch)
            # Try inserting one by one to find problematic records
            for row in batch:
                try:
                    supabase.table(TABLE_NAME).insert(row).execute()
                    inserted += 1
                    failed -= 1
                except Exception as e2:
                    print(f"       ❌ Failed to insert {row.get('image_id')}: {e2}")
        
        # Small delay between batches
        if i + BATCH_SIZE < len(rows_to_insert):
            time.sleep(0.5)
    
    print(f"✅ Complete! Inserted: {inserted}, Failed: {failed}, Skipped: {skipped}")
    return inserted


def main():
    """Main entry point"""
    print("="*80)
    print("Upload to Supabase: test_google_embeddings_table")
    print("="*80)
    
    # Initialize Supabase
    try:
        init_supabase()
    except Exception as e:
        print(f"❌ Failed to initialize Supabase: {e}")
        return
    
    # Find all projects
    structured_path = Path(STRUCTURED_JSON_DIR)
    if not structured_path.exists():
        print(f"❌ Structured JSON directory not found: {structured_path}")
        return
    
    projects = []
    for project_dir in structured_path.iterdir():
        if project_dir.is_dir():
            json_file = project_dir / f"structured_{project_dir.name}.json"
            if json_file.exists():
                projects.append(project_dir.name)
    
    if not projects:
        print(f"❌ No projects found in {structured_path}")
        return
    
    projects = sorted(projects)
    print(f"📁 Found {len(projects)} project(s): {', '.join(projects)}")
    print()
    
    # Check if project ID provided as argument
    import sys
    if len(sys.argv) > 1:
        project_id = sys.argv[1]
        if project_id not in projects:
            print(f"❌ Project {project_id} not found!")
            return
        projects = [project_id]
    
    # Process each project
    total_inserted = 0
    successful = 0
    failed = 0
    
    for project_id in projects:
        try:
            count = process_project(project_id, skip_existing=True)
            if count >= 0:
                successful += 1
                total_inserted += count
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Error processing {project_id}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*80)
    print("✨ Upload Complete!")
    print(f"   Successful: {successful}")
    print(f"   Failed: {failed}")
    print(f"   Total records inserted: {total_inserted}")
    print("="*80)


if __name__ == "__main__":
    main()

