#!/usr/bin/env python3
"""
Intelligent Orchestrator for Excel Add-in
Processes commands and returns structured Excel actions
"""

import json
import logging
import os
import re
from typing import Dict, Any, List, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)

# Initialize OpenAI client
openai_client = None
try:
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        # Use explicit initialization to avoid proxy/environment issues
        # httpx_client parameter ensures we control the HTTP client
        import httpx
        http_client = httpx.Client(timeout=60.0)
        openai_client = OpenAI(
            api_key=api_key,
            http_client=http_client,
            timeout=60.0,
            max_retries=2
        )
        logger.info("✅ OpenAI client initialized")
    else:
        logger.warning("⚠️ OPENAI_API_KEY not set - AI features disabled")
except Exception as e:
    logger.error(f"⚠️ Failed to initialize OpenAI client: {e}")
    openai_client = None

# Initialize Building Code RAG
CODE_RAG_AVAILABLE = False
# Simple in-memory session store (per workbook/sheet)
SESSION_MEMORY: Dict[str, Any] = {}
# Lightweight memory for code follow-ups (module-level to avoid global errors)
LAST_CODE_RESULTS: List[Dict[str, Any]] = []
LAST_CODE_QUERY: str = ""
try:
    from .building_code_rag import get_building_code_rag
    _code_rag = None
    CODE_RAG_AVAILABLE = True
    logger.info("✅ Building Code RAG available")
except Exception as e:
    logger.warning(f"⚠️ Building Code RAG not available: {e}")

# Default LLM model for synthesis
DEFAULT_MODEL = "gpt-4o-mini"

# ============================================================================
# ENGINEERING PROMPTS
# ============================================================================

ROUTER_PROMPT = """You are an intelligent router for Excel engineering commands. Classify the user's command into ONE of these categories:

1. "building_code" - Questions about applicable building codes, code clauses, CSA standards, OBC requirements, code references
   Examples: "What is the applicable building code?", "Tell me what code relates to this sheet", "Find code for timber design"
   
2. "update_value" - Commands to update a specific cell/property value
   Examples: "Update tributary width to 15m", "Change span to 10m", "Set load to 50 kN"
   
3. "sheet_analysis" - Requests to understand, analyze, or explain what's in the sheet
   Examples: "What's on this sheet?", "Explain this sheet", "What parameters are here?", "Tell me about this design"
   
4. "formula_verification" - Requests to verify, check, track, or validate an Excel formula against building codes
   Examples: "Verify this formula", "Check if this equation is correct", "Track this formula", "Compare this to building code", "Is this formula correct?"
   
5. "calculation" - Requests for engineering calculations or design operations
   Examples: "Design me a beam", "Calculate the capacity", "Perform a design check"
   
6. "query" - General informational queries about the spreadsheet
   Examples: "What is the span?", "Show me the loads", "What are the material properties?"

Return ONLY a single word: building_code|update_value|sheet_analysis|formula_verification|calculation|query

Command: "{command}"
"""

COMMAND_ANALYSIS_PROMPT = """You are an expert structural engineer assistant analyzing Excel commands.

User Command: "{command}"

Excel Context:
- Workbook: {workbook}
- Sheet: {sheet}
- Sample Data:
{sample_data}

Analyze this command and return a JSON response with:
{{
  "intent": "update_value|calculate|design|validate|query",
  "engineering_element": "beam|column|wall|slab|foundation|general",
  "parameters": {{
    "property": "span|load|strength|etc",
    "value": number or null,
    "unit": "m|kN|MPa|etc"
  }},
  "requires_calculation": true|false,
  "target_cells": ["address1", "address2"],
  "reasoning": "brief explanation"
}}

Focus on:
1. What the user wants to do
2. What engineering calculations are needed
3. Which cells should be updated
4. What validations should be performed
"""

CALCULATION_PROMPT = """You are a structural engineering calculator.

Calculation Request: {intent}
Parameters: {parameters}

Perform the engineering calculations and return JSON:
{{
  "calculations": [
    {{
      "type": "moment|shear|deflection|capacity",
      "formula": "mathematical formula used",
      "value": calculated number,
      "unit": "kN⋅m|kN|mm|MPa",
      "cell_address": "where to put this in Excel"
    }}
  ],
  "validations": [
    {{
      "check": "check name",
      "status": "PASS|FAIL|WARNING",
      "passed": true|false,
      "value": current value,
      "limit": code limit,
      "ratio": utilization ratio,
      "code": "AS3600|Eurocode|etc"
    }}
  ],
  "message": "summary for user"
}}

Use standard engineering formulas:
- Moment: M = wL²/8 (uniformly distributed load)
- Shear: V = wL/2
- Deflection: δ = 5wL⁴/384EI
"""

# ============================================================================
# MAIN PROCESSING FUNCTION
# ============================================================================

