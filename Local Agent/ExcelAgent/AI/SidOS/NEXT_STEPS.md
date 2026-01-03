# Next Steps After Parsing

You've successfully generated semantic metadata! Here's your roadmap to a complete system.

## ✅ What You Have Now

1. **Semantic Metadata JSON** (`Glulam_Column_metadata.json`)
   - Maps semantic names to Excel cell addresses
   - Organized into groups (inputs, outputs, lookups)
   - Ready for the local agent

2. **Local Agent System** (`local_agent/`)
   - `ExcelToolAPI` - Fixed tool interface (read_input, write_input, recalculate, read_output)
   - `SemanticMetadataLoader` - Loads and validates metadata
   - `AgentService` - Main service entry point

3. **Test Script** (`test_local_agent.py`)
   - Quick way to test the local agent

---

## 🎯 Phase 2: Test & Validate Local Agent

### Step 1: Test the Local Agent (5 minutes)

```bash
cd "/Users/jameshinsperger/Desktop/Desktop - MacBook Pro (2)/Visual Studio/trainexcel/SidOS"

python test_local_agent.py \
    "/Users/jameshinsperger/Desktop/Desktop - MacBook Pro (2)/Sidian/SidOS/Glulam Column.xlsx" \
    "parsing/Glulam_Column_metadata.json"
```

**What this does:**
- Loads your metadata
- Opens Excel workbook
- Tests reading/writing inputs
- Triggers recalculation
- Reads outputs

**Expected result:** You should see the agent successfully interact with Excel using semantic names.

### Step 2: Verify Metadata Format

Check that your metadata matches the expected format:

```json
{
  "inputs": {
    "parameter_name": {
      "sheet": "SheetName",
      "address": "B3",
      "group": "group_name",
      "description": "..."
    }
  },
  "outputs": {
    "parameter_name": {
      "sheet": "SheetName", 
      "address": "G12",
      "group": "group_name",
      "description": "..."
    }
  }
}
```

**If you have groups instead of individual cells**, the converter should handle it, but verify the format matches what `ExcelToolAPI` expects.

---

## 🚀 Phase 3: Build Cloud Orchestrator (FastAPI)

### Step 3: Create Orchestrator Service

Create `cloud_orchestrator/` directory:

```
SidOS/
├── cloud_orchestrator/
│   ├── __init__.py
│   ├── main.py          # FastAPI app
│   ├── models.py         # Request/Response models
│   ├── orchestrator.py   # LLM orchestration logic
│   └── requirements.txt
```

### Step 4: FastAPI Server

**`cloud_orchestrator/main.py`:**

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import openai

app = FastAPI(title="SidOS Cloud Orchestrator")

class TaskRequest(BaseModel):
    user_query: str
    workbook_path: str
    metadata_path: str

class ToolCall(BaseModel):
    tool: str
    params: Dict[str, Any]

class TaskResponse(BaseModel):
    tool_sequence: List[ToolCall]
    explanation: str

@app.post("/api/orchestrate", response_model=TaskResponse)
async def orchestrate_task(request: TaskRequest):
    """
    Convert user query into tool sequence for local agent.
    
    The orchestrator uses LLM to:
    1. Understand user intent
    2. Map to semantic parameters
    3. Generate tool sequence
    4. Return sequence for local agent execution
    """
    # Load metadata
    import json
    with open(request.metadata_path, 'r') as f:
        metadata = json.load(f)
    
    # Use LLM to plan tool sequence
    tool_sequence = await plan_tool_sequence(
        user_query=request.user_query,
        metadata=metadata
    )
    
    return TaskResponse(
        tool_sequence=tool_sequence,
        explanation="Tool sequence generated from user query"
    )

async def plan_tool_sequence(user_query: str, metadata: dict) -> List[Dict]:
    """
    Use LLM to convert user query into tool sequence.
    
    Example:
    User: "Change span to 15m and show me the moment"
    
    Returns:
    [
        {"tool": "write_input", "params": {"name": "span", "value": 15.0}},
        {"tool": "recalculate", "params": {}},
        {"tool": "read_output", "params": {"name": "moment"}}
    ]
    """
    # Build prompt with available inputs/outputs
    inputs = list(metadata.get("inputs", {}).keys())
    outputs = list(metadata.get("outputs", {}).keys())
    
    prompt = f"""You are an orchestrator that converts user queries into Excel tool sequences.

Available inputs: {inputs}
Available outputs: {outputs}

User query: {user_query}

Generate a tool sequence using these tools:
- read_input(name): Read an input parameter
- write_input(name, value): Write an input parameter
- recalculate(): Trigger Excel recalculation
- read_output(name): Read an output parameter

Return JSON array of tool calls.
"""
    
    # Call LLM (OpenAI or Gemini)
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You convert user queries to tool sequences. Return only valid JSON."},
            {"role": "user", "content": prompt}
        ]
    )
    
    # Parse and return tool sequence
    # ... (implementation)
```

### Step 5: Test Orchestrator Locally

```bash
cd cloud_orchestrator
uvicorn main:app --reload --port 8000
```

Test with:
```bash
curl -X POST "http://localhost:8000/api/orchestrate" \
  -H "Content-Type: application/json" \
  -d '{
    "user_query": "Change span to 15m and show me the moment",
    "workbook_path": "/path/to/workbook.xlsx",
    "metadata_path": "/path/to/metadata.json"
  }'
