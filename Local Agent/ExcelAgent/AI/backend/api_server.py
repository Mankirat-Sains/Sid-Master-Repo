#!/usr/bin/env python3
"""
FastAPI Server for Mantle Excel Add-in Backend
Provides intelligent engineering assistance for Excel
"""

import logging
import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from trainexcel root
# .env is in trainexcel root: backend/api_server.py -> backend/ -> trainexcel/
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Mantle Excel Backend",
    description="Intelligent backend for Mantle Excel Add-in",
    version="1.0.0"
)

# Enable CORS for Excel Add-in
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class ExcelContext(BaseModel):
    workbookName: str
    sheetName: str
    selectedRange: Dict[str, Any] = {}  # Made optional with default
    tables: List[Dict[str, Any]] = []
    usedRange: Dict[str, Any] = {}  # Made optional with default
    timestamp: str
    labelMap: Optional[Dict[str, str]] = None  # Map of labels to cell addresses
    sectionHeaders: Optional[Dict[str, str]] = None  # Section headers
    detectedMaterial: Optional[str] = None  # Auto-detected material type

class ExcelCommandRequest(BaseModel):
    command: str
    context: ExcelContext
    capabilities: List[str]

class ExcelUpdate(BaseModel):
    address: str
    value: Any
    sheet: Optional[str] = None
    formula: Optional[str] = None
    format: Optional[Dict[str, Any]] = None

class ExcelValidation(BaseModel):
    check: str
    status: str
    passed: bool
    value: Optional[str] = None
    limit: Optional[str] = None
    ratio: Optional[float] = None

class ExcelCommandResponse(BaseModel):
    action: str  # "update_value", "update_multiple", "message", "error"
    updates: Optional[List[ExcelUpdate]] = None
    message: str
    reasoning: Optional[str] = None
    calculations: Optional[List[Dict[str, Any]]] = None
    validations: Optional[List[ExcelValidation]] = None
    suggestions: Optional[List[str]] = None
    # Additional fields for update_value action (used by frontend)
    property: Optional[str] = None  # Property name for label map lookup
    target: Optional[str] = None    # Cell address
    value: Optional[Any] = None     # Value to set

# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Mantle Excel Backend",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "excel_command": "/api/excel/command",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "openai_configured": bool(os.getenv("OPENAI_API_KEY"))
    }

@app.post("/api/excel/analyze-layout")
async def analyze_layout_handler(request: dict):
    """
    Use LLM to analyze Excel sheet layout structure
    Returns: Layout pattern (which columns contain labels, symbols, values, units)
    """
    try:
        sample_data = request.get("sampleData", "")
        sheet_name = request.get("sheetName", "Sheet")
        workbook_name = request.get("workbookName", "Unknown")
        
        logger.info(f"📐 Analyzing layout for {workbook_name}/{sheet_name}")
        
        from openai import OpenAI
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            return {
                "layout_pattern": "unknown",
                "label_column": "B",
                "symbol_column": "D",
                "value_column": "G",
                "error": "OpenAI API key not set"
            }
        
        try:
            import httpx
            http_client = httpx.Client(timeout=60.0)
            openai_client = OpenAI(
                api_key=openai_key,
                http_client=http_client,
                timeout=60.0,
                max_retries=2
            )
        except Exception as e:
            logger.error(f"Failed to create OpenAI client: {e}")
            return {"layout_pattern": "unknown", "error": str(e)}
        
        prompt = f"""Analyze the LAYOUT STRUCTURE of this engineering spreadsheet.

Workbook: {workbook_name}
Sheet: {sheet_name}

Sample Data (first 50 rows):
{sample_data[:5000]}  # Limit to avoid token limits

Questions:
1. What column contains parameter LABELS (descriptive text like "Treatment factor", "Effective Length")?
2. What column contains SYMBOLS/NOTATION (short codes like "K_T", "Led", "E_os")?
3. What column contains VALUES (numeric inputs/outputs)?
4. What column contains UNITS (e.g., "MPa", "mm", "kN")?
5. Are labels in the SAME ROW as their values, or are they positioned differently?
6. Are there multiple value columns (e.g., Imperial/Metric)?

Return JSON:
{{
  "layout_pattern": "same-row" | "multi-row" | "header-row" | "unknown",
  "label_column": "B",
  "symbol_column": "D",
  "value_column": "G",
  "unit_column": "H",
  "label_position": "same-row" | "above-row" | "header-row",
  "has_multiple_value_columns": false,
  "description": "Brief description of the layout"
}}

If labels can be in multiple positions, specify an array:
{{
  "label_columns": ["B"],
  "label_positions": ["same-row", "above-row"]
}}

Return ONLY valid JSON."""
        
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert at analyzing Excel spreadsheet layouts. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=500
        )
        
        content = response.choices[0].message.content.strip()
        
        # Strip markdown if present
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        
        result = json.loads(content.strip())
        logger.info(f"✅ Layout analysis complete: {result.get('layout_pattern')}")
        
        return result
        
    except Exception as e:
        logger.error(f"Layout analysis error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "layout_pattern": "unknown",
            "error": str(e)
        }

