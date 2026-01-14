# Excel Agent API Testing Guide

## Overview

The Excel Sync Agent API runs on `http://localhost:8001` and provides endpoints for:
1. **File Operations** - Access any Excel files in allowed directories
2. **Sync Operations** - Work with pre-configured synced projects

## Understanding the Tool Calls

### What Happened in Your Logs

Looking at lines 339-343, the deep agent made these calls:

1. **Line 339**: `get_excel_file_info` - Gets file structure (sheets, columns, dimensions)
2. **Line 341**: `read_desktop_excel` for "Full Building" sheet (20 rows)
3. **Line 342**: `read_desktop_excel` for "INFO" sheet (20 rows)
4. **Line 344**: Agent completed successfully ✅

**Lines 368-415**: These are NOT from the deep agent! These are repeated calls to:
- `/api/agent/status`
- `/api/agent/projects`
- `/api/agent/project/Testing/data`

These are likely from:
- Frontend polling for sync status
- Another component checking project data
- Background health checks

## API Endpoints

### 1. Get Excel File Info

**Endpoint**: `GET /api/agent/files/excel/info`

**What it does**:
- Opens Excel file in read-only mode
- Gets all sheet names
- For each sheet: dimensions (max_row, max_column), first 10 column headers, formula count
- Does NOT read actual data - just structure

**How many cells?**: 
- Only reads first row for headers (first 10 columns)
- Scans first 100 rows × 20 columns to count formulas
- **Does NOT read all cells** - very fast!

**Test with curl**:
```bash
curl -G "http://localhost:8001/api/agent/files/excel/info" \
  --data-urlencode "file_path=/Users/jameshinsperger/Desktop/Desktop - MacBook Pro (2)/Sidian/Vibeeng/Excel Templates/Stud Barn Design (2025 Updates)5.xlsx"
```

**Response**:
```json
{
  "file_path": "/Users/jameshinsperger/Desktop/.../Stud Barn Design (2025 Updates)5.xlsx",
  "file_name": "Stud Barn Design (2025 Updates)5.xlsx",
  "total_sheets": 5,
  "sheets": [
    {
      "sheet_name": "Full Building",
      "dimensions": {
        "max_row": 500,
        "max_column": 25
      },
      "columns": [
        {"column": "A", "header": "Member Name"},
        {"column": "B", "header": "Load"},
        ...
      ],
      "formula_count": 120,
      "has_data": true
    },
    ...
  ],
  "timestamp": "2025-01-15T18:21:04.123456"
}
```

### 2. Read Excel Data

**Endpoint**: `GET /api/agent/files/excel/read`

**What it does**:
- Opens Excel file in read-only mode with `data_only=True` (calculated values, not formulas)
- Reads a specific sheet (or first sheet if not specified)
- Gets headers from row 1 (first 50 columns max)
- Reads data rows starting from row 2
- Limits to `max_rows` parameter (default: 100)

**How many cells?**:
- Headers: First 50 columns from row 1
- Data: `max_rows` rows × up to 50 columns
- **Default: 100 rows × 50 columns = 5,000 cells max**
- The agent can control this with `max_rows` parameter

**Test with curl**:
```bash
# Read first sheet, default 100 rows
curl -G "http://localhost:8001/api/agent/files/excel/read" \
  --data-urlencode "file_path=/Users/jameshinsperger/Desktop/Desktop - MacBook Pro (2)/Sidian/Vibeeng/Excel Templates/Stud Barn Design (2025 Updates)5.xlsx"

# Read specific sheet with 20 rows (like the agent did)
curl -G "http://localhost:8001/api/agent/files/excel/read" \
  --data-urlencode "file_path=/Users/jameshinsperger/Desktop/Desktop - MacBook Pro (2)/Sidian/Vibeeng/Excel Templates/Stud Barn Design (2025 Updates)5.xlsx" \
  --data-urlencode "sheet_name=Full Building" \
  --data-urlencode "max_rows=20"
```