```

---

## 🎨 Phase 4: Build Streamlit UI

### Step 6: Create Streamlit App

Create `streamlit_app/` directory:

```
SidOS/
├── streamlit_app/
│   ├── app.py
│   ├── components.py
│   └── requirements.txt
```

**`streamlit_app/app.py`:**

```python
import streamlit as st
import requests
import json
from pathlib import Path

st.set_page_config(page_title="SidOS - Junior Engineer", layout="wide")

st.title("🤖 SidOS - Junior Engineer")
st.markdown("Ask questions about your Excel design and get instant answers.")

# Sidebar: Configuration
with st.sidebar:
    st.header("Configuration")
    workbook_path = st.text_input(
        "Excel Workbook Path",
        value="/Users/jameshinsperger/Desktop/Desktop - MacBook Pro (2)/Sidian/SidOS/Glulam Column.xlsx"
    )
    metadata_path = st.text_input(
        "Metadata JSON Path",
        value="/Users/jameshinsperger/Desktop/Desktop - MacBook Pro (2)/Visual Studio/trainexcel/SidOS/parsing/Glulam_Column_metadata.json"
    )
    orchestrator_url = st.text_input(
        "Orchestrator URL",
        value="http://localhost:8000"
    )

# Main chat interface
st.header("💬 Chat with Your Design")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask a question about your design..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get tool sequence from orchestrator
    with st.chat_message("assistant"):
        with st.spinner("Planning actions..."):
            try:
                response = requests.post(
                    f"{orchestrator_url}/api/orchestrate",
                    json={
                        "user_query": prompt,
                        "workbook_path": workbook_path,
                        "metadata_path": metadata_path
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    tool_sequence = result["tool_sequence"]
                    
                    st.markdown("**Planned Actions:**")
                    for tool_call in tool_sequence:
                        st.code(json.dumps(tool_call, indent=2))
                    
                    # Execute on local agent (would be separate API call in production)
                    st.markdown("**Executing...**")
                    # ... execute tool sequence via local agent API
                    
                    st.markdown("**Results:**")
                    st.success("✅ Task completed successfully!")
                else:
                    st.error(f"Error: {response.status_code}")
            except Exception as e:
                st.error(f"Error: {e}")
```

### Step 7: Run Streamlit App

```bash
cd streamlit_app
streamlit run app.py
```

---

## 🔗 Phase 5: Connect Everything

### Step 8: Local Agent API

The local agent needs to expose an HTTP API so the orchestrator can send tasks:

**`local_agent/api_server.py`:**

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from excel_tools import ExcelToolAPI, execute_tool_sequence
from semantic_loader import load_metadata

app = FastAPI(title="SidOS Local Agent API")

class ExecuteTaskRequest(BaseModel):
    workbook_path: str
    metadata_path: str
    tool_sequence: List[Dict[str, Any]]

@app.post("/api/execute")
async def execute_task(request: ExecuteTaskRequest):
    """Execute tool sequence on local Excel workbook"""
    try:
        metadata = load_metadata(request.metadata_path)
        result = execute_tool_sequence(
            workbook_path=request.workbook_path,
            semantic_metadata=metadata,
            tool_sequence=request.tool_sequence,
            visible=False
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Step 9: Update Orchestrator to Call Local Agent

In `cloud_orchestrator/main.py`, after generating tool sequence:

```python
# Send tool sequence to local agent
local_agent_url = "http://localhost:8001"  # Local agent runs on different port
response = requests.post(
    f"{local_agent_url}/api/execute",
    json={
        "workbook_path": request.workbook_path,
        "metadata_path": request.metadata_path,
        "tool_sequence": tool_sequence
    }
)
```

---

## 📋 Complete Workflow

```
User Query (Streamlit)
    ↓
Cloud Orchestrator (FastAPI)
    ↓ (LLM plans tool sequence)
Tool Sequence JSON
    ↓
Local Agent API (FastAPI)
    ↓ (Executes on Excel)
Excel Workbook (xlwings)
    ↓ (Recalculates)
Results
    ↓
Streamlit UI (Displays results)
```

---

## 🎯 Quick Start Checklist

- [ ] **Test local agent** with your metadata
- [ ] **Create cloud orchestrator** (FastAPI)
- [ ] **Test orchestrator** with sample queries
- [ ] **Create Streamlit UI**
- [ ] **Connect orchestrator to local agent**
- [ ] **Test end-to-end workflow**

---

## 💡 Pro Tips

1. **Start Simple**: Get local agent working first, then add orchestrator, then UI
2. **Test Incrementally**: Test each component independently before connecting
3. **Use Logging**: Add extensive logging to debug issues
4. **Error Handling**: Add proper error handling at each layer
5. **Metadata Validation**: Validate metadata format before using

---

## 🚨 Common Issues

1. **Metadata Format Mismatch**: Ensure metadata matches what `ExcelToolAPI` expects
2. **xlwings Not Working**: Check Excel is installed and xlwings is configured
3. **Port Conflicts**: Use different ports for orchestrator (8000) and local agent (8001)
4. **Path Issues**: Use absolute paths for workbooks and metadata

---

## 📚 Next: Production Deployment

Once everything works locally:
1. Deploy orchestrator to AWS (ECS/Lambda)
2. Deploy Streamlit to AWS (Elastic Beanstalk/EC2)
3. Set up secure communication (HTTPS, authentication)
4. Add monitoring and logging
5. Scale for multiple users

---

**You're building something amazing! 🚀**

