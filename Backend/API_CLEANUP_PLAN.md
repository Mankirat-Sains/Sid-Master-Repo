# API Server Cleanup Plan

## Analysis Complete

### Functions TO KEEP (actively used in /chat/stream):
- ✅ `strip_asterisks_from_projects()` - Used 4x in streaming endpoint
- ✅ `wrap_code_file_links()` - Used 3x in streaming endpoint  
- ✅ `wrap_coop_file_links()` - Used 1x in streaming endpoint
- ✅ `wrap_external_links()` - Used 2x in streaming endpoint
- ✅ Supabase logger imports - Used throughout for logging
- ✅ Enhanced logger imports - Used in /logs/enhanced endpoints
- ✅ `INSTRUCTIONS_CONTENT` - Used in /instructions endpoint

### Functions TO REMOVE (unused):
- ❌ `sanitize_file_path()` (lines 181-210) - NOT USED ANYWHERE
- ❌ `/debug/categories` endpoint (lines 1181-1227) - Debug only, not needed
- ❌ Electron-specific comments (lines 4, 1001, 2579)
- ❌ `/feedback` POST endpoint - ALREADY REMOVED by user
- ❌ `FeedbackRequest` model (line 1146) - No longer needed

### Endpoints Analysis

**Active Endpoints (24 total):**
1. `/health` - Health check
2. `/chat/stream` - PRIMARY ENDPOINT ✅
3. `/approve-action` - Deep agent interrupts
4. `/api/doc/*` - Document operations (5 endpoints)
5. `/chat/upload-ifc` - IFC file upload
6. `/feedback/stats` - Feedback statistics (keep for analytics)
7. `/db/health` - Database health
8. `/debug/routing` - Routing debug
9. `/logs/enhanced` - Enhanced logging (3 endpoints)
10. `/stats/*` - Supabase statistics (3 endpoints)
11. `/instructions` - User instructions
12. `/test/backend-version` - Version check
13. `/` - Root redirect
14. `/graph/cypher` - Graph database query
15. `/graph/schema` - Graph schema

**Endpoints to Remove:**
- ❌ `/debug/categories` - Debug only

**Endpoints Already Removed:**
- ✅ `/chat` - REMOVED in Phase 1
- ✅ `/chat/legacy` - REMOVED in Phase 1
- ✅ `/feedback` POST - REMOVED by user
- ✅ `/renderer-update/*` - REMOVED by user

## Cleanup Tasks

### 1. Remove Unused Function
```python
# Remove lines 181-210: sanitize_file_path() function
```

### 2. Remove Debug Endpoint
```python
# Remove lines 1181-1227: /debug/categories endpoint
```

### 3. Remove Unused Model
```python
# Remove line 1146: FeedbackRequest class
```

### 4. Clean Up Comments
```python
# Line 4: Remove "Connect the chatbutton Electron app to the rag.py backend"
# Line 1001: Remove "# Enable CORS for the Electron desktop app"
# Line 2579: Remove Electron reference in print statement
```

### 5. Update Docstrings
- Update module docstring to reflect current purpose
- Remove Electron references from endpoint docstrings

## Impact Assessment

**Lines to Remove: ~80 lines**
- `sanitize_file_path()`: 30 lines
- `/debug/categories`: 47 lines
- `FeedbackRequest`: 6 lines
- Comments: ~5 lines

**Risk Level: LOW**
- All removed code is confirmed unused
- No dependencies on removed functionality
- Active endpoints remain untouched

## Next: Phase 2 - Function Renaming

After cleanup, proceed with:
1. Rename `run_agentic_rag()` → `execute_query()`
2. Rename `rag_wrapper.py` → `query_wrapper.py`
3. Update all imports across codebase
4. Rename state classes (Phase 3)

---

**Status**: Ready to execute cleanup
**Estimated Time**: 15 minutes
**Risk**: Low
