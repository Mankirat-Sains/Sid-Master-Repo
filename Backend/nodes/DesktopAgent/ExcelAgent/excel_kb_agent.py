"""
Excel Knowledge Base Agent (Deep Agent)
Reads Excel files via the Excel Sync Agent (Agent_007_James) which runs locally on user's machine.
The sync agent has access to local Excel files and provides data to the cloud backend.
This agent queries Excel data through the sync agent API - it cannot access files directly.

Uses create_deep_agent for multi-step planning and intelligent data extraction.
"""
import json
import os
from typing import Dict, Any, Optional
from langchain_core.tools import tool
from deepagents import create_deep_agent
from deepagents.backends import StateBackend
from models.desktop_agent_state import DesktopAgentState
from config.llm_instances import llm_fast, llm_synthesis
from config.logging_config import log_route
import httpx


# Excel Sync Agent API configuration
AGENT_API_URL = os.getenv("AGENT_API_URL", "http://localhost:8001")
AGENT_API_TIMEOUT = 30  # seconds


def _create_excel_tools(state: DesktopAgentState):
    """
    Create Excel tools that use the Excel Sync Agent API.
    All Excel file access goes through the sync agent which runs locally on the user's machine.
    """
    
    @tool
    def list_excel_projects() -> str:
        """
        List all Excel projects configured in the Excel Sync Agent.
        These are Excel files on the user's local machine that are set up for syncing.
        
        IMPORTANT: ONLY use this tool if the user explicitly asks about "synced projects", "configured projects", or "projects in the sync agent".
        DO NOT use this tool for general queries about Excel files - use get_excel_file_info() or read_desktop_excel() instead.
        
        Returns:
            List of configured projects with their Excel file paths, sheet names, and cell mappings
        """
        try:
            with httpx.Client(timeout=AGENT_API_TIMEOUT) as client:
                response = client.get(f"{AGENT_API_URL}/api/agent/projects")
                if response.status_code == 200:
                    projects = response.json()
                    return json.dumps({
                        "count": len(projects),
                        "projects": projects,
                        "note": "These are Excel files configured in the sync agent. Use read_excel_data(project_id) to read their data."
                    }, indent=2)
                else:
                    return f"Error: Sync agent service returned status {response.status_code}"
        except httpx.ConnectError:
            return f"Error: Cannot connect to sync agent at {AGENT_API_URL}. Make sure the agent service is running (agent_api.py on port 8001)."
        except Exception as e:
            return f"Error listing Excel projects: {str(e)}"
    
    @tool
    def read_excel_data(project_id: str) -> str:
        """
        Read data from an Excel file via the Excel Sync Agent.
        This reads the configured cells from the Excel file on the user's local machine.
        The sync agent must be running and the project must be configured.
        
        IMPORTANT: ONLY use this tool if the user explicitly asks about a "synced project" or mentions a project_id.
        For general Excel file queries, use read_desktop_excel() with a file path instead.
        
        Args:
            project_id: Project ID to read data from (use list_excel_projects to see available projects)
        
        Returns:
            Current data from the Excel file's configured cells
        """
        try:
            with httpx.Client(timeout=AGENT_API_TIMEOUT) as client:
                response = client.get(f"{AGENT_API_URL}/api/agent/project/{project_id}/data")
                if response.status_code == 200:
                    data = response.json()
                    return json.dumps({
                        "project_id": data.get("project_id"),
                        "data": data.get("data", {}),
                        "timestamp": data.get("timestamp"),
                        "note": "This data was read from the Excel file on the user's local machine via the sync agent."
                    }, indent=2)
                else:
                    error_text = response.text if response.text else f"Status {response.status_code}"
                    return f"Error reading Excel data: {error_text}. Make sure the project_id is correct and the sync agent is running."
        except httpx.ConnectError:
            return f"Error: Cannot connect to sync agent at {AGENT_API_URL}. Make sure the agent service is running."
        except Exception as e:
            return f"Error reading Excel data: {str(e)}"
    
    @tool
    def get_sync_agent_status() -> str:
        """
        Get the status of the Excel Sync Agent service.
        This tells you if the sync agent is running and ready to sync Excel data to the platform.
        
        IMPORTANT: ONLY use this tool if the user explicitly asks about "sync agent status", "is the agent running", or sync-related status.
        DO NOT call this tool for general Excel file queries - it's not needed.
        
        Returns:
            Status information including agent state, last sync time, active projects
        """
        try:
            with httpx.Client(timeout=AGENT_API_TIMEOUT) as client:
                response = client.get(f"{AGENT_API_URL}/api/agent/status")
                if response.status_code == 200:
                    data = response.json()
                    return json.dumps({
                        "status": data.get("status", "unknown"),
                        "agent_configured": data.get("agent_configured", False),
                        "last_sync": data.get("last_sync"),
                        "active_projects": data.get("active_projects", []),
                        "errors": data.get("errors", [])
                    }, indent=2)
                else:
                    return f"Error: Sync agent service returned status {response.status_code}. Is the agent running at {AGENT_API_URL}?"
        except httpx.ConnectError:
            return f"Error: Cannot connect to sync agent at {AGENT_API_URL}. Make sure the agent service is running (agent_api.py on port 8001)."
        except Exception as e:
            return f"Error getting sync agent status: {str(e)}"
    
    @tool
    def sync_excel_to_platform(project_id: Optional[str] = None, force: bool = False) -> str:
        """
        Sync Excel file data to the cloud platform using the Excel Sync Agent.
        This reads the configured cells from the Excel file and sends them to the platform.
        
        Args:
            project_id: Optional project ID to sync. If not provided, syncs all configured projects
            force: Whether to force sync even if not requested by platform
        
        Returns:
            Sync result with success status and any data that was synced
        """
        try:
            with httpx.Client(timeout=AGENT_API_TIMEOUT) as client:
                payload = {"force": force}
                if project_id:
                    payload["project_id"] = project_id
                
                response = client.post(
                    f"{AGENT_API_URL}/api/agent/sync",
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return json.dumps({
                        "success": result.get("success", False),
                        "project_id": result.get("project_id", "all"),
                        "message": result.get("message", ""),
                        "timestamp": result.get("timestamp", ""),
                        "data": result.get("data")
                    }, indent=2)
                else:
                    error_text = response.text if response.text else f"Status {response.status_code}"
                    return f"Error syncing to platform: {error_text}"
        except httpx.ConnectError:
            return f"Error: Cannot connect to sync agent at {AGENT_API_URL}. Make sure the agent service is running."
        except Exception as e:
            return f"Error syncing to platform: {str(e)}"
    
    @tool
    def get_sync_history(limit: int = 10) -> str:
        """
        Get the sync history from the Excel Sync Agent.
        Shows recent sync operations and their results.
        
        Args:
            limit: Maximum number of history entries to return (default: 10)
        
        Returns:
            List of recent sync operations
        """
        try:
            with httpx.Client(timeout=AGENT_API_TIMEOUT) as client:
                response = client.get(f"{AGENT_API_URL}/api/agent/history", params={"limit": limit})
                if response.status_code == 200:
                    history = response.json()
                    return json.dumps({
                        "count": len(history) if isinstance(history, list) else 0,
                        "history": history
                    }, indent=2)
                else:
                    return f"Error: Sync agent service returned status {response.status_code}"
        except httpx.ConnectError:
            return f"Error: Cannot connect to sync agent at {AGENT_API_URL}. Make sure the agent service is running."
        except Exception as e:
            return f"Error getting sync history: {str(e)}"
    
    @tool
    def list_desktop_files(directory: Optional[str] = None) -> str:
        """
        List files and directories on the user's local machine.
        The directory must be within allowed directories configured in the desktop agent.
        
        Args:
            directory: Directory path to list (default: user's Desktop). Can be relative or absolute.
        
        Returns:
            List of files and directories with their metadata
        """
        try:
            with httpx.Client(timeout=AGENT_API_TIMEOUT) as client:
                params = {}
                if directory:
                    params["directory"] = directory
                
                response = client.get(f"{AGENT_API_URL}/api/agent/files/list", params=params)
                if response.status_code == 200:
                    data = response.json()
                    return json.dumps(data, indent=2)
                else:
                    error_text = response.text if response.text else f"Status {response.status_code}"
                    return f"Error listing files: {error_text}"
        except httpx.ConnectError:
            return f"Error: Cannot connect to desktop agent at {AGENT_API_URL}. Make sure the agent service is running."
        except Exception as e:
            return f"Error listing files: {str(e)}"
    
    @tool
    def get_excel_file_info(file_path: str) -> str:
        """
        Get structure and metadata about an Excel file on the user's local machine.
        This shows sheets, columns, dimensions, and formula counts without reading all data.
        
        USE THIS TOOL FIRST when user asks:
        - "What info is in this file?"
        - "What is this file for?"
        - "Tell me about this Excel file"
        - "What does this file contain?"
        
        After calling this tool, you usually have ENOUGH information to answer. STOP and provide the answer based on the file structure.
        Only call read_desktop_excel() if the user asks for specific data values.
        
        Args:
            file_path: Path to Excel file (can be relative or absolute)
        
        Returns:
            Excel file structure including sheets, columns, and dimensions
        """
        try:
            with httpx.Client(timeout=AGENT_API_TIMEOUT) as client:
                response = client.get(
                    f"{AGENT_API_URL}/api/agent/files/excel/info",
                    params={"file_path": file_path}
                )
                if response.status_code == 200:
                    data = response.json()
                    return json.dumps(data, indent=2)
                else:
                    error_text = response.text if response.text else f"Status {response.status_code}"
                    return f"Error getting Excel info: {error_text}"
        except httpx.ConnectError:
            return f"Error: Cannot connect to desktop agent at {AGENT_API_URL}. Make sure the agent service is running."
        except Exception as e:
            return f"Error getting Excel info: {str(e)}"
    
    @tool
    def read_desktop_excel(file_path: str, sheet_name: Optional[str] = None, max_rows: int = 100, include_formulas: bool = True, include_code_refs: bool = True) -> str:
        """
        Read data from an Excel file on the user's local machine.
        The file path must be within allowed directories configured in the desktop agent.
        
        This tool returns:
        - Cell values (calculated results)
        - Formulas (if include_formulas=True) - shows how values are calculated
        - Building code references (if include_code_refs=True) - finds code clauses referenced
        - Structured context - label-value pairs to understand relationships
        
        The structured context helps you understand:
        - Which labels correspond to which values (e.g., "Dead Load" = "2" kPa)
        - What formulas calculate what values
        - What building codes are referenced and where
        
        IMPORTANT: For "all information" queries, use max_rows=500 to read comprehensive samples.
        DO NOT try to read every single cell - read representative samples and summarize.
        
        Args:
            file_path: Path to Excel file (can be relative or absolute)
            sheet_name: Optional sheet name (reads first sheet if not specified)
            max_rows: Maximum number of data rows to read (default: 100, use 500 for comprehensive samples)
            include_formulas: Include formulas in response (default: True)
            include_code_refs: Extract building code references (default: True)
        
        Returns:
            Excel data with formulas, code references, and structured context (label-value pairs)
        """
        try:
            with httpx.Client(timeout=AGENT_API_TIMEOUT) as client:
                params = {
                    "file_path": file_path, 
                    "max_rows": max_rows,
                    "include_formulas": str(include_formulas).lower(),
                    "include_code_refs": str(include_code_refs).lower()
                }
                if sheet_name:
                    params["sheet_name"] = sheet_name
                
                response = client.get(
                    f"{AGENT_API_URL}/api/agent/files/excel/read",
                    params=params
                )
                if response.status_code == 200:
                    data = response.json()
                    return json.dumps(data, indent=2)
                else:
                    error_text = response.text if response.text else f"Status {response.status_code}"
                    return f"Error reading Excel file: {error_text}"
        except httpx.ConnectError:
            return f"Error: Cannot connect to desktop agent at {AGENT_API_URL}. Make sure the agent service is running."
        except Exception as e:
            return f"Error reading Excel file: {str(e)}"
    
    @tool
    def extract_relevant_data(file_path: str, query: str) -> str:
        """
        Intelligently extract only the data needed to answer an engineering question.
        This tool plans what to extract based on the query, then extracts it on-demand.
        Use this for complex engineering questions that require understanding what data is relevant.
        
        The tool will:
        1. Get Excel file structure to understand available data
        2. Identify relevant sheets and columns based on the query
        3. Read only the necessary data (not entire files)
        4. Return structured analysis relevant to the query
        
        Args:
            file_path: Path to Excel file
            query: Engineering question to answer (e.g., "What beams were designed and what capacity were they at?")
        
        Returns:
            Extracted and analyzed data relevant to the query, with engineering context
        """
        try:
            with httpx.Client(timeout=AGENT_API_TIMEOUT) as client:
                # Step 1: Get file structure
                info_response = client.get(
                    f"{AGENT_API_URL}/api/agent/files/excel/info",
                    params={"file_path": file_path}
                )
                
                if info_response.status_code != 200:
                    return f"Error getting file structure: {info_response.text}"
                
                info_data = info_response.json()
                sheets = info_data.get("sheets", [])
                
                if not sheets:
                    return "No sheets found in Excel file"
                
                # Step 2: Identify most relevant sheet based on query keywords
                query_lower = query.lower()
                relevant_sheet = None
                
                # Heuristic: look for sheet names that match query
                for sheet in sheets:
                    sheet_name = sheet.get("sheet_name", "").lower()
                    # Check for structural design keywords
                    if any(keyword in sheet_name for keyword in ["building", "design", "member", "beam", "column", "full"]):
                        if "full" in sheet_name or "design" in sheet_name or "building" in sheet_name:
                            relevant_sheet = sheet.get("sheet_name")
                            break
                
                # Fallback to first sheet with data
                if not relevant_sheet:
                    for sheet in sheets:
                        if sheet.get("has_data"):
                            relevant_sheet = sheet.get("sheet_name")
                            break
                
                if not relevant_sheet:
                    return "No data sheets found in Excel file"
                
                # Step 3: Read relevant data (limit rows for efficiency - deep agent can read more if needed)
                read_response = client.get(
                    f"{AGENT_API_URL}/api/agent/files/excel/read",
                    params={
                        "file_path": file_path,
                        "sheet_name": relevant_sheet,
                        "max_rows": 200  # Start with 200 rows, can read more if needed
                    }
                )
                
                if read_response.status_code != 200:
                    return f"Error reading data: {read_response.text}"
                
                read_data = read_response.json()
                
                # Step 4: Return structured data for analysis
                return json.dumps({
                    "query": query,
                    "file_path": file_path,
                    "relevant_sheet": relevant_sheet,
                    "file_structure": {
                        "total_sheets": info_data.get("total_sheets"),
                        "all_sheets": [s.get("sheet_name") for s in sheets]
                    },
                    "data": read_data,
                    "note": "This data was extracted based on the query. Analyze it with engineering knowledge to answer the question. You can read more rows or other sheets if needed."
                }, indent=2)
                
        except httpx.ConnectError:
            return f"Error: Cannot connect to desktop agent at {AGENT_API_URL}. Make sure the agent service is running."
        except Exception as e:
            return f"Error extracting relevant data: {str(e)}"
    
    @tool
    def lookup_building_code(clause_reference: str, query: Optional[str] = None) -> str:
        """
        Look up building code information using the RAG system.
        This tool queries the building code database to find actual code text for clauses.
        
        Use this after extracting code references from Excel to get the actual building code text.
        
        Args:
            clause_reference: Building code clause reference (e.g., "7.5.12", "CSA O86-19 Clause 7.5.12")
            query: Optional natural language query to help find relevant code sections
        
        Returns:
            Building code text and relevant clauses from the code database
        """
        try:
            # Import RAG retrieval functions
            from nodes.DBRetrieval.KGdb.retrievers import make_code_hybrid_retriever
            from config.llm_instances import emb
            
            # Build query - prioritize clause number if found
            import re
            clause_match = re.search(r'(\d+(?:\.\d+)*(?:\.\d+)?)', clause_reference)
            if clause_match:
                clause_num = clause_match.group(1)
                search_query = f"clause {clause_num}"
                if query:
                    search_query = f"{search_query} {query}"
            else:
                search_query = query or clause_reference
            
            # Query building code database
            code_retriever = make_code_hybrid_retriever()
            code_docs = code_retriever(search_query, k=5)
            
            if not code_docs:
                return f"No building code information found for: {clause_reference}"
            
            # Format results
            results = []
            for doc in code_docs:
                metadata = doc.metadata if hasattr(doc, 'metadata') else {}
                results.append({
                    "code": metadata.get("filename", "Unknown"),
                    "page": metadata.get("page", "N/A"),
                    "text": doc.page_content[:1000],  # Truncate for readability
                    "source": metadata.get("source", "Unknown")
                })
            
            return json.dumps({
                "query": search_query,
                "clause_reference": clause_reference,
                "results": results,
                "count": len(results)
            }, indent=2)
        except Exception as e:
            return f"Error looking up building code: {str(e)}"
    
    return [
        # File operations (work with any files)
        list_desktop_files,
        get_excel_file_info,
        read_desktop_excel,  # Enhanced: Now includes formulas, code refs, and structured context
        extract_relevant_data,  # Intelligent extraction tool
        lookup_building_code,  # Look up building codes via RAG
        # Sync operations (work with configured projects)
        list_excel_projects,
        read_excel_data,
        get_sync_agent_status,
        sync_excel_to_platform,
        get_sync_history
    ]


def create_excel_kb_agent(state: DesktopAgentState):
    """
    Create Excel knowledge base agent as a deep agent for multi-step planning.
    Uses create_deep_agent for intelligent planning and on-demand data extraction.
    Tools have access to state via closure.
    """
    # Create tools with state closure
    tools = _create_excel_tools(state)
    
    system_prompt = """You are an Excel knowledge base assistant with ENGINEERING EXPERTISE.
You help engineers answer questions about Excel files by intelligently extracting and analyzing data on-demand.

IMPORTANT ARCHITECTURE:
- You run on the cloud backend and CANNOT directly access files on the user's computer
- The Desktop Agent (Excel Sync Agent) runs locally on the user's machine and has access to their files
- All file access must go through the desktop agent API
- You are a DEEP AGENT with planning capabilities - use them to extract only relevant data

🚨 CRITICAL RULE - READ THIS FIRST:
- For ANY query about Excel file contents, structure, or data, you MUST ONLY use FILE OPERATIONS tools
- NEVER call sync tools (list_excel_projects, read_excel_data, get_sync_agent_status, sync_excel_to_platform, get_sync_history) for file content queries
- Sync tools are ONLY for queries explicitly about "synced projects" or "syncing functionality"
- If you call sync tools for a file content query, you are making a MISTAKE

ENGINEERING KNOWLEDGE:
- Beams: Structural members that carry loads (look for: beam name, span, load, moment, capacity, utilization)
- Columns: Vertical structural members (look for: column name, load, capacity, slenderness)
- Capacity: Maximum load/moment a member can carry (look for: capacity, allowable, design strength, Pn, Mn)
- Utilization: Ratio of applied load to capacity (look for: utilization, ratio, U, safety factor)
- Concerns: High utilization (>0.9), low safety factors (<1.0), errors, warnings, failures
- Structural design: Look for utilization ratios, safety factors, pass/fail indicators, design checks

YOUR CAPABILITIES:
FILE OPERATIONS (work with any files in allowed directories) - USE THESE FOR MOST QUERIES:
- list_desktop_files(directory) - List files and directories on user's machine (only if you need to find a file)
- get_excel_file_info(file_path) - Get Excel file structure (sheets, columns, dimensions) - USE THIS FIRST to understand file structure
- read_desktop_excel(file_path, sheet_name, max_rows, include_formulas, include_code_refs) - Read data with formulas, code references, and structured context
  * Returns: cell values, formulas, building code references, and label-value pairs for context
  * The "structured_context" field shows label-value relationships (e.g., "Dead Load" = "2" kPa)
  * Use this to understand what values mean and how they relate to labels
- extract_relevant_data(file_path, query) - Intelligently extract only data needed for a query
- lookup_building_code(clause_reference, query) - Look up actual building code text for clauses (e.g., "7.5.12" or "CSA O86-19 Clause 7.5.12")

SYNC OPERATIONS (work with configured projects) - ONLY USE IF USER ASKS ABOUT SYNCED PROJECTS:
- list_excel_projects() - List Excel projects configured for syncing (ONLY if user asks about synced projects)
- read_excel_data(project_id) - Read data from a configured project (ONLY if user asks about a specific synced project)
- sync_excel_to_platform(project_id) - Sync configured project to platform (ONLY if user asks to sync)
- get_sync_agent_status() - Check desktop agent status (ONLY if user asks about sync status)
- get_sync_history(limit) - View sync history (ONLY if user asks about sync history)

CRITICAL: For queries about Excel file contents, structure, or data, use FILE OPERATIONS tools, NOT sync operations.
Sync operations are ONLY for queries about synced projects or syncing functionality.

NEVER call these sync tools for file content queries:
- list_excel_projects() - ONLY if user explicitly asks "what projects are synced"
- read_excel_data(project_id) - ONLY if user explicitly mentions a project_id
- get_sync_agent_status() - ONLY if user explicitly asks "is the sync agent running"
- sync_excel_to_platform() - ONLY if user explicitly asks to sync
- get_sync_history() - ONLY if user explicitly asks about sync history

For file content queries, ONLY use:
- get_excel_file_info(file_path) - Get file structure
- read_desktop_excel(file_path, sheet_name, max_rows) - Read data
- list_desktop_files(directory) - Find files (only if needed)

PLANNING WORKFLOW FOR ENGINEERING QUERIES:
1. UNDERSTAND: What engineering question is being asked? What concepts are involved?
2. PLAN: What Excel data is needed? Which sheets? Which columns? How many rows?
3. EXTRACT: Use extract_relevant_data() for complex queries, or read_desktop_excel() for specific data
4. ANALYZE: Apply engineering knowledge to extracted data (identify beams, capacities, concerns)
5. SYNTHESIZE: Answer with engineering context and highlight concerns

EXAMPLE PLANNING:
User: "What beams were designed and what capacity were they at? What should I be concerned about?"

Plan:
- Step 1: Get Excel structure → identify sheets with beam data (likely "Full Building" or similar)
- Step 2: Use extract_relevant_data() with query → intelligently extract beam-related data
- Step 3: Analyze extracted data → identify beam names, capacities, utilization ratios
- Step 4: Identify concerns → high utilization (>0.9), low safety factors, errors
- Step 5: Synthesize answer → "Found 12 beams designed. Capacities range from 45-120 kN. Concerns: Beam-3 has 95% utilization..."

IMPORTANT PLANNING PRINCIPLES:
- Don't read entire files - be selective and extract only what's needed
- Use extract_relevant_data() for complex queries that require understanding what's relevant
- Use read_desktop_excel() for specific, known data needs
- Plan your extraction before reading - understand the structure first
- Iterate if needed: read small sample, analyze, then read more if necessary
- Apply engineering knowledge to filter and analyze data

WORKFLOW FOR SIMPLE QUERIES ABOUT FILE CONTENTS/STRUCTURE:
1. Check conversation history FIRST - if a file path was mentioned previously (like "/Users/.../file.xlsx"), use it!
   - Look for file paths in previous messages
   - If user says "tell me about the Axial sheet" and a file was mentioned before, use that file path
   - DO NOT try to find the file by listing directories - use the path from history
2. If user provides a file path in current query, use it directly - DON'T call list_desktop_files() or sync tools
3. Use get_excel_file_info(file_path) FIRST to understand file structure (sheets, columns, dimensions)
4. Based on the info, determine if you need to read data:
   - If user asks "what info is in this file" or "what is this file for" → get_excel_file_info() is usually ENOUGH
   - If user asks about a specific sheet (e.g., "tell me about the Axial sheet") → read_desktop_excel() for that sheet with max_rows=500
   - If user asks for specific data → use read_desktop_excel() for that specific sheet
   - If user asks for "all cells" or "all information" → Read a COMPREHENSIVE SAMPLE (not every cell):
     * Read first 200-500 rows from each major sheet (use max_rows=500 for important sheets)
     * Summarize the structure and key data patterns
     * Explain that you're providing a comprehensive overview, not every single cell
     * DO NOT try to read every sheet individually - batch your approach
5. STOP and answer after you have the information - don't call additional tools unnecessarily
6. DO NOT call sync tools EVER for file content queries - they are completely unnecessary
7. DO NOT call list_desktop_files() if you already have a file path from conversation history

WORKFLOW FOR BUILDING CODE AND DESIGN CHECKS QUERIES:
1. Read Excel data using read_desktop_excel(file_path, include_formulas=True, include_code_refs=True)
   - This returns: values, formulas, code references, and structured context (label-value pairs)
2. Use the "structured_context" field to understand relationships:
   - Labels like "Dead Load", "Live Load", "Axial Load (Pn)" are paired with their values
   - Formulas show how values are calculated
   - Code references show which building code clauses are used
3. For each code reference found, use lookup_building_code(clause_reference) to get actual code text
4. Compare Excel formulas against building code requirements
5. Synthesize answer with:
   - Design checks identified from Excel structure and labels
   - Building code clauses referenced (from code_references field)
   - Actual building code text for each clause
   - Verification of formulas against code requirements
   - Explanation of what each value means using the structured context

WORKFLOW FOR COMPLEX ENGINEERING QUERIES:
1. Understand the engineering question semantically
2. Use extract_relevant_data() to get only what's needed
3. Analyze extracted data with engineering knowledge
4. Synthesize answer with context and concerns

CRITICAL EFFICIENCY RULES:
- ALWAYS use FULL file paths when you know them - don't navigate directory by directory
- If user provides a path like "/Users/jameshinsperger/Desktop/Desktop - MacBook Pro (2)/Sidian/Vibeeng/Excel Templates/file.xlsx", use it directly
- Only use list_desktop_files() to explore when you don't know the exact location
- After finding a file, use its FULL path for all subsequent operations
- Don't navigate step-by-step through directories - use full paths to go directly to files

STOPPING RULES (CRITICAL - FOLLOW THESE):
- For "what info is in this file" or "what is this file for" or "tell me what is in" queries:
  1. Call get_excel_file_info(file_path) ONCE
  2. Analyze the response (sheets, columns, structure)
  3. STOP IMMEDIATELY and provide your answer - DO NOT call additional tools
  4. The file structure is sufficient to answer "what info is in this file"
  5. DO NOT call read_desktop_excel() unless user explicitly asks for data values
  6. After calling get_excel_file_info(), you have ENOUGH information - STOP and answer

- For "all cells" or "all information" queries:
  1. Call get_excel_file_info(file_path) FIRST to see all sheets
  2. Identify the most important sheets (usually 2-4 sheets max)
  3. Read comprehensive samples from those sheets (max_rows=500 for each)
  4. MAXIMUM 5 tool calls total: 1 info + up to 4 sheet reads
  5. After reading samples, STOP and provide a comprehensive summary
  6. Explain that you've provided a comprehensive overview of the file structure and key data

- DO NOT call sync tools (list_excel_projects, read_excel_data, get_sync_agent_status) unless user explicitly asks about syncing
- DO NOT read every single sheet - be strategic and read the most important ones
- MAXIMUM 5 tool calls for "all information" queries - read samples, not every cell

HANDLING "ALL CELLS" OR "ALL INFORMATION" REQUESTS:
- When user asks for "all cells" or "all information", they want a COMPREHENSIVE overview, not literally every cell
- Strategy:
  1. Get file structure first (get_excel_file_info)
  2. Identify the most important sheets (usually 2-4 sheets)
  3. Read comprehensive samples from those sheets (max_rows=500 for each)
  4. Provide a structured summary of:
     * File purpose and structure
     * Key sheets and their contents
     * Sample data from each important sheet
     * Data patterns and key information
  5. Explain that you're providing a comprehensive overview based on samples
  6. MAXIMUM 5 tool calls: 1 info + up to 4 sheet reads
  7. DO NOT try to read every sheet - be strategic

UNDERSTANDING EXCEL DATA - COHESIVE VIEW:
When read_desktop_excel() returns data, it provides a complete picture:

1. "data": Array of rows with cell values (the actual data)
   - Each row is a dictionary with column headers as keys
   - Values are the calculated results

2. "formulas": Simple map of cell addresses to formula strings
   - Example: {"B10": "=B5*B6", "C15": "=SUM(B10:B12)"}
   - Shows what formula is in each cell

3. "formulas_detailed": Detailed formula information with dependencies
   - Each entry includes:
     * "cell": Cell address (e.g., "B10")
     * "formula": Formula string (e.g., "=B5*B6")
     * "dependencies": List of cells this formula references (e.g., ["B5", "B6"])
     * "calculated_value": The result of the formula
   - Use this to understand calculation chains and relationships

4. "formula_dependencies_summary": Overview of all cells referenced by formulas
   - Shows which cells are inputs to calculations
   - Helps identify key data points

5. "code_references": Building code clauses found in cells/comments
   - Each entry shows: cell, clause number, reference text
   - Links Excel calculations to building code requirements

6. "structured_context": OPTIONAL label-value pairs and horizontal relationships (may be empty)
   - Two types of patterns detected:
     * "vertical": Label in left column, value in right column (e.g., "Dead Load" in A5, 2 in B5)
     * "horizontal": Related cells in same row across columns
       Example: ["Load Duration Factor,", "KD", "=", 1, "Cl. 5.3.2.3: ..."]
       This shows: label, variable name, equals/value, actual value, comment
   - If empty, infer relationships from data structure and formulas
   - Different Excel files have different structures - this is flexible

HOW TO USE THIS FOR COHESIVE UNDERSTANDING:
1. Start with "data" to see actual values
2. Use "formulas_detailed" to understand:
   - How values are calculated
   - What cells feed into each calculation (dependencies)
   - Calculation chains (e.g., B5*B6 → B10, then B10 used in C15)
3. Use "formula_dependencies_summary" to identify key input cells
4. Cross-reference "code_references" with formulas to see design basis
5. Use "structured_context" to understand relationships:
   - "vertical" patterns: Label-value pairs in adjacent columns
   - "horizontal" patterns: Related info in same row (label, variable, value, comment)
   - Example horizontal: {"label": "Load Duration Factor", "variable": "KD", "value": 1, "comment": "Cl. 5.3.2.3: ..."}
   - If structured_context is empty, infer relationships from raw data and formulas

EXAMPLE COHESIVE ANALYSIS:
- Cell B5 = 2 (from "data")
- Cell B6 = 3.25 (from "data")
- Cell B10 formula = "=B5*B6" (from "formulas_detailed")
- Cell B10 dependencies = ["B5", "B6"] (from "formulas_detailed")
- Cell B10 calculated_value = 6.5 (from "formulas_detailed")
- Code reference in B10 comment: "CSA O86-19 Clause 7.5.12" (from "code_references")

This tells you: B10 calculates 2 × 3.25 = 6.5, and this calculation is based on CSA O86-19 Clause 7.5.12.

IMPORTANT:
- For file operations, you can access any files in allowed directories (typically Desktop, Documents)
- For sync operations, files must be pre-configured in the desktop agent
- Always plan before extracting - don't read everything
- The desktop agent must be running for any operations to work
- Be helpful and provide clear, structured answers with engineering context
- For simple "what info is in this file" queries: 1 tool call is usually enough (get_excel_file_info)
- For "all information" queries: Maximum 5 tool calls - read comprehensive samples, not every cell
- Use structured_context from read_desktop_excel() to understand label-value relationships
"""
    
    # Use deep agent for planning capabilities
    # Use llm_synthesis (OpenAI/Gemini) instead of llm_fast (Groq) because Groq doesn't support bind_tools()
    # deepagents requires tool binding which Groq doesn't support
    agent = create_deep_agent(
        model=llm_synthesis,  # Use synthesis model (OpenAI/Gemini) which supports tool binding
        tools=tools,
        system_prompt=system_prompt,
        backend=lambda rt: StateBackend(rt)  # Ephemeral - clears after query completes
    )
    
    return agent


def node_excel_kb_agent(state: DesktopAgentState) -> Dict[str, Any]:
    """
    Excel KB Agent Node (Deep Agent)
    Uses create_deep_agent for multi-step planning and intelligent data extraction.
    All Excel file access goes through the Excel Sync Agent which runs locally on user's machine.
    """
    import time
    t_start = time.time()
    log_route.info(">>> EXCEL KB AGENT START")
    
    try:
        # Create agent with state (tools access state via closure)
        agent = create_excel_kb_agent(state)
        
        # Invoke agent with user query
        # Pass max_iterations in config to prevent infinite loops
        # LangGraph agents support this to limit tool call iterations
        # Detect if user is asking for "all" information - increase limit but guide agent to be efficient
        user_query_lower = state.user_query.lower()
        is_all_info_query = any(phrase in user_query_lower for phrase in [
            "all cells", "all information", "all data", "every cell", "entire file", "complete file"
        ])
        
        # Deep agents make many internal LLM calls (not just tool calls), so we need higher limits
        # Each tool call + processing = multiple LLM iterations
        # For "what is in this file" queries, agent should stop after get_excel_file_info, but
        # it still needs headroom for processing the response
        recursion_limit = 25 if is_all_info_query else 20  # Increased from 20/15
        
        # Build messages with conversation history for context
        # This helps the agent understand follow-up queries like "tell me more about the Axial sheet"
        agent_messages = []
        if state.messages:
            # Include recent conversation history (last 4 messages = 2 exchanges)
            recent_messages = state.messages[-4:] if len(state.messages) > 4 else state.messages
            for msg in recent_messages:
                agent_messages.append({
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                })
        else:
            # No history, just use current query
            agent_messages.append({"role": "user", "content": state.user_query})
        
        # Always add current query as last message
        if not agent_messages or agent_messages[-1].get("content") != state.user_query:
            agent_messages.append({"role": "user", "content": state.user_query})
        
        log_route.info(f"📝 Passing {len(agent_messages)} messages to agent (including conversation history)")
        
        response = agent.invoke(
            {"messages": agent_messages},
            config={"recursion_limit": recursion_limit}
        )
        
        # Extract answer from agent response
        # Deep agent returns dict with "messages" key containing list of message objects
        # Gemini models return content as list format: [{'type': 'text', 'text': '...'}]
        from nodes.DBRetrieval.SQLdb.answer import extract_text_from_content
        from langchain_core.messages import ToolMessage, AIMessage, HumanMessage
        
        if isinstance(response, dict) and "messages" in response:
            messages = response["messages"]
            
            # LOG AGENT'S THINKING AND TOOL CALLS
            log_route.info(f"🧠 AGENT THINKING - Total messages: {len(messages)}")
            for i, msg in enumerate(messages):
                # Handle both dict and object message formats
                if isinstance(msg, dict):
                    msg_type = msg.get('type', 'unknown')
                    content = msg.get('content', '')
                    
                    if msg_type == 'human':
                        log_route.info(f"   [{i}] USER: {str(content)[:200]}...")
                    elif msg_type == 'ai':
                        # Check for tool calls in dict format
                        tool_calls = msg.get('tool_calls', [])
                        if tool_calls:
                            log_route.info(f"   [{i}] AGENT DECISION: Calling {len(tool_calls)} tool(s)")
                            for tool_call in tool_calls:
                                tool_name = tool_call.get('name', tool_call.get('id', 'unknown'))
                                tool_args = tool_call.get('args', {})
                                log_route.info(f"      🔧 Tool: {tool_name}")
                                for key, value in tool_args.items():
                                    val_str = str(value)
                                    if len(val_str) > 100:
                                        val_str = val_str[:100] + "..."
                                    log_route.info(f"         - {key}: {val_str}")
                        else:
                            # Agent's reasoning
                            content_str = extract_text_from_content(content) if content else ""
                            if content_str:
                                log_route.info(f"   [{i}] AGENT THINKING: {content_str[:300]}...")
                    elif msg_type == 'tool':
                        tool_result = str(content)
                        if len(tool_result) > 200:
                            tool_result = tool_result[:200] + "..."
                        log_route.info(f"   [{i}] TOOL RESULT: {tool_result}")
                    else:
                        log_route.info(f"   [{i}] {msg_type}: {str(msg)[:200]}...")
                else:
                    # Object format
                    msg_type = type(msg).__name__
                    
                    if isinstance(msg, HumanMessage):
                        content = getattr(msg, 'content', '')
                        log_route.info(f"   [{i}] USER: {str(content)[:200]}...")
                    elif isinstance(msg, AIMessage):
                        # Check if this message has tool calls
                        tool_calls = getattr(msg, 'tool_calls', None) or []
                        if tool_calls:
                            log_route.info(f"   [{i}] AGENT DECISION: Calling {len(tool_calls)} tool(s)")
                            for tool_call in tool_calls:
                                if isinstance(tool_call, dict):
                                    tool_name = tool_call.get('name', 'unknown')
                                    tool_args = tool_call.get('args', {})
                                else:
                                    tool_name = getattr(tool_call, 'name', 'unknown')
                                    tool_args = getattr(tool_call, 'args', {})
                                log_route.info(f"      🔧 Tool: {tool_name}")
                                for key, value in tool_args.items():
                                    val_str = str(value)
                                    if len(val_str) > 100:
                                        val_str = val_str[:100] + "..."
                                    log_route.info(f"         - {key}: {val_str}")
                        else:
                            # Agent's reasoning/thinking
                            content = getattr(msg, 'content', '')
                            content_str = extract_text_from_content(content) if content else ""
                            if content_str:
                                log_route.info(f"   [{i}] AGENT THINKING: {content_str[:300]}...")
                    elif isinstance(msg, ToolMessage):
                        # Tool result
                        tool_result = getattr(msg, 'content', '')
                        if isinstance(tool_result, str) and len(tool_result) > 200:
                            tool_result = tool_result[:200] + "..."
                        log_route.info(f"   [{i}] TOOL RESULT: {tool_result}")
                    else:
                        # Other message types
                        content = str(msg)[:200]
                        log_route.info(f"   [{i}] {msg_type}: {content}...")
            
            if messages and len(messages) > 0:
                last_message = messages[-1]
                # Handle both dict and object message formats
                if isinstance(last_message, dict):
                    content = last_message.get("content", "No response")
                else:
                    content = getattr(last_message, "content", "No response")
                
                # Extract text from content (handles Gemini list format)
                answer = extract_text_from_content(content)
            else:
                answer = "No response from agent"
        else:
            # Fallback: try to extract from string or other formats
            answer = str(response) if response else "No response"
            log_route.warning(f"⚠️ Unexpected response format: {type(response)}")
        
        log_route.info(f"✅ Excel KB Agent completed")
        log_route.info(f"📝 Answer length: {len(answer) if answer else 0} chars")
        log_route.info(f"📝 Answer preview: {answer[:200] if answer else 'None'}...")
        
        t_elapsed = time.time() - t_start
        log_route.info(f"<<< EXCEL KB AGENT DONE in {t_elapsed:.2f}s")
        
        return {
            "desktop_result": answer,
            "desktop_citations": []  # Could add file references here
        }
        
    except Exception as e:
        log_route.error(f"❌ Excel KB Agent failed: {e}")
        import traceback
        traceback.print_exc()
        
        t_elapsed = time.time() - t_start
        log_route.info(f"<<< EXCEL KB AGENT DONE (with error) in {t_elapsed:.2f}s")
        
        return {
            "desktop_result": f"Error: {str(e)}",
            "desktop_citations": []
        }