**Response**:
```json
{
  "file_path": "/Users/jameshinsperger/Desktop/.../Stud Barn Design (2025 Updates)5.xlsx",
  "sheet_name": "Full Building",
  "headers": ["Member Name", "Load", "Capacity", "Utilization", ...],
  "row_count": 20,
  "data": [
    {
      "Member Name": "Beam-1",
      "Load": 45.2,
      "Capacity": 50.0,
      "Utilization": 0.904,
      ...
    },
    ...
  ],
  "timestamp": "2025-01-15T18:21:14.123456"
}
```

### 3. List Files

**Endpoint**: `GET /api/agent/files/list`

**What it does**:
- Lists files and directories in a specified directory
- Must be within `allowed_directories` from config.json
- Returns file names, paths, sizes, modification dates

**Test with curl**:
```bash
# List Desktop
curl -G "http://localhost:8001/api/agent/files/list" \
  --data-urlencode "directory=/Users/jameshinsperger/Desktop"

# List specific directory
curl -G "http://localhost:8001/api/agent/files/list" \
  --data-urlencode "directory=/Users/jameshinsperger/Desktop/Desktop - MacBook Pro (2)/Sidian/Vibeeng/Excel Templates"
```

### 4. Sync Agent Status (NOT used by deep agent for file queries)

**Endpoint**: `GET /api/agent/status`

**What it does**:
- Returns sync agent status (idle, syncing, error)
- Last sync time
- Active projects
- Errors

**Test with curl**:
```bash
curl "http://localhost:8001/api/agent/status"
```

**Response**:
```json
{
  "status": "idle",
  "last_sync": "2025-01-15T18:00:00Z",
  "active_projects": ["Testing"],
  "errors": [],
  "agent_configured": true
}
```

### 5. List Projects (NOT used by deep agent for file queries)

**Endpoint**: `GET /api/agent/projects`

**What it does**:
- Lists all configured projects from config.json
- Returns project IDs, names, Excel file paths, sheet names, cell mappings

**Test with curl**:
```bash
curl "http://localhost:8001/api/agent/projects"
```

### 6. Get Project Data (NOT used by deep agent for file queries)

**Endpoint**: `GET /api/agent/project/{project_id}/data`

**What it does**:
- Reads data from a configured project's Excel file
- Uses the cell mappings from config.json
- Only reads the specific cells configured for that project

**Test with curl**:
```bash
curl "http://localhost:8001/api/agent/project/Testing/data"
```

## How the System Decides How Many Cells to Get

### For `get_excel_file_info`:
- **Always fast**: Only reads structure, not data
- Headers: First 10 columns from row 1
- Formula count: Scans first 100 rows × 20 columns
- **Total cells scanned: ~2,000 cells max** (very fast!)

### For `read_desktop_excel`:
- **Controlled by `max_rows` parameter**
- Default: 100 rows
- The deep agent can specify `max_rows` when calling the tool
- Headers: First 50 columns from row 1
- Data: `max_rows` rows × up to 50 columns
- **Example**: `max_rows=20` → 20 rows × 50 columns = 1,000 cells max

### Why the Agent Called `read_desktop_excel` Twice:

Looking at your logs:
- Line 341: Read "Full Building" sheet with 20 rows
- Line 342: Read "INFO" sheet with 20 rows

The agent decided it needed data from both sheets to answer "what info is in this file". This is the deep agent's planning in action - it:
1. Got file structure (line 339)
2. Identified relevant sheets ("Full Building" and "INFO")
3. Read sample data from each (20 rows each)
4. Synthesized an answer

## Why So Many API Calls After Agent Completed?

**Lines 368-415**: These are repeated calls every ~30 seconds:
- `/api/agent/status`
- `/api/agent/projects`
- `/api/agent/project/Testing/data`

**These are NOT from the deep agent!** They're likely from:
1. **Frontend polling**: The UI might be checking sync status periodically
2. **Health checks**: Another service monitoring the agent
3. **Background tasks**: Something checking project data

