# SidOS Frontend Setup Guide

## Quick Start

1. **Install Dependencies**
   ```bash
   cd Frontend
   npm install
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your values:
   - `ORCHESTRATOR_URL`: Your LangGraph backend (e.g., `http://localhost:8000`)
   - `SPECKLE_URL`: Your AWS-hosted Speckle server URL
   - `SPECKLE_TOKEN`: Speckle authentication token

3. **Start Development Server**
   ```bash
   npm run dev
   ```

   The app will be available at `http://localhost:3000`

## Integration with Orchestrator

### Expected Response Format

The orchestrator should return responses in this format:

```json
{
  "answer": "Here's information about project 25-08-127...",
  "model_info": {
    "projectId": "b44d7945a3",
    "modelId": "1711f08980",
    "commitId": "optional-commit-id",
    "projectNumber": "25-08-127"
  },
  "citations": 5,
  "message_id": "msg_12345"
}
```

### Adding Model Info to Orchestrator Response

In your `rag.py` or `api_server.py`, you can extract model information from:
1. **Project citations**: Extract Speckle project/model IDs from citations
2. **Answer text**: Parse project numbers and map to Speckle IDs
3. **Query context**: If user asks about a specific project, look up its Speckle IDs

Example helper function to add to your orchestrator:

```python
def extract_model_info_from_response(answer: str, citations: List[Dict]) -> Optional[Dict]:
    """
    Extract Speckle model information from RAG response.
    
    Returns:
        {
            "projectId": "speckle-project-id",
            "modelId": "speckle-model-id",
            "commitId": "optional-commit-id",
            "projectNumber": "25-08-127"
        }
    """
    # Method 1: Check citations for Speckle URLs
    for citation in citations:
        if 'speckle_url' in citation:
            # Parse URL to extract IDs
            # Format: https://speckle.xyz/projects/{projectId}/models/{modelId}
            pass
    
    # Method 2: Extract project number from answer and look up in mapping
    import re
    project_match = re.search(r'\b(\d{2}-\d{2}-\d{3})\b', answer)
    if project_match:
        project_number = project_match.group(1)
        # Look up in your PROJECT_MODEL_MAP or query Supabase
        # Return mapped Speckle IDs
    
    # Method 3: Check if answer contains explicit Speckle IDs
    project_id_match = re.search(r'project[_\s]?id[:\s]+([a-zA-Z0-9]{10,})', answer, re.IGNORECASE)
    model_id_match = re.search(r'model[_\s]?id[:\s]+([a-zA-Z0-9]{10,})', answer, re.IGNORECASE)
    
    if project_id_match and model_id_match:
        return {
            "projectId": project_id_match.group(1),
            "modelId": model_id_match.group(1)
        }
    
    return None
```

Then in your `run_agentic_rag` return statement, add:

```python
model_info = extract_model_info_from_response(
    final_state.final_answer,
    final_state.answer_citations
)

return {
    "answer": final_state.final_answer,
    "model_info": model_info,  # Add this
    # ... rest of response
}
```

## Project Number to Speckle ID Mapping

You'll need to maintain a mapping between project numbers (like "25-08-127") and Speckle project/model IDs. Options:

1. **Store in Supabase**: Add a `speckle_project_id` and `speckle_model_id` column to your project metadata table
2. **Environment variables**: For development, use a simple mapping
3. **Query Speckle GraphQL**: Search for projects by name/number

## Testing

1. **Test Chat Interface**:
   - Send a message: "Show me project 25-08-127"
   - Verify response appears in chat

2. **Test Viewer Integration**:
   - Ask about a project with a known Speckle model
   - Verify model loads in viewer panel

3. **Test Model Extraction**:
   - Check browser console for any errors
   - Verify model info is extracted correctly

## Troubleshooting

### Viewer Not Loading
- Check browser console for errors
- Verify `SPECKLE_URL` and `SPECKLE_TOKEN` are correct
- Ensure the project/model IDs are valid
- Check CORS settings on Speckle server

### Chat Not Working
- Verify `ORCHESTRATOR_URL` is correct
- Check orchestrator is running
- Look for CORS errors in browser console

### Model Info Not Extracted
- Check orchestrator response includes `model_info`
- Verify model extraction logic in frontend
- Check browser console for parsing errors

