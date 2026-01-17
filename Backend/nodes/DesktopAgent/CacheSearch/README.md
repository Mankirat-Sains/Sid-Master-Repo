# CacheSearch Module

Sandboxed module for testing local cache retrieval from project folders.

## How It Works

1. **Detection**: When a user asks a question in ProjectChat, the frontend includes folder context:
   ```
   [Context: User is working in project folder: /path/to/folder]
   ```

2. **Pre-Router**: `pre_router.py` detects this pattern and routes to CacheSearch

3. **Search**: `retriever.py` searches the local cache at `/Volumes/J/cache/projects/{project_id}/`

4. **Answer**: `node.py` generates an answer using the cached documents

5. **Return**: Results are returned as `final_answer` and bypass normal routing

## File Structure

```
CacheSearch/
├── __init__.py          # Module init
├── retriever.py         # Local cache search logic
├── router.py            # Detection logic (has_folder_context)
├── pre_router.py        # Intercepts queries before normal routing
├── router_wrapper.py    # Wraps router_dispatcher
├── node.py              # Main search and answer generation
└── README.md            # This file
```

## Integration Points

- **graph/builder.py**: Uses `node_router_dispatcher_with_cache_search` wrapper
- **graph/subgraphs/cache_search_subgraph.py**: Standalone subgraph for CacheSearch

## Testing

1. Make sure cache exists for your test folder:
   ```bash
   ls /Volumes/J/cache/projects/{project_id}/
   ```

2. Ask a question in ProjectChat with that folder selected

3. Check logs for:
   - `🎯 PROJECTCHAT QUERY DETECTED`
   - `🔍 Searching cache for folder: ...`
   - `✅ Found X results from local cache`

## Notes

- This is **sandboxed** - doesn't modify existing retrieval code
- Only activates when folder context is detected
- Falls through to normal routing if no folder context or cache not found
- Results are returned as `final_answer` to match normal flow