@app.post("/api/excel/detect-legend")
async def detect_legend_handler(request: dict):
    """
    Intelligently detect and classify legend from Excel sheet
    Uses AI to understand any legend format without hardcoding
    """
    try:
        from agents.building_code_rag import get_building_code_rag
        import json
        
        legend_cells = request.get("legendCells", [])
        sheet_name = request.get("sheetName", "Sheet1")
        
        if not legend_cells:
            return {"legendFound": False, "colorMappings": {}}
        
        # Use OpenAI to classify legend intelligently
        from openai import OpenAI
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            try:
                import httpx
                http_client = httpx.Client(timeout=60.0)
                openai_client = OpenAI(
                    api_key=openai_key,
                    http_client=http_client,
                    timeout=60.0,
                    max_retries=2
                )
            except Exception as e:
                logger.error(f"Failed to create OpenAI client: {e}")
                openai_client = None
        else:
            openai_client = None
            
        if openai_client:
            prompt = f"""You are analyzing a spreadsheet legend to understand what colors mean.

Sheet: {sheet_name}
Legend cells found:
{json.dumps(legend_cells, indent=2)}

Your task: Classify each legend item into semantic categories:
- user_input: Cells users should modify (input parameters)
- calculated_output: Calculated results/formulas that display outputs
- calculation: Intermediate calculations
- override: Manually overridden values
- status_indicator: Pass/fail, warning indicators
- capacity_ratio: Utilization ratios (Mf/Mr, Vf/Vr, etc.)

Return ONLY valid JSON:
{{
  "legendFound": true,
  "colorMappings": {{
    "color_hex": {{
      "category": "user_input|calculated_output|calculation|override|status_indicator|capacity_ratio",
      "description": "what this color means",
      "confidence": 0.95
    }}
  }},
  "cellClassifications": {{
    "cell_address": "category"
  }}
}}

CRITICAL: Return valid JSON only. No markdown."""
            
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing spreadsheet legends. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content.strip()
            # Strip markdown if present
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            
            result = json.loads(content)
            return result
        
        return {"legendFound": False, "colorMappings": {}}
        
    except Exception as e:
        logger.error(f"Legend detection error: {e}")
        return {"legendFound": False, "colorMappings": {}, "error": str(e)}