async def process_excel_command(command: str, context: Dict[str, Any], capabilities: List[str]) -> Dict[str, Any]:
    """
    Process Excel command and return structured actions
    
    Args:
        command: User's natural language command
        context: Excel workbook context
        capabilities: What the add-in can do
    
    Returns:
        Structured response with actions to perform
    """
    
    try:
        logger.info(f"🎯 Processing: {command}")
        logger.info(f"📋 Context keys: {list(context.keys())}")
        logger.info(f"📊 LabelMap size: {len(context.get('labelMap', {}) or {})}")
        
        # STEP 1: Use LLM-based router to classify command type
        route_decision = await intelligent_route_command(command)
        logger.info(f"🛤️ Router decision: {route_decision}")
        
        # STEP 2: Route to appropriate handler based on router decision
        if route_decision == "building_code":
            logger.info("🏗️ Routing to building code handler...")
            result = await handle_building_code_query(command, context)
            logger.info(f"🏗️ Building code result: action={result.get('action')}, message length={len(str(result.get('message', '')))}")
            return result
        
        elif route_decision == "sheet_analysis":
            logger.info("📊 Routing to sheet analysis handler...")
            result = await handle_sheet_analysis(command, context)
            return result
        
        elif route_decision == "formula_verification":
            logger.info("🔍 Routing to formula verification handler...")
            result = await handle_formula_verification(command, context)
            return result
        
        elif route_decision == "update_value":
            logger.info("📝 Routing to update value handler...")
            
            # FIRST: Check if command has explicit cell address (e.g., "update F21 to 10", "set cell F21 = 10")
            import re
            cell_address_pattern = r'\b([A-Z]{1,3}\d{1,7})\b'
            cell_matches = re.findall(cell_address_pattern, command.upper()) or []
            
            if cell_matches:
                # Extract value from command (after 'to', '=' or 'with')
                value_pattern = r'(?:(?:to)|(?:=)|(?:with))\s*([-+]?\d*\.?\d+)'
                value = None
                try:
                    vm = re.search(value_pattern, command.lower())
                    if vm:
                        value = float(vm.group(1))
                except Exception as e:
                    logger.warning(f"Value parse failed for explicit cell: {e}")
                
                if value is not None:
                    target_cell = cell_matches[0]  # Use first cell address found
                    logger.info(f"🎯 Direct cell update detected: {target_cell} = {value}")
                    return {
                        "action": "update_value",
                        "property": None,  # Explicit cell address, no property lookup needed
                        "target": target_cell,
                        "value": value,
                        "updates": [{
                            "address": target_cell,
                            "value": value
                        }],
                        "message": f"Updated cell {target_cell} to {value}",
                        "reasoning": f"Direct cell address update"
                    }
            
            # If no explicit cell address, try simple property pattern before AI
            simple_prop = re.search(r'(?:update|set|change)\s+([a-zA-Z][a-zA-Z\s/_-]{2,}?)\s+(?:to|=)\s*([-+]?\d*\.?\d+)', command or '', re.IGNORECASE)
            if simple_prop:
                prop = simple_prop.group(1).strip()
                try:
                    value = float(simple_prop.group(2))
                except Exception as e:
                    logger.warning(f"Property value parse failed: {e}")
                    value = None
                if value is not None:
                    logger.info(f"🔎 Resolving property '{prop}' via labelMap")
                    target_cell = find_property_cell(prop, context)
                    if target_cell:
                        return {
                            "action": "update_value",
                            "property": prop,
                            "target": target_cell,
                            "value": value,
                            "updates": [{"address": target_cell, "value": value}],
                            "message": f"Updated {prop} to {value}",
                            "reasoning": "Pattern-matched property update"
                        }
            
            # If no explicit cell address, proceed with normal property-based update
            workbook = context.get("workbookName", "Unknown")
            sheet = context.get("sheetName", "Sheet1")
            sample_data = format_sample_data(context.get("usedRange", {}).get("allData", []))
            sheet_type = detect_sheet_type(context)
            
            # Analyze the command to extract parameters
            if openai_client:
                analysis = await analyze_command_with_ai(command, workbook, sheet, sample_data, sheet_type)
            else:
                analysis = analyze_command_fallback(command, context)
            
            logger.info(f"📋 Intent: {analysis.get('intent')}")
            logger.info(f"🏗️ Element: {analysis.get('engineering_element')}")
            logger.info(f"📊 Parameters extracted: {json.dumps(analysis.get('parameters', {}), default=str)}")
            
            result = create_simple_update(analysis, context)
            logger.info(f"📤 Update result keys: {list(result.keys())}")
            return result
        
        elif route_decision == "calculation":
            logger.info("⚙️ Routing to calculation handler...")
            workbook = context.get("workbookName", "Unknown")
            sheet = context.get("sheetName", "Sheet1")
            sample_data = format_sample_data(context.get("usedRange", {}).get("allData", []))
            sheet_type = detect_sheet_type(context)
            
            if openai_client:
                analysis = await analyze_command_with_ai(command, workbook, sheet, sample_data, sheet_type)
            else:
                analysis = analyze_command_fallback(command, context)
            
            result = await perform_calculations(analysis, context, sheet_type)
            return result
        
        else:  # query or default
            logger.info("❓ Routing to general query handler...")
            workbook = context.get("workbookName", "Unknown")
            sheet = context.get("sheetName", "Sheet1")
            sample_data = format_sample_data(context.get("usedRange", {}).get("allData", []))
            sheet_type = detect_sheet_type(context)
            
            if openai_client:
                analysis = await analyze_command_with_ai(command, workbook, sheet, sample_data, sheet_type)
            else:
                analysis = analyze_command_fallback(command, context)
            
            # For queries, return informational response
            result = {
                "action": "message",
                "message": f"I analyzed your query about '{command}'. The sheet '{sheet}' contains engineering design parameters. Would you like me to update a specific value or perform calculations?",
                "reasoning": f"General query about {analysis.get('engineering_element', 'sheet')}"
            }
            return result
        
    except Exception as e:
        logger.error(f"❌ Error processing command: {e}")
        import traceback
        traceback.print_exc()
        return {
            "action": "error",
            "message": f"Error: {str(e)}"
        }

# ============================================================================
# AI-POWERED ROUTING
# ============================================================================

async def intelligent_route_command(command: str) -> str:
    """
    Use LLM to intelligently route commands to appropriate handlers
    Returns: building_code|update_value|sheet_analysis|calculation|query
    """
    if not openai_client:
        # Fallback to keyword-based routing
        command_lower = command.lower()
        # If user references the clicked/selected cell, prefer cell-level analysis/verification
        if any(p in command_lower for p in ["clicked cell", "selected cell", "this cell", "current cell"]):
            if any(p in command_lower for p in ["formula", "equation", "verify", "check", "compare", "validate"]):
                return "formula_verification"
            # Cell-specific explanation
            return "formula_verification"
        # Priority: formula verification first (before building_code, since it might mention both)
        if any(phrase in command_lower for phrase in ["track", "verify", "check", "compare", "validate"]) and \
           any(phrase in command_lower for phrase in ["formula", "equation", "cell", "this"]):
            return "formula_verification"
        elif any(phrase in command_lower for phrase in ["code", "csa", "obc", "clause", "standard", "applicable code"]):
            return "building_code"
        elif any(phrase in command_lower for phrase in ["update", "change", "set", "modify"]):
            return "update_value"
        elif any(phrase in command_lower for phrase in ["what's on", "explain", "tell me about", "what is in", "analyze this"]):
            return "sheet_analysis"
        elif any(phrase in command_lower for phrase in ["verify", "check formula", "track formula", "compare formula", "validate formula", "is this formula correct"]):
            return "formula_verification"
        elif any(phrase in command_lower for phrase in ["calculate", "design", "compute"]):
            return "calculation"
        else:
            return "query"
    
    try:
        # Special-case follow-ups: if user says "more information" or "these clauses", keep it in building_code
        cl = command.lower()
        if any(p in cl for p in ["more information", "these clauses", "expand", "show details"]):
            return "building_code"
        prompt = ROUTER_PROMPT.format(command=command)
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a strict router. Return ONLY one word."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=20
        )
        
        route = response.choices[0].message.content.strip().lower()
        
        # Validate route
        valid_routes = ["building_code", "update_value", "sheet_analysis", "formula_verification", "calculation", "query"]
        if route in valid_routes:
            # If user references clicked/selected cell, bias toward formula_verification even if LLM said sheet_analysis
            cl = command.lower()
            if route == "sheet_analysis" and any(p in cl for p in ["clicked cell", "selected cell", "this cell", "current cell"]):
                return "formula_verification"
            return route
        else:
            logger.warning(f"⚠️ Invalid route '{route}' from LLM, falling back to query")
            return "query"
            
    except Exception as e:
        logger.error(f"❌ Router LLM failed: {e}, using fallback")
        # Fallback routing
        command_lower = command.lower()
        if any(phrase in command_lower for phrase in ["code", "csa", "obc"]):
            return "building_code"
        elif any(phrase in command_lower for phrase in ["update", "change", "set"]):
            return "update_value"
        else:
            return "query"

# ============================================================================
# AI-POWERED ANALYSIS
# ============================================================================

async def handle_sheet_analysis(command: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle sheet analysis queries - explain what's in the sheet
    """
    try:
        label_map = context.get("labelMap", {}) or {}
        sheet_name = context.get("sheetName", "Sheet")
        workbook_name = context.get("workbookName", "Unknown")
        used_range = context.get("usedRange", {})
        all_data = used_range.get("allData", [])
        
        # Build a summary of what's in the sheet
        if label_map:
            # Extract key parameters
            key_params = list(label_map.keys())[:50]  # Top 50 parameters
            
            if openai_client:
                # Use AI to create a smart summary
                summary_prompt = f"""Analyze this Excel sheet and create a clear summary of what it contains.

Sheet: {sheet_name}
Workbook: {workbook_name}

Available Parameters ({len(key_params)} total):
{chr(10).join(f"- {param}" for param in key_params[:30])}

Create a clear, engineering-focused summary explaining:
1. What type of design this sheet contains (beam, column, wall, etc.)
2. Key design parameters and their purposes
3. What the user can do with this sheet

Be concise and professional."""
                
                response = openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are an expert structural engineer explaining Excel design sheets."},
                        {"role": "user", "content": summary_prompt}
                    ],
                    temperature=0.3,
                    max_tokens=500
                )
                
                summary = response.choices[0].message.content.strip()
            else:
                # Fallback summary
                summary = f"This sheet '{sheet_name}' contains {len(key_params)} design parameters including: {', '.join(key_params[:10])}."
            
            return {
                "action": "message",
                "message": f"📊 Analysis of \"{sheet_name}\":\n\n{summary}\n\n💡 Tip: Try asking me to update specific parameters or calculate design values.",
                "reasoning": f"Analyzed sheet with {len(label_map)} parameters"
            }
        else:
            return {
                "action": "message",
                "message": f"The sheet '{sheet_name}' appears to be empty or I couldn't read its structure. Please ensure the sheet has data and labels.",
                "reasoning": "No label map available"
            }
            
    except Exception as e:
        logger.error(f"❌ Sheet analysis error: {e}")
        return {
            "action": "message",
            "message": f"Error analyzing sheet: {str(e)}",
            "reasoning": "Analysis failed"
        }

async def handle_formula_verification(command: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Verify an Excel formula against building code requirements
    - Extracts formula from selected cell
    - Maps cell references to their labels/meanings
    - Retrieves relevant building code formulas
    - Compares and validates
    """
    try:
        # Get selected cell and its formula
        selected_range = context.get("selectedRange", {})
        formula = selected_range.get("formulas", [[None]])[0][0] if selected_range.get("formulas") else None
        address = selected_range.get("address", "Unknown")
        values = selected_range.get("values", [[None]])[0][0] if selected_range.get("values") else None
        
        if not formula or not formula.startswith("="):
            return {
                "action": "message",
                "message": f"⚠️ No formula found in selected cell {address}. Please select a cell containing a formula.",
                "reasoning": "Formula verification requires a cell with a formula"
            }
        
        logger.info(f"🔍 Verifying formula in {address}: {formula}")
        
        # Get workbook context for mapping cell references
        label_map = context.get("labelMap", {}) or {}
        used_range = context.get("usedRange", {})
        all_data = used_range.get("allData", []) or []
        sheet_name = context.get("sheetName", "Sheet")
        sheet_type = detect_sheet_type(context)
        
        # Parse formula to extract cell references
        import re
        cell_refs = re.findall(r'([A-Z]+)(\d+)', formula)
        logger.info(f"📋 Found {len(cell_refs)} cell references in formula")
        
        # Map cell references to their labels/meanings
        cell_meanings = {}
        for col_letter, row_num in cell_refs:
            cell_addr = f"{col_letter}{row_num}"
            
            # First try to find in labelMap (reverse lookup)
            found_label = None
            for label, mapped_addr in label_map.items():
                if mapped_addr.upper() == cell_addr.upper():
                    found_label = label
                    break
            
            # Get cell value from all_data
            row_idx = int(row_num) - 1
            col_idx = ord(col_letter) - ord('A')
            cell_value = None
            if row_idx < len(all_data) and col_idx < len(all_data[row_idx]):
                cell_value = all_data[row_idx][col_idx]
            
            # If not in labelMap, check left columns for labels
            if not found_label and row_idx < len(all_data):
                for c in range(max(0, col_idx - 5), col_idx):
                    if c < len(all_data[row_idx]):
                        label = all_data[row_idx][c]
                        if label and isinstance(label, str) and len(label.strip()) > 1:
                            found_label = label.strip()
                            break
            
            cell_meanings[cell_addr] = {
                "label": found_label or f"Cell {cell_addr}",
                "value": cell_value
            }
        
        # Get building code context for the formula type
        code_context = ""
        if CODE_RAG_AVAILABLE:
            try:
                code_rag = get_building_code_rag()
                if code_rag and code_rag.loaded:
                    # Extract what the formula might be calculating
                    formula_type_prompt = f"""Analyze this Excel formula and determine what engineering calculation it represents.

Formula: {formula}
Sheet: {sheet_name}
Cell References and Meanings:
{json.dumps(cell_meanings, indent=2, default=str)}

What engineering calculation does this formula perform? (e.g., "Euler buckling load", "moment resistance", "deflection")"""
                    
                    if openai_client:
                        response = openai_client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[
                                {"role": "system", "content": "You are an expert structural engineer analyzing Excel formulas."},
                                {"role": "user", "content": formula_type_prompt}
                            ],
                            temperature=0.1,
                            max_tokens=100
                        )
                        calc_type = response.choices[0].message.content.strip()
                        
                        # Query building codes for relevant formulas
                        code_query = f"{calc_type} {sheet_type} design formula"
                        code_results = code_rag.query(code_query, top_k=3)
                        code_context = "\n\n".join([f"[{r['code']}]\n{r['text'][:500]}" for r in code_results])
                        logger.info(f"📚 Retrieved {len(code_results)} code sections for formula verification")
            except Exception as e:
                logger.error(f"⚠️ Error retrieving code context: {e}")
        
        # Use AI to verify the formula
        if openai_client:
            verification_prompt = f"""You are an expert structural engineer verifying an Excel formula against building codes.

EXCEL FORMULA:
Cell: {address}
Formula: {formula}
Current Value: {values}

CELL REFERENCES:
{json.dumps(cell_meanings, indent=2, default=str)}

BUILDING CODE FORMULAS (for reference):
{code_context or 'No building code context available'}

Verify if the Excel formula correctly implements the building code requirements:
1. Identify what calculation the formula performs
2. Map each cell reference to its engineering parameter
3. Compare the formula structure to the code formula
4. Check if units and conversions are correct
5. Verify if the formula handles both cases correctly (e.g., strong-axis vs weak-axis)

Return a detailed verification report in this format:

VERIFICATION REPORT:
Calculation Type: [what it calculates]
Formula Structure: [parsed structure]
Cell Reference Mapping: [what each cell represents]
Building Code Reference: [relevant code clause]
Verification: [CORRECT | INCORRECT | PARTIAL]
Issues Found: [any issues]
Recommendations: [suggestions]

Be specific about which parts are correct or incorrect."""
            
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert structural engineer and Excel formula validator."},
                    {"role": "user", "content": verification_prompt}
                ],
                temperature=0.2,
                max_tokens=800
            )
            
            verification = response.choices[0].message.content.strip()
            
            return {
                "action": "message",
                "message": f"🔍 Formula Verification Report for {address}:\n\n{verification}\n\nFormula: `{formula}`\nCurrent Value: {values}",
                "reasoning": f"Verified formula in {address} against building codes",
                "code_references": code_results if code_context else []
            }
        else:
            return {
                "action": "message",
                "message": f"⚠️ Formula verification requires OpenAI API. Formula in {address}: {formula}\n\nCell References: {', '.join(cell_meanings.keys())}",
                "reasoning": "OpenAI client not available"
            }
            
    except Exception as e:
        logger.error(f"❌ Formula verification error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "action": "message",
            "message": f"Error verifying formula: {str(e)}",
            "reasoning": "Verification failed"
        }