**To verify**: Check your frontend code for polling intervals or look for other services calling these endpoints.

## Testing All Endpoints

### Quick Test Script

```bash
#!/bin/bash

BASE_URL="http://localhost:8001"
FILE_PATH="/Users/jameshinsperger/Desktop/Desktop - MacBook Pro (2)/Sidian/Vibeeng/Excel Templates/Stud Barn Design (2025 Updates)5.xlsx"

echo "=== 1. Health Check ==="
curl "$BASE_URL/health" | jq

echo -e "\n=== 2. Get Excel File Info ==="
curl -G "$BASE_URL/api/agent/files/excel/info" \
  --data-urlencode "file_path=$FILE_PATH" | jq

echo -e "\n=== 3. Read Excel Data (First Sheet, 20 rows) ==="
curl -G "$BASE_URL/api/agent/files/excel/read" \
  --data-urlencode "file_path=$FILE_PATH" \
  --data-urlencode "max_rows=20" | jq

echo -e "\n=== 4. Read Specific Sheet ==="
curl -G "$BASE_URL/api/agent/files/excel/read" \
  --data-urlencode "file_path=$FILE_PATH" \
  --data-urlencode "sheet_name=Full Building" \
  --data-urlencode "max_rows=10" | jq

echo -e "\n=== 5. List Files in Directory ==="
curl -G "$BASE_URL/api/agent/files/list" \
  --data-urlencode "directory=/Users/jameshinsperger/Desktop" | jq

echo -e "\n=== 6. Sync Agent Status ==="
curl "$BASE_URL/api/agent/status" | jq

echo -e "\n=== 7. List Projects ==="
curl "$BASE_URL/api/agent/projects" | jq
```

Save as `test_api.sh`, make executable: `chmod +x test_api.sh`, then run: `./test_api.sh`

## How to See the Agent's Thinking

The deep agent's reasoning and tool call decisions are now logged in the backend logs. Look for:

```
🧠 AGENT THINKING - Total messages: X
   [0] USER: <user query>
   [1] AGENT THINKING: <agent's reasoning>
   [2] AGENT DECISION: Calling 1 tool(s)
      🔧 Tool: get_excel_file_info
         - file_path: /Users/.../file.xlsx
   [3] TOOL RESULT: <tool response>
   [4] AGENT DECISION: Calling 1 tool(s)
      🔧 Tool: read_desktop_excel
         - file_path: /Users/.../file.xlsx
         - sheet_name: Full Building
         - max_rows: 20
   [5] TOOL RESULT: <tool response>
   [6] AGENT THINKING: <final reasoning>
```

**Where to find this**:
- Backend logs: Look for `🧠 AGENT THINKING` entries
- Log file: Check your backend log file for `ROUTING - INFO` entries
- Terminal: If running backend in terminal, you'll see these logs in real-time

**What you'll see**:
- **AGENT THINKING**: The agent's reasoning before making decisions
- **AGENT DECISION**: When the agent decides to call a tool, with exact parameters
- **TOOL RESULT**: What the tool returned (truncated for readability)

**Example**: When you see `max_rows=20`, that's the agent's decision based on:
- The query complexity
- The file structure it saw
- Its planning to read a sample first

## Summary

**Deep Agent Tool Calls (for file queries)**:
1. `get_excel_file_info` - Fast, only structure (~2,000 cells scanned)
2. `read_desktop_excel` - Controlled by `max_rows` (default 100, agent can specify)
3. `list_desktop_files` - Only if file path not provided

**Sync Agent Calls (NOT used for file queries)**:
- `/api/agent/status` - Status check
- `/api/agent/projects` - List configured projects
- `/api/agent/project/{id}/data` - Read configured project data

**The repeated calls (lines 368-415) are NOT from the deep agent** - they're from frontend polling or other services.

**To see agent thinking**: Check backend logs for `🧠 AGENT THINKING` entries showing reasoning and tool call parameters.
