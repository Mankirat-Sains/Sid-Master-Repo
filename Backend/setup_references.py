#!/usr/bin/env python3
"""
Helper script to copy reference documents from original Backend folder
to the references/ folder for client customization.
"""
from pathlib import Path
import shutil

# Get paths
BACKEND_NEW_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_NEW_DIR.parent
ORIGINAL_BACKEND = PROJECT_ROOT / "Backend"
REFERENCES_DIR = BACKEND_NEW_DIR / "references"

# Files to copy
REFERENCE_FILES = [
    "planner_playbook.md",
    "project_categories.md"
]

def setup_references():
    """Copy reference files from original Backend to references folder"""
    print("📋 Setting up reference documents...")
    print(f"   Source: {ORIGINAL_BACKEND}")
    print(f"   Destination: {REFERENCES_DIR}")
    print()
    
    # Create references directory if it doesn't exist
    REFERENCES_DIR.mkdir(exist_ok=True)
    
    copied = []
    skipped = []
    missing = []
    
    for filename in REFERENCE_FILES:
        source = ORIGINAL_BACKEND / filename
        dest = REFERENCES_DIR / filename
        
        if not source.exists():
            missing.append(filename)
            print(f"⚠️  {filename} not found in {ORIGINAL_BACKEND}")
            continue
        
        if dest.exists():
            skipped.append(filename)
            print(f"⏭️  {filename} already exists in references/ (skipping)")
        else:
            shutil.copy2(source, dest)
            copied.append(filename)
            print(f"✅ Copied {filename}")
    
    print()
    print("=" * 60)
    print("Summary:")
    print(f"  ✅ Copied: {len(copied)} files")
    print(f"  ⏭️  Skipped: {len(skipped)} files (already exist)")
    print(f"  ⚠️  Missing: {len(missing)} files")
    print()
    
    if copied:
        print("📝 Next steps:")
        print("   1. Review and customize the files in references/")
        print("   2. Edit planner_playbook.md for client-specific planning")
        print("   3. Edit project_categories.md for client-specific categories")
    elif missing:
        print("⚠️  Some reference files are missing.")
        print("   You may need to create them manually or copy from another location.")
    
    print()
    print(f"📁 Reference files location: {REFERENCES_DIR}")

if __name__ == "__main__":
    setup_references()