async def handle_building_code_query(command: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle building code queries like "Find applicable code for this sheet"
    """
    global LAST_CODE_RESULTS, LAST_CODE_QUERY
    if not CODE_RAG_AVAILABLE:
        return {
            "action": "message",
            "message": "Building Code RAG is not available. Please ensure building codes are loaded.",
            "reasoning": "Building code system not initialized"
        }
    
    try:
        # Get building code RAG instance
        code_rag = get_building_code_rag()
        if not code_rag or not code_rag.loaded:
            return {
                "action": "message",
                "message": "Building codes not loaded. Please check Building codes/ directory.",
                "reasoning": "No building codes available"
            }
        
        # Detect sheet type to determine which code to query
        sheet_type = detect_sheet_type(context)
        sheet_name = context.get("sheetName", "Sheet")

        # Session key and memory lookup
        workbook_name = context.get("workbookName", "Unknown")
        session_key = f"{workbook_name}::{sheet_name}"
        mem = SESSION_MEMORY.get(session_key, {})
        if mem:
            logger.info(f"🧠 Session memory hit for {session_key}: {json.dumps(mem, default=str)}")
        # Material hint for filtering (prefer glulam over CLT when ambiguous)
        material_hint = (context.get("detectedMaterial") or "").lower()
        workbook_name_lower = (context.get("workbookName") or "").lower()
        sheet_name_lower = sheet_name.lower()
        material_type = "glulam" if sheet_type in ["timber", "wood", "glulam"] else sheet_type
        if "clt" in material_hint or "clt" in workbook_name_lower or "clt" in sheet_name_lower:
            material_type = "clt"
        
        # Check if command has context about a selected cell
        # Frontend adds context like: "Tell me about applicable codes (Context: Selected cell G35 represents 'Euler Buckling Load, PE' (symbol: PE) with value: 1479.2)"
        selected_cell_context = ""
        if "(Context:" in command:
            context_match = re.search(r'\(Context:([\s\S]+?)\)', command, re.DOTALL)
            if context_match:
                selected_cell_context = context_match.group(1)
                logger.info(f"📋 Found selected cell context: {selected_cell_context}")
                # Extract symbol and label from context
                symbol_match = re.search(r'symbol:\s*([A-Z_0-9]+)', selected_cell_context)
                label_match = re.search(r'represents\s*"([^"]+)"', selected_cell_context)
                if symbol_match or label_match:
                    symbol = symbol_match.group(1) if symbol_match else ""
                    label = label_match.group(1) if label_match else ""
                    
                    # CRITICAL: Prioritize the ACTUAL cell's label/symbol over dependencies
                    # The user is asking about G124 (Euler Buckling Load, P_e), NOT about its dependencies
                    # This prevents returning wrong clauses (like CLT compressive resistance)
                    
                    # Detect material type from sheet/workbook name to avoid CLT confusion
                    # Prefer memory if available
                    if mem.get("material_type"):
                        material_type = mem["material_type"]
                    else:
                        material_type = material_type or "glulam"
                    
                    # Build semantic query using cell's label and symbol directly
                    # No hardcoding - works for any engineering parameter
                    if label and symbol:
                        query_text = f"{label} ({symbol}) {material_type} {sheet_type} design building code requirements formula"
                    elif label:
                        query_text = f"{label} {material_type} {sheet_type} design building code requirements formula"
                    elif symbol:
                        query_text = f"{symbol} {material_type} {sheet_type} design building code requirements formula"
                    else:
                        query_text = f"{material_type} {sheet_type} design building code requirements"
                    
                    logger.info(f"🎯 Cell-specific query (material: {material_type}): {query_text}")
                    logger.info(f"   Main cell label: {label}, symbol: {symbol}")
                else:
                    query_text = selected_cell_context + f" {sheet_type} design code requirements"
            else:
                query_text = command
        else:
            # Build query based on command
            query_text = command
            if "applicable" in command.lower() or "for this sheet" in command.lower():
                # Find applicable code for the sheet
                query_text = f"Building code requirements for {sheet_type} design in {sheet_name}"
        
        # Follow-up handling: if user asks for more information on previous clauses
        follow_up = False
        cl = command.lower()
        if any(p in cl for p in ["more information", "these clauses", "expand", "more details", "give me more"]):
            if LAST_CODE_RESULTS:
                code_text = "\n\n".join([
                    f"[{r['code']} - Page {r.get('page','N/A')}]\n{r.get('text','')[:1200]}"
                    for r in LAST_CODE_RESULTS[:4]
                ])
                return {
                    "action": "message",
                    "message": f"📖 More detail on previous code references:\n\n{code_text}",
                    "reasoning": "Expanded last retrieved code sections"
                }
        
        logger.info(f"🔍 Querying building codes: {query_text}")
        
        # Map sheet type to code names (must match keys in building_code_rag.py _load_all_codes)
        code_mapping = {
            "timber": "CSA_O86_Timber",
            "wood": "CSA_O86_Timber",
            "glulam": "CSA_O86_Timber",
            "concrete": "CSA_A23.3_Concrete",
            "steel": "CSA_S16_Steel"
        }
        
        logger.info(f"📋 Available codes: {list(code_rag.codes.keys())}")
        
        # Check if user is asking about a specific clause (e.g., "clause 7.5.6" or "cl 7.5.6")
        command_lower = command.lower()
        clause_match = re.search(r'cl(?:ause)?\s*\.?\s*(\d+(?:\.\d+)*(?:\.\d+)?)', command_lower)
        if clause_match:
            clause_num = clause_match.group(1)
            logger.info(f"🔍 User asking about specific clause: {clause_num}")
            
            # Query all codes for this clause number
            clause_query = f"clause {clause_num}"
            all_clause_results = code_rag.query_all_codes(clause_query, top_k_per_code=3)
            
            if all_clause_results:
                # Build comprehensive clause information
                clause_info = []
                for code_name, results in all_clause_results.items():
                    if results:
                        for r in results[:2]:  # Top 2 from each code
                            clause_info.append(f"[{code_name}]\n{r['text'][:600]}...\n(Page {r['page']})\n")
                
                return {
                    "action": "message",
                    "message": f"📖 Clause {clause_num} Information:\n\n" + "\n".join(clause_info),
                    "reasoning": f"Found clause {clause_num} references in building codes",
                    "code_references": [
                        {"code": code, "page": r["page"], "text": r["text"][:300]}
                        for code, results in all_clause_results.items()
                        for r in results[:1]
                    ]
                }
        
        # Query specific code if we know the type, otherwise query all
        target_code = None
        if sheet_type in code_mapping:
            target_code = code_mapping[sheet_type]
            logger.info(f"🎯 Targeting code: {target_code} for {sheet_type} design")
        # Bias target code from memory if present
        if mem.get("target_code") and mem.get("target_code") in code_rag.codes:
            logger.info(f"🧠 Using target_code from memory: {mem.get('target_code')}")
            target_code = mem["target_code"]
        
        # Check if the code exists in loaded codes
        if target_code and target_code in code_rag.codes:
            # Build re-ranking terms (general, not hardcoded)
            include_terms = []
            exclude_terms = []
            boost_terms = []
            
            # Material-specific filtering
            if material_type != "clt":
                exclude_terms.extend(["clt", "cross-laminated timber"])
                include_terms.extend(["glulam", "glued-laminated", "timber"])
            
            # Boost by actual cell label/symbol (works for any parameter)
            try:
                if 'label' in locals() and label:
                    # Extract key words from label for boosting (first 3-4 words usually capture the concept)
                    label_words = label.lower().split()[:4]
                    boost_terms.extend([label] + label_words)
                if 'symbol' in locals() and symbol:
                    boost_terms.append(symbol.lower())
            except Exception:
                pass
            logger.info(f"📤 Sending query to RAG: '{query_text}'")
            logger.info(f"   Code: {target_code}, top_k=10")
            logger.info(f"   Include terms: {include_terms}")
            logger.info(f"   Exclude terms: {exclude_terms}")
            logger.info(f"   Boost terms: {boost_terms}")
            
            results = code_rag.query_code(target_code, query_text, top_k=10,
                                          include_terms=include_terms,
                                          exclude_terms=exclude_terms,
                                          boost_terms=boost_terms)
            
            logger.info(f"📥 RAG returned {len(results)} chunks")
            for i, r in enumerate(results[:3], 1):
                logger.info(f"   Chunk {i}: Score={r.get('score', 0):.3f}, Page={r.get('page', 'N/A')}, Preview={r.get('text', '')[:100]}...")
            
            if results:
                # Filter out CLT when material is glulam/timber
                if material_type != "clt":
                    filtered = [r for r in results if ("clt" not in r.get("text"," ").lower() and "cross-laminated" not in r.get("text"," ").lower())]
                    results = filtered or results
                
                # Save to lightweight memory for follow-ups
                LAST_CODE_RESULTS = results
                LAST_CODE_QUERY = query_text
                # Update session memory
                SESSION_MEMORY[session_key] = {
                    "material_type": material_type,
                    "target_code": target_code,
                    "last_query_label": locals().get("label", ""),
                    "last_query_symbol": locals().get("symbol", ""),
                    "timestamp": context.get("timestamp")
                }
                
                # Use RAG's synthesis helper (centralizes all LLM synthesis logic)
                synthesized = code_rag.synthesize_response(
                    results=results,
                    user_context=selected_cell_context or "",
                    material_type=material_type,
                    sheet_type=sheet_type,
                    model=DEFAULT_MODEL
                )
                
                if synthesized:
                    return {
                        "action": "message",
                        "message": synthesized,
                        "reasoning": f"Synthesized from {target_code} results",
                        "code_references": [{
                            "code": r["code"],
                            "page": r["page"],
                            "text": r["text"][:300]
                        } for r in results[:2]]
                    }
                else:
                    # Fallback: concise summary with clause bullets (no truncation)
                    # Do not require a page number; include first few informative snippets
                    clause_items = []
                    for r in results[:4]:
                        page = r.get('page', 'N/A')
                        text = (r.get('text', '') or '')
                        preview = text.strip().replace('\n', ' ')
                        preview = (preview[:150] + '...') if len(preview) > 150 else preview
                        clause_items.append(f"• Clause {page}: {preview}")
                    clause_list = "\n".join(clause_items)
                    summary = f"Relevant building code sections from {target_code}:\n\n{clause_list}"
                    return {
                        "action": "message",
                        "message": summary,
                        "reasoning": f"Found relevant code sections from {target_code}",
                        "code_references": [{
                            "code": r["code"],
                            "page": r["page"],
                            "text": r["text"][:300]
                        } for r in results[:2]]
                    }
            else:
                logger.warning(f"⚠️ No results found for code '{target_code}' with query '{query_text}'")
        else:
            logger.warning(f"⚠️ Sheet type '{sheet_type}' not in code mapping or code '{target_code}' not loaded. Available codes: {list(code_rag.codes.keys())}")
        
        # Query all codes and return most relevant (fallback)
        logger.info(f"📚 Querying all codes as fallback...")
        all_results = code_rag.query_all_codes(query_text, top_k_per_code=2)
        
        if all_results:
            # Find best matching code
            best_code = None
            best_score = 0.0
            for code_name, results in all_results.items():
                if results and results[0]["score"] > best_score:
                    best_score = results[0]["score"]
                    best_code = code_name
            
            if best_code and all_results[best_code]:
                top_results = all_results[best_code][:2]
                clause_refs = "\n".join([f"• Clause {r.get('page', 'N/A')}: {r.get('text', '')[:150]}..." for r in top_results if r.get('page')])
                return {
                    "action": "message",
                    "message": f"Most relevant code: {best_code}\n\n{clause_refs}",
                    "reasoning": f"Found relevant code from {best_code}",
                    "code_references": [{
                        "code": best_code,
                        "page": r["page"],
                        "text": r["text"][:300]
                    } for r in top_results[:2]]
                }
        
        return {
            "action": "message",
            "message": f"No relevant building code found for '{query_text}'. Try being more specific about what you're looking for.",
            "reasoning": "No matching code sections found"
        }
        
    except Exception as e:
        logger.error(f"❌ Building code query failed: {e}")
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Traceback: {error_trace}")
        return {
            "action": "error",
            "message": f"Error querying building codes: {str(e)}\n\nCheck backend logs for details."
        }

def detect_sheet_type(context: Dict[str, Any]) -> str:
    """
    Detect the material/design type from the Excel context
    """
    # First check if add-in already detected it
    detected_material = context.get("detectedMaterial", "").lower()
    if detected_material and detected_material != "unknown":
        return detected_material
    
    sheet_name = context.get("sheetName", "").lower()
    workbook_name = context.get("workbookName", "").lower()
    label_map = context.get("labelMap", {})
    
    # Check sheet/workbook names
    if any(term in sheet_name or term in workbook_name for term in ["glulam", "timber", "wood", "lumber"]):
        return "timber"
    elif any(term in sheet_name or term in workbook_name for term in ["concrete", "rebar", "reinforcement"]):
        return "concrete"
    elif any(term in sheet_name or term in workbook_name for term in ["steel", "w-shape", "i-beam"]):
        return "steel"
    
    # Check label map for material indicators
    labels_text = " ".join(label_map.keys()).lower()
    if any(term in labels_text for term in ["glulam", "wood species", "timber", "k_d", "load duration"]):
        return "timber"
    elif any(term in labels_text for term in ["f'c", "f_c", "concrete strength", "reinforcement"]):
        return "concrete"
    elif any(term in labels_text for term in ["fy", "fy=", "steel", "w-shape"]):
        return "steel"
    
    return "unknown"

async def analyze_command_with_ai(command: str, workbook: str, sheet: str, sample_data: str, sheet_type: str = "unknown") -> Dict[str, Any]:
    
    prompt = COMMAND_ANALYSIS_PROMPT.format(
        command=command,
        workbook=workbook,
        sheet=sheet,
        sample_data=sample_data
    )
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert structural engineer analyzing Excel commands."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=500
        )
        
        # Parse JSON response
        content = response.choices[0].message.content.strip()
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', content, flags=re.DOTALL)
        if json_match:
            analysis = json.loads(json_match.group())
            return analysis
        else:
            raise ValueError("No JSON found in AI response")
            
    except Exception as e:
        logger.error(f"AI analysis failed: {e}")
        return analyze_command_fallback(command, {"workbookName": workbook, "sheetName": sheet})

def analyze_command_fallback(command: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback keyword-based analysis"""
    
    command_lower = command.lower()
    
    # Detect intent
    if any(word in command_lower for word in ["update", "set", "change", "modify"]):
        intent = "update_value"
    elif any(word in command_lower for word in ["calculate", "compute", "find", "determine"]):
        intent = "calculate"
    elif any(word in command_lower for word in ["design", "create"]):
        intent = "design"
    elif any(word in command_lower for word in ["check", "validate", "verify"]):
        intent = "validate"
    else:
        intent = "query"
    
    # Detect engineering element
    if any(word in command_lower for word in ["beam", "joist", "member"]):
        element = "beam"
    elif "wall" in command_lower:
        element = "wall"
    elif any(word in command_lower for word in ["column", "post"]):
        element = "column"
    elif "slab" in command_lower:
        element = "slab"
    else:
        element = "general"
    
    # Extract value from command
    value_match = re.search(r'(\d+\.?\d*)\s*(m|kN|MPa|mm)?', command)
    value = float(value_match.group(1)) if value_match else None
    unit = value_match.group(2) if value_match else ""
    
    # Extract property
    property_name = None
    if "span" in command_lower:
        property_name = "span"
    elif "load" in command_lower:
        property_name = "load"
    elif "strength" in command_lower or "concrete" in command_lower:
        property_name = "concrete_strength"
    
    return {
        "intent": intent,
        "engineering_element": element,
        "parameters": {
            "property": property_name,
            "value": value,
            "unit": unit
        },
        "requires_calculation": intent in ["calculate", "design", "validate"],
        "target_cells": [],
        "reasoning": f"Detected {intent} operation on {element}"
    }

# ============================================================================
# CALCULATION ENGINE
# ============================================================================

async def perform_calculations(analysis: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Perform engineering calculations based on analysis"""
    
    intent = analysis["intent"]
    element = analysis["engineering_element"]
    params = analysis["parameters"]
    
    logger.info(f"⚙️ Calculating {intent} for {element}")
    
    # Get building code context if available
    code_context = ""
    if CODE_RAG_AVAILABLE and sheet_type != "unknown":
        try:
            code_rag = get_building_code_rag()
            code_mapping = {
                "timber": "CSA_O86_Timber",
                "wood": "CSA_O86_Timber",
                "glulam": "CSA_O86_Timber",
                "concrete": "CSA_A23.3_Concrete",
                "steel": "CSA_S16_Steel"
            }
            if sheet_type in code_mapping:
                code_name = code_mapping[sheet_type]
                if code_name in code_rag.codes:
                    # Get relevant code sections for validation
                    query = f"{element} design requirements and limits"
                    code_results = code_rag.query_code(code_name, query, top_k=2)
                    if code_results:
                        code_context = "\n".join([r['text'][:200] for r in code_results])
        except Exception as e:
            logger.warning(f"⚠️ Could not retrieve code context: {e}")
    
    # Get calculation function
    if element == "beam":
        result = calculate_beam_design(params, context, code_context)
    elif element == "column":
        result = calculate_column_design(params, context, code_context)
    else:
        result = {
            "action": "message",
            "message": f"Calculation for {element} not yet implemented",
            "reasoning": "Feature coming soon"
        }
    
    return result

def calculate_beam_design(params: Dict[str, Any], context: Dict[str, Any], code_context: str = "") -> Dict[str, Any]:
    """Calculate beam design parameters"""
    
    # Extract parameters
    span = params.get("value")
    property_type = params.get("property")
    
    # Get load from context or use default
    load = 5.5  # Default load in kN/m
    
    # Try to find load in spreadsheet
    sample_data = context.get("usedRange", {}).get("sampleData", [])
    for row in sample_data:
        for i, cell in enumerate(row):
            if isinstance(cell, str) and "load" in cell.lower():
                # Load value might be in next cell
                if i + 1 < len(row) and isinstance(row[i + 1], (int, float)):
                    load = float(row[i + 1])
                    break
    
    if not span:
        span = 15  # Default span
    
    # Calculate forces
    moment = (load * span * span) / 8  # M = wL²/8
    shear = (load * span) / 2  # V = wL/2
    
    # Simplified deflection (needs E and I for real calculation)
    # Assuming typical concrete beam: E = 30 GPa, I = 7.2e9 mm⁴
    E = 30000  # MPa
    I = 7.2e9  # mm⁴
    deflection = (5 * load * (span * 1000) ** 4) / (384 * E * I)  # mm
    
    # Find target cells intelligently using label map
    moment_cell = find_cell_by_label(context, "moment")
    shear_cell = find_cell_by_label(context, "shear")
    deflection_cell = find_cell_by_label(context, "deflection")
    
    logger.info(f"Found cells: moment={moment_cell}, shear={shear_cell}, deflection={deflection_cell}")
    
    # Create updates only for cells we found
    updates = []
    
    if moment_cell:
        updates.append({
            "address": moment_cell,
            "value": round(moment, 2),
            "formula": f"= ({load} * {span}^2) / 8"
        })
    
    if shear_cell:
        updates.append({
            "address": shear_cell,
            "value": round(shear, 2),
            "formula": f"= ({load} * {span}) / 2"
        })
    
    if deflection_cell:
        updates.append({
            "address": deflection_cell,
            "value": round(deflection, 2),
            "formula": f"= (5 * {load} * {span}^4) / (384 * {E} * {I/1e9})"
        })
    
    # If no cells found, return message with calculations
    if not updates:
        return {
            "action": "message",
            "message": f"Calculated: Moment = {moment:.2f} kN⋅m, Shear = {shear:.2f} kN, Deflection = {deflection:.2f} mm",
            "reasoning": f"No matching cells found in your spreadsheet for moment/shear/deflection",
            "calculations": [
                {"type": "moment", "value": moment, "unit": "kN⋅m"},
                {"type": "shear", "value": shear, "unit": "kN"},
                {"type": "deflection", "value": deflection, "unit": "mm"}
            ]
        }
    
    # Validation checks
    deflection_limit = (span * 1000) / 250  # L/250 limit
    validations = [
        {
            "check": "Moment",
            "status": "CALCULATED",
            "passed": True,
            "value": f"{moment:.2f} kN⋅m",
            "limit": "N/A",
            "ratio": None
        },
        {
            "check": "Shear",
            "status": "CALCULATED",
            "passed": True,
            "value": f"{shear:.2f} kN",
            "limit": "N/A",
            "ratio": None
        },
        {
            "check": "Deflection (L/250)",
            "status": "PASS" if deflection < deflection_limit else "FAIL",
            "passed": deflection < deflection_limit,
            "value": f"{deflection:.2f} mm",
            "limit": f"{deflection_limit:.2f} mm",
            "ratio": round(deflection / deflection_limit, 2) if deflection_limit > 0 else None
        }
    ]
    
    return {
        "action": "update_multiple",
        "updates": updates,
        "message": f"Calculated beam design for span = {span}m, load = {load} kN/m",
        "reasoning": f"Used standard formulas: M = wL²/8, V = wL/2, δ = 5wL⁴/384EI",
        "calculations": [
            {"type": "moment", "value": moment, "unit": "kN⋅m", "formula": "wL²/8"},
            {"type": "shear", "value": shear, "unit": "kN", "formula": "wL/2"},
            {"type": "deflection", "value": deflection, "unit": "mm", "formula": "5wL⁴/384EI"}
        ],
        "validations": validations,
        "suggestions": [
            "Consider checking concrete capacity",
            "Verify steel reinforcement requirements",
            "Review AS3600 clause 8.1 for beam design"
        ]
    }

def calculate_column_design(params: Dict[str, Any], context: Dict[str, Any], code_context: str = "") -> Dict[str, Any]:
    """Calculate column design parameters"""
    
    return {
        "action": "message",
        "message": "Column design calculation coming soon",
        "reasoning": "Feature under development"
    }

def create_simple_update(analysis: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Create a simple value update"""
    
    params = analysis["parameters"]
    value = params.get("value")
    property_name = params.get("property", "value")
    
    if not value:
        return {
            "action": "message",
            "message": f"No value found to update for {property_name}",
            "reasoning": "Please specify a value in your command"
        }
    
    # Try to find the target cell
    target_cell = find_property_cell(property_name, context)
    
    if not target_cell:
        target_cell = "B3"  # Default fallback
    
    logger.info(f"🎯 Creating update: property='{property_name}', value={value}, target={target_cell}")
    
    return {
        "action": "update_value",
        "property": property_name,  # Property name for frontend label map lookup
        "target": target_cell,      # Cell address (or let frontend find via labelMap)
        "value": value,             # Value to set
        "updates": [{
            "address": target_cell,
            "value": value
        }],
        "message": f"Updated {property_name} to {value} {params.get('unit', '')}",
        "reasoning": f"Based on your command"
    }

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def format_sample_data(sample_data: List[List]) -> str:
    """Format sample data for prompt"""
    if not sample_data:
        return "No data available"
    
    lines = []
    for i, row in enumerate(sample_data[:10], 1):
        row_str = " | ".join(str(cell) for cell in row)
        lines.append(f"Row {i}: {row_str}")
    
    return "\n".join(lines)

def find_property_cell(property_name: str, context: Dict[str, Any]) -> Optional[str]:
    """Find cell address for a property using label map"""
    logger.info(f"🔍 Finding cell for property: '{property_name}'")
    
    if not property_name:
        logger.warning("⚠️ No property name provided")
        return None
    
    property_lower = property_name.lower().strip()
    
    # First try using labelMap (most reliable)
    label_map = context.get("labelMap", {}) or {}
    logger.info(f"   LabelMap has {len(label_map)} entries")
    
    if label_map:
        # Try exact match
        if property_lower in label_map:
            cell = label_map[property_lower]
            logger.info(f"   ✅ Exact match found: '{property_lower}' → {cell}")
            return cell
        
        # Token-based fuzzy scoring (no external deps)
        def normalize(s: str) -> List[str]:
            s = re.sub(r"[^a-z0-9\s]", " ", s.lower())
            return [t for t in s.split() if t]
        target_tokens = set(normalize(property_lower))
        best_addr = None
        best_score = 0.0
        for label, cell_address in label_map.items():
            label_tokens = set(normalize(label))
            if not label_tokens:
                continue
            inter = len(target_tokens & label_tokens)
            union = len(target_tokens | label_tokens)
            score = inter / union if union else 0.0
            # Also allow substring containment to boost score
            if property_lower in label or label in property_lower:
                score += 0.25
            if score > best_score:
                best_score = score
                best_addr = cell_address
        if best_addr and best_score >= 0.35:  # threshold tuned for short phrases like 'tributary width'
            logger.info(f"   ✅ Fuzzy match (score={best_score:.2f}) → {best_addr}")
            return best_addr
        logger.info(f"   ⚠️ No match found in labelMap for '{property_lower}' (best_score={best_score:.2f})")
    
    # Fallback: search sample data
    sample_data = context.get("usedRange", {}).get("allData", []) or context.get("usedRange", {}).get("sampleData", [])
    logger.info(f"   Trying sample data search ({len(sample_data)} rows)...")
    
    for i, row in enumerate(sample_data):
        for j, cell in enumerate(row):
            if isinstance(cell, str) and property_lower in cell.lower():
                # Found the label - value is likely in next cell
                row_num = i + 1
                col_num = j + 2  # Next column
                col_letter = get_column_letter(col_num)
                return f"{col_letter}{row_num}"
    
    return None

def get_column_letter(col_num: int) -> str:
    """Convert column number to letter (1 -> A, 2 -> B, etc.)"""
    letter = ""
    while col_num > 0:
        col_num -= 1
        letter = chr(65 + (col_num % 26)) + letter
        col_num //= 26
    return letter

def find_cell_by_label(context: Dict[str, Any], label: str) -> Optional[str]:
    """
    Find cell address using intelligent label mapping
    
    Uses the labelMap_client provides, which maps normalized labels to cell addresses
    """
    label_map = context.get("labelMap", {})
    
    if not label_map:
        return None
    
    # Try exact match first
    normalized_label = label.lower().strip()
    if normalized_label in label_map:
        return label_map[normalized_label]
    
    # Try partial matches
    for map_label, address in label_map.items():
        if label.lower() in map_label or map_label in label.lower():
            return address
    
    return None

