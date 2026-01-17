# Project Folder Cache Generator

This module creates embeddings cache for all files in a selected project folder. It processes PDFs, Word documents, and Excel files, generating embeddings for semantic search.

## Features

- **PDF Processing**: Uses Google Vision API for OCR, extracts text per page
- **Word Processing**: Extracts text from Word documents, splits into logical pages
- **Excel Processing**: Extracts file name and worksheet names
- **Embeddings**: Uses OpenAI `text-embedding-3-small` for all embeddings
- **Cache Storage**: Stores cache in `/Volumes/J/cache/projects/{project_id}/`

## Requirements

```bash
pip install openai python-docx openpyxl google-cloud-vision python-dotenv
```

## Environment Variables

- `OPENAI_API_KEY`: Required for generating embeddings
- `GOOGLE_OCR_KEY_PATH`: Optional, path to Google Vision API credentials JSON file

## Usage

### Command Line

```bash
python cache_generator.py /path/to/project/folder
```

### Python API

```python
from cache_generator import build_project_cache

result = build_project_cache("/path/to/project/folder")
print(f"Processed {result['processed']} files")
```

## Cache Structure

```
/Volumes/J/cache/projects/{project_id}/
  ├── index.json          # Master index with all file metadata
  └── files/
      ├── {file_hash1}.json
      ├── {file_hash2}.json
      └── ...
```

Each file cache contains:
- File metadata (name, size, dates, type)
- Pages/chunks with text and embeddings
- Timestamp of when it was cached

## Integration

To trigger when user clicks "Add Folder" in the UI, call:

```python
from Local_Agent.ExcelAgent.caching.cache_generator import build_project_cache

# When folder is selected
folder_path = "/path/to/selected/folder"
result = build_project_cache(folder_path)
```
