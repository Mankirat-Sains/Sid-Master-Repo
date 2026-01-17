# Cache Generator Integration Guide

## Overview

The cache generator is now integrated into the Local Agent API. When a user selects a folder in the UI, you can trigger cache generation via an API call.

## API Endpoints

### 1. Build Cache (POST)
```
POST /api/agent/cache/build
```

**Request Body:**
```json
{
  "folder_path": "/Volumes/J/25-02-186"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Cache building started for folder: /Volumes/J/25-02-186. Processing in background.",
  "cache_location": "/Volumes/J/cache/projects/25-02-186/",
  "timestamp": "2026-01-16T10:30:00.000000"
}
```

**Note:** This endpoint returns immediately and processes in the background. The cache generation may take several minutes depending on the number of files.

### 2. Get Cache Status (GET)
```
GET /api/agent/cache/status/{project_id}
```

**Response:**
```json
{
  "exists": true,
  "project_id": "25-02-186",
  "folder_path": "/Volumes/J/25-02-186",
  "created_at": "2026-01-16T10:30:00.000000",
  "total_files": 15,
  "processed": 15,
  "failed": 0,
  "cache_location": "/Volumes/J/cache/projects/25-02-186",
  "files": [...]
}
```

## Frontend Integration

### When User Clicks "Add Folder"

```typescript
// In your frontend code (e.g., ProjectChat.vue or folder selection component)

async function handleFolderSelected(folderPath: string) {
  try {
    // Call the cache build endpoint
    const response = await fetch('http://localhost:8001/api/agent/cache/build', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        folder_path: folderPath
      })
    });
    
    const result = await response.json();
    
    if (result.success) {
      console.log('Cache building started:', result.message);
      // Show user a notification that cache is being built
      // You can poll the status endpoint to check progress
    }
  } catch (error) {
    console.error('Error starting cache build:', error);
  }
}

// Poll cache status (optional - to show progress)
async function checkCacheStatus(projectId: string) {
  try {
    const response = await fetch(
      `http://localhost:8001/api/agent/cache/status/${projectId}`
    );
    const status = await response.json();
    return status;
  } catch (error) {
    console.error('Error checking cache status:', error);
    return null;
  }
}
```

## Backend Integration

If you want to call this from the backend instead:

```python
import httpx

async def build_cache_for_folder(folder_path: str):
    """Call local agent API to build cache"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8001/api/agent/cache/build",
            json={"folder_path": folder_path}
        )
        return response.json()
```

## Testing in Production

1. **Start Local Agent:**
   ```bash
   cd "/Volumes/J/Sid-Master-Repo/Local Agent/ExcelAgent/Agent_007_James"
   python agent_api.py --config config.json --port 8001
   ```

2. **Test the endpoint:**
   ```bash
   curl -X POST http://localhost:8001/api/agent/cache/build \
     -H "Content-Type: application/json" \
     -d '{"folder_path": "/Volumes/J/Sample Documents"}'
   ```

3. **Check status:**
   ```bash
   curl http://localhost:8001/api/agent/cache/status/Sample_Documents
   ```

## Environment Setup

Make sure your `.env` file in the project root has:
```
OPENAI_API_KEY=sk-your-key-here
GOOGLE_OCR_KEY_PATH=/path/to/google-ocr-key.json  # Optional, for PDFs
```

The local agent will automatically load environment variables when it starts.

## Error Handling

The endpoint will:
- Validate that the folder path is within allowed directories
- Check that the folder exists
- Return errors if cache generator dependencies are missing
- Process in background so it doesn't block the API

## Cache Location

Caches are stored at:
```
/Volumes/J/cache/projects/{project_id}/
  ├── index.json
  └── files/
      ├── {file_hash1}.json
      ├── {file_hash2}.json
      └── ...
```

The `project_id` is automatically generated from the folder name.