@app.post("/api/excel/parse-labels")
async def parse_labels_handler(request: dict):
    """
    Use LLM to resolve ambiguous label-to-value mappings
    Only called when heuristics fail for complex layouts
    """
    try:
        ambiguous_cells = request.get("ambiguousCells", [])
        layout_structure = request.get("layoutStructure", {})
        sheet_name = request.get("sheetName", "Sheet")
        workbook_name = request.get("workbookName", "Unknown")
        
        if not ambiguous_cells:
            return {"mappings": []}
        
        logger.info(f"🧠 Parsing {len(ambiguous_cells)} ambiguous label mappings via LLM")
        
        from openai import OpenAI
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            return {"mappings": [], "error": "OpenAI API key not set"}
        
        try:
            import httpx
            http_client = httpx.Client(timeout=60.0)
            openai_client = OpenAI(
                api_key=openai_key,
                http_client=http_client,
                timeout=60.0,
                max_retries=2
            )
        except Exception as e:
            logger.error(f"Failed to create OpenAI client: {e}")
            return {"mappings": [], "error": str(e)}
        
        # Build prompt with all ambiguous cells and their neighborhoods
        cells_context = []
        for cell_info in ambiguous_cells[:20]:  # Limit to 20 to avoid token limits
            cell_addr = cell_info.get("cell", "")
            neighborhood = cell_info.get("neighborhood", {})
            candidates = cell_info.get("candidates", [])
            
            neighborhood_str = "\n".join([f"  {pos}: {value}" for pos, value in list(sorted(neighborhood.items())[:10])])
            candidates_str = ", ".join(candidates) if candidates else "none"
            
            cells_context.append(f"""
Cell {cell_addr}:
  Value: {cell_info.get('value', 'unknown')}
  Neighborhood cells:
{neighborhood_str}
  Candidate labels found: {candidates_str}
""")
        
        prompt = f"""You are analyzing an engineering spreadsheet to map parameter labels to their value cells.

Workbook: {workbook_name}
Sheet: {sheet_name}
Layout Pattern: {layout_structure.get('layout_pattern', 'unknown')}
Label Column: {layout_structure.get('label_column', 'unknown')}
Value Column: {layout_structure.get('value_column', 'unknown')}

Ambiguous cells that need label resolution:
{chr(10).join(cells_context)}

For each cell, determine:
1. What is the parameter name/label for this value cell?
2. What is the symbol (if visible)?
3. What are the units (if visible)?

Look for labels in:
- Same row, to the left
- One row above
- Column headers above
- Nearby cells in the neighborhood

Return ONLY valid JSON array:
[
  {{
    "cell": "G19",
    "label": "Tributary width",
    "symbol": "W_t",
    "unit": "m",
    "confidence": 0.95
  }},
  ...
]

If no label can be determined, set confidence < 0.5."""
        
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert at understanding engineering spreadsheet structures. Return only valid JSON arrays."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=1500
        )
        
        content = response.choices[0].message.content.strip()
        
        # Strip markdown if present
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        
        mappings = json.loads(content.strip())
        logger.info(f"✅ LLM resolved {len(mappings)} label mappings")
        
        return {"mappings": mappings}
        
    except Exception as e:
        logger.error(f"Label parsing error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"mappings": [], "error": str(e)}

@app.post("/api/excel/command", response_model=ExcelCommandResponse)
async def excel_command_handler(request: ExcelCommandRequest):
    """
    Handle Excel add-in commands with structured responses
    
    This endpoint receives rich Excel context and returns
    structured actions for the add-in to execute
    """
    try:
        logger.info(f"📊 Excel Command: {request.command}")
        logger.info(f"📁 Workbook: {request.context.workbookName}")
        logger.info(f"📄 Sheet: {request.context.sheetName}")
        
        # Import the orchestrator
        from agents.orchestrator import process_excel_command
        
        # Process the command
        logger.info(f"📋 Context received - LabelMap size: {len(request.context.labelMap or {})}")
        logger.info(f"📋 Sheet name: {request.context.sheetName}")
        logger.info(f"📋 Detected material: {request.context.detectedMaterial}")
        
        result = await process_excel_command(
            command=request.command,
            context=request.context.dict(),
            capabilities=request.capabilities
        )
        
        logger.info(f"✅ Action: {result.get('action')}")
        logger.info(f"📤 Response structure: {list(result.keys())}")
        
        # Log response details
        if result.get('action') == 'update_value':
            logger.info(f"   Property: {result.get('property', 'MISSING')}")
            logger.info(f"   Target: {result.get('target', 'MISSING')}")
            logger.info(f"   Value: {result.get('value', 'MISSING')}")
        elif result.get('action') == 'message':
            message_preview = str(result.get('message', 'MISSING'))[:200]
            logger.info(f"   Message: {message_preview}...")
        
        # Validate response has required fields
        if 'message' not in result:
            logger.warning("⚠️ Response missing 'message' field - adding default")
            result['message'] = result.get('reasoning', 'Command processed')
        
        logger.info(f"📦 Final response: {json.dumps(result, default=str)[:500]}")
        
        return ExcelCommandResponse(**result)
        
    except Exception as e:
        logger.error(f"❌ Error processing command: {e}")
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Traceback: {error_trace}")
        return ExcelCommandResponse(
            action="error",
            message=f"Error: {str(e)}\n\nCheck backend logs for details."
        )

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    # Check environment setup
    if not os.getenv("OPENAI_API_KEY"):
        logger.warning("⚠️ OPENAI_API_KEY not set. AI features will be limited.")
        print("\n💡 Set OPENAI_API_KEY in .env file for full functionality")
    
    port = int(os.getenv("PORT", 8000))
    
    print("\n" + "="*60)
    print("🚀 MANTLE EXCEL BACKEND SERVER")
    print("="*60)
    print(f"📡 Server: http://localhost:{port}")
    print(f"📊 Excel endpoint: http://localhost:{port}/api/excel/command")
    print(f"💚 Health check: http://localhost:{port}/health")
    print("="*60 + "\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )

