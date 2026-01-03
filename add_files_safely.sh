#!/bin/bash
# Script to add files while skipping corrupted ones

cd "$(dirname "$0")"

echo "Adding files safely, skipping corrupted ones..."

# Add .gitignore first
git add .gitignore 2>/dev/null

# Function to add files from a directory, skipping errors
add_directory() {
    local dir=$1
    echo "Processing $dir..."
    
    # Find all files and add them one by one, skipping errors
    find "$dir" -type f ! -path "*/.git/*" ! -path "*/node_modules/*" ! -path "*/venv/*" ! -path "*/venv_backup/*" ! -path "*/venv_xlwings/*" ! -path "*/.DS_Store" 2>/dev/null | while read -r file; do
        git add "$file" 2>/dev/null || true
    done
}

# Add directories
add_directory "sandbox-JH"
add_directory "superceded_JH"  
add_directory "localagent-JH"

echo "Done! Check git status to see what was added."

