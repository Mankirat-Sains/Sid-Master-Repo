#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify JSON structure matches Supabase table structure

This script checks that:
1. All required fields are present
2. Field names match exactly
3. Data types are correct
4. Arrays are properly formatted (will be converted to comma-separated strings on upload)
5. Embeddings are exactly 1536 dimensions
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional

# ================= CONFIGURATION =================
STRUCTURED_JSON_DIR = r"C:\Users\shine\Testing-2025-01-07\Local Agent\dataprocessing\google\structured_json"
TEST_PROJECT_ID = "25-01-004"  # Test with this project first
MAX_TEST_IMAGES = 3  # Test first 3 images
# =================================================

# Expected table structure (for reference)
TABLE_STRUCTURE = {
    "id": "uuid (auto-generated)",
    "project_key": "text, not null",
    "page_num": "integer, not null",
    "region_number": "integer, null",
    "image_id": "text, not null",
    "relative_path": "text, null",
    "classification": "text, null",
    "location": "text, null",
    "level": "text, null",
    "orientation": "text, null",
    "element_type": "text, null",
    "grid_references": "text, null (comma-separated)",
    "section_callouts": "text, null (comma-separated)",
    "element_callouts": "text, null (comma-separated)",
    "key_components": "text, null (comma-separated)",
    "text_verbatim": "text, null",
    "summary": "text, null",
    "text_verbatim_embedding": "vector(1536), null",
    "summary_embedding": "vector(1536), null",
    "created_at": "timestamptz (auto-generated)",
    "updated_at": "timestamptz (auto-generated)"
}

# JSON field name to table field name mapping
FIELD_MAPPING = {
    "project_id": "project_key",
    "page_number": "page_num",
    # All other fields match directly
}

# Required fields (must not be null/empty in JSON, but can be null in DB)
REQUIRED_FIELDS = ["project_id", "page_number", "image_id"]

# Array fields that will be converted to comma-separated strings
ARRAY_FIELDS = ["grid_references", "section_callouts", "element_callouts", "key_components"]


def array_to_comma_separated(arr: List[Any]) -> Optional[str]:
    """Convert array to comma-separated string, return None if empty"""
    if not arr or len(arr) == 0:
        return None
    return ", ".join(str(item) for item in arr if item is not None)


def convert_json_to_table_row(img: Dict[str, Any]) -> Dict[str, Any]:
    """Convert JSON image object to table row format"""
    row = {
        # Map field names
        "project_key": img.get("project_id"),
        "page_num": img.get("page_number"),
        "region_number": img.get("region_number"),
        "image_id": img.get("image_id"),
        "relative_path": img.get("relative_path"),
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
        "text_verbatim_embedding": img.get("text_verbatim_embedding"),
        "summary_embedding": img.get("summary_embedding"),
    }
    
    # Remove None values for cleaner output (Supabase will use NULL)
    # But keep them for validation purposes
    return row


def validate_image(img: Dict[str, Any], index: int) -> tuple[bool, List[str]]:
    """Validate a single image object against table structure"""
    errors = []
    warnings = []
    
    # Check required fields
    for field in REQUIRED_FIELDS:
        if field not in img or img[field] is None:
            errors.append(f"Missing required field: {field}")
        elif field == "page_number" and not isinstance(img[field], int):
            errors.append(f"Field 'page_number' must be integer, got {type(img[field]).__name__}")
        elif field == "image_id" and not isinstance(img[field], str):
            errors.append(f"Field 'image_id' must be string, got {type(img[field]).__name__}")
    
    # Check page_num type
    if "page_number" in img and not isinstance(img.get("page_number"), int):
        errors.append(f"page_number must be integer, got {type(img.get('page_number')).__name__}")
    
    # Check region_number type (if present)
    if "region_number" in img and img["region_number"] is not None:
        if not isinstance(img["region_number"], int):
            errors.append(f"region_number must be integer, got {type(img['region_number']).__name__}")
    
    # Check array fields
    for field in ARRAY_FIELDS:
        if field in img:
            value = img[field]
            if value is not None and not isinstance(value, list):
                warnings.append(f"{field} should be array, got {type(value).__name__}")
    
    # Check embedding dimensions
    if "text_verbatim_embedding" in img and img["text_verbatim_embedding"] is not None:
        emb = img["text_verbatim_embedding"]
        if isinstance(emb, list):
            if len(emb) != 1536:
                errors.append(f"text_verbatim_embedding must be 1536 dimensions, got {len(emb)}")
        else:
            warnings.append(f"text_verbatim_embedding should be list, got {type(emb).__name__}")
    
    if "summary_embedding" in img and img["summary_embedding"] is not None:
        emb = img["summary_embedding"]
        if isinstance(emb, list):
            if len(emb) != 1536:
                errors.append(f"summary_embedding must be 1536 dimensions, got {len(emb)}")
        else:
            warnings.append(f"summary_embedding should be list, got {type(emb).__name__}")
    
    return len(errors) == 0, errors + warnings


def test_project(project_id: str, max_images: int = 3):
    """Test a project's JSON structure"""
    json_file = Path(STRUCTURED_JSON_DIR) / project_id / f"structured_{project_id}.json"
    
    if not json_file.exists():
        print(f"❌ JSON file not found: {json_file}")
        return False
    
    print("="*80)
    print(f"Testing Table Structure Match: {project_id}")
    print("="*80)
    print(f"JSON file: {json_file}\n")
    
    # Load JSON
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading JSON: {e}")
        return False
    
    images = data.get("images", [])
    if not images:
        print("❌ No images found in JSON")
        return False
    
    print(f"📸 Found {len(images)} images")
    print(f"🔍 Testing first {min(max_images, len(images))} images\n")
    
    # Test first few images
    test_images = images[:max_images]
    all_valid = True
    
    for i, img in enumerate(test_images, 1):
        print(f"[{i}/{len(test_images)}] Testing: {img.get('image_id', 'unknown')}")
        
        is_valid, issues = validate_image(img, i)
        
        if is_valid and not issues:
            print(f"  ✅ Valid")
        else:
            all_valid = False
            if issues:
                for issue in issues:
                    if "must be" in issue.lower() or "missing" in issue.lower():
                        print(f"  ❌ {issue}")
                    else:
                        print(f"  ⚠️  {issue}")
        
        # Show converted table row (first image only for brevity)
        if i == 1:
            print(f"\n  📋 Sample table row format:")
            row = convert_json_to_table_row(img)
            for key, value in row.items():
                if value is None:
                    print(f"    {key}: NULL")
                elif isinstance(value, list):
                    print(f"    {key}: [list with {len(value)} items]")
                elif isinstance(value, str) and len(value) > 50:
                    print(f"    {key}: {value[:50]}... (truncated)")
                else:
                    print(f"    {key}: {value}")
        
        print()
    
    print("="*80)
    if all_valid:
        print("✅ All tested images are valid!")
    else:
        print("⚠️  Some issues found. Please review above.")
    print("="*80)
    
    return all_valid


def main():
    """Main entry point"""
    test_project(TEST_PROJECT_ID, MAX_TEST_IMAGES)


if __name__ == "__main__":
    main()

