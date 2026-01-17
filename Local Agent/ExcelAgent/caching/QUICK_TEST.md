# Quick Testing Guide

## Setup Checklist

✅ **1. Environment Variables**
- Make sure `.env` file in project root has:
  ```
  OPENAI_API_KEY=sk-your-key-here
  ```

✅ **2. Dependencies Installed**
```bash
cd "/Volumes/J/Sid-Master-Repo/Local Agent/ExcelAgent/caching"
pip install -r requirements.txt
```

✅ **3. Local Agent Running**
```bash
cd "/Volumes/J/Sid-Master-Repo/Local Agent/ExcelAgent/Agent_007_James"
python agent_api.py --config config.json --port 8001
```

✅ **4. Frontend Running**
```bash
cd "/Volumes/J/Sid-Master-Repo/Frontend/Frontend"
npm run dev
```

## Testing Steps

### Step 1: Start Everything
1. Start Local Agent (port 8001)
2. Start Frontend (usually port 3000)
3. Start Backend (port 8000) - if needed

### Step 2: Test in Frontend
1. Open browser to frontend URL (usually http://localhost:3000)
2. Navigate to Work/Projects view
3. Click "Add Folder" button
4. Select a folder with some PDF/Word/Excel files
5. Click "Select This Folder"

### Step 3: What Should Happen
- ✅ Folder is added to your saved folders
- ✅ Notification appears: "Cache generation started for [folder name]..."
- ✅ Cache building runs in background
- ✅ Check browser console for logs

### Step 4: Verify Cache Was Created
```bash
# Check cache directory
ls -la /Volumes/J/cache/projects/

# Check specific project cache
cat /Volumes/J/cache/projects/{project_name}/index.json
```

### Step 5: Check Local Agent Logs
```bash
# View agent API logs
tail -f "/Volumes/J/Sid-Master-Repo/Local Agent/ExcelAgent/Agent_007_James/agent_api.log"
```

## Expected Behavior

**When folder is selected:**
1. Frontend calls: `POST http://localhost:8001/api/agent/cache/build`
2. Local Agent validates folder path
3. Local Agent starts cache generation in background
4. Returns immediately with success message
5. Cache generation continues processing files

**Cache generation process:**
- Scans folder for PDF, Word, Excel files
- For each file:
  - PDFs: OCR each page → generate embeddings
  - Word: Extract text per page → generate embeddings
  - Excel: Extract file name + sheet names → generate embedding
- Saves cache to `/Volumes/J/cache/projects/{project_id}/`

## Troubleshooting

### "Cache generator not available"
- Check that caching folder exists
- Check Python path in agent_api.py
- Verify cache_generator.py is in the caching folder

### "OPENAI_API_KEY environment variable is required"
- Set OPENAI_API_KEY in .env file
- Restart local agent after setting

### "Access denied: Path is not within allowed directories"
- Add folder path to `allowed_directories` in config.json
- Or add parent directory (e.g., `/Volumes`)

### Cache not appearing
- Check `/Volumes/J/cache/projects/` directory exists
- Check file permissions
- Check local agent logs for errors

## API Testing (Direct)

You can also test the API directly:

```bash
# Build cache
curl -X POST http://localhost:8001/api/agent/cache/build \
  -H "Content-Type: application/json" \
  -d '{"folder_path": "/Volumes/J/Sample Documents"}'

# Check status
curl http://localhost:8001/api/agent/cache/status/Sample_Documents
```

## Success Indicators

✅ **Frontend:**
- Notification appears when folder is selected
- No errors in browser console
- Folder appears in saved folders list

✅ **Local Agent:**
- Log shows "Starting cache build for folder: ..."
- Log shows "Cache build complete: X files processed"
- No errors in agent_api.log

✅ **Cache Files:**
- `/Volumes/J/cache/projects/{project_id}/index.json` exists
- `/Volumes/J/cache/projects/{project_id}/files/` contains JSON files
- Each JSON file has `metadata` and `pages` with embeddings
