# Testing Guide for Cache Generator

## Step 1: Install Dependencies

Navigate to the caching directory and install requirements:

```bash
cd "/Volumes/J/Sid-Master-Repo/Local Agent/ExcelAgent/caching"
pip install -r requirements.txt
```

Or install individually:
```bash
pip install openai python-docx openpyxl google-cloud-vision python-dotenv
```

## Step 2: Set Up Environment Variables

You need to set your OpenAI API key. You can do this in several ways:

### Option A: Environment Variable (Recommended)
```bash
export OPENAI_API_KEY="sk-your-api-key-here"
```

### Option B: .env File
Create a `.env` file in the project root or caching directory:
```
OPENAI_API_KEY=sk-your-api-key-here
GOOGLE_OCR_KEY_PATH=/path/to/your/google-ocr-key.json
```

### Option C: Set in Terminal Before Running
```bash
OPENAI_API_KEY="sk-your-api-key-here" python cache_generator.py /path/to/folder
```

## Step 3: Prepare a Test Folder

Create or use a test folder with sample files:
- At least one PDF file (for OCR testing)
- At least one Word document (.docx)
- At least one Excel file (.xlsx)

Example test folder structure:
```
test_project/
├── document.pdf
├── report.docx
└── calculations.xlsx
```

## Step 4: Run the Script

### Basic Test
```bash
cd "/Volumes/J/Sid-Master-Repo/Local Agent/ExcelAgent/caching"
python cache_generator.py "/path/to/your/test/folder"
```

### Example with actual path:
```bash
python cache_generator.py "/Volumes/J/Sample Documents"
```

Or if you're in the repo root:
```bash
python "Local Agent/ExcelAgent/caching/cache_generator.py" "/Volumes/J/Sample Documents"
```

## Step 5: Verify the Output

### Check Cache Directory
The cache should be created at:
```
/Volumes/J/cache/projects/{project_id}/
```

### Verify Files Were Created
```bash
ls -la /Volumes/J/cache/projects/
```

You should see:
- A folder named after your project
- Inside: `index.json` and a `files/` directory

### Check the Index
```bash
cat /Volumes/J/cache/projects/{project_id}/index.json
```

This should show:
- Project metadata
- List of processed files
- Count of processed vs failed files

### Check a Sample Cache File
```bash
ls /Volumes/J/cache/projects/{project_id}/files/
cat /Volumes/J/cache/projects/{project_id}/files/{some-hash}.json | head -50
```

You should see:
- File metadata
- Pages/chunks with text
- Embeddings (arrays of numbers)

## Step 6: Test Different File Types

### Test PDF Only
```bash
python cache_generator.py "/path/to/folder/with/pdfs"
```

### Test Word Only
```bash
python cache_generator.py "/path/to/folder/with/word/docs"
```

### Test Excel Only
```bash
python cache_generator.py "/path/to/folder/with/excel/files"
```

## Troubleshooting

### Error: "OPENAI_API_KEY environment variable is required"
- Make sure you've set the API key (see Step 2)
- Verify: `echo $OPENAI_API_KEY` (should show your key)

### Error: "Google Vision API not available"
- This is OK if you're only testing Word/Excel files
- For PDFs, install: `pip install google-cloud-vision`
- Set `GOOGLE_OCR_KEY_PATH` if you have credentials

### Error: "python-docx not installed"
- Install: `pip install python-docx`

### Error: "openpyxl not installed"
- Install: `pip install openpyxl`

### No files found
- Check that your folder path is correct
- Verify files have correct extensions (.pdf, .docx, .xlsx)
- Check file permissions

### Embeddings are empty arrays
- Check OpenAI API key is valid
- Check you have API credits/quota
- Check internet connection

## Quick Test Script

Create a simple test script `test_cache.py`:

```python
#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from cache_generator import build_project_cache

# Test with a sample folder
test_folder = "/Volumes/J/Sample Documents"  # Change to your test folder

if not os.path.exists(test_folder):
    print(f"❌ Test folder not found: {test_folder}")
    print("Please update test_folder path in this script")
    sys.exit(1)

print(f"🧪 Testing cache generator with: {test_folder}")
result = build_project_cache(test_folder)

print(f"\n✅ Test complete!")
print(f"   Processed: {result['processed']} files")
print(f"   Failed: {result['failed']} files")
print(f"   Cache location: /Volumes/J/cache/projects/{result['project_id']}/")
```

Run it:
```bash
python test_cache.py
```

## Expected Output

When running successfully, you should see:

```
============================================================
Building cache for folder: /path/to/folder
============================================================

Found 3 files to process

[1/3]    Processing: document.pdf
   ✅ Cached 5 page(s)/entry(ies)
[2/3]    Processing: report.docx
   ✅ Cached 3 page(s)/entry(ies)
[3/3]    Processing: calculations.xlsx
   ✅ Cached 1 page(s)/entry(ies)

============================================================
Cache creation complete!
  Processed: 3 files
  Failed: 0 files
  Cache location: /Volumes/J/cache/projects/test_project/
============================================================
```

## Next Steps

Once testing is successful:
1. Integrate into your UI to trigger when user clicks "Add Folder"
2. Use the cache for semantic search queries
3. Monitor cache size and implement cleanup if needed
