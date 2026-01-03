# Gameplan Verification: Excel as Deterministic Compute Engine

## Executive Summary

**Status**: ⚠️ **PARTIAL ALIGNMENT** - The implementation has the right foundation but violates a core principle of the gameplan.

**Key Finding**: The system is currently performing structural engineering calculations itself instead of treating Excel as the authoritative compute engine.

---

## Core Principle Verification

### ✅ ALIGNED: Semantic Abstraction Layer

**Gameplan Says:**
> "Each workbook is abstracted into a semantic interface defined by: Inputs, Outputs, Lookups, Context"

**Implementation Status:**
- ✅ **Label Mapping**: System uses `labelMap` to map parameter names to cell addresses
- ✅ **Layout Detection**: LLM analyzes spreadsheet layout to understand structure
- ✅ **Context Extraction**: Automatically extracts workbook context (labels, formulas, structure)
- ✅ **Workbook-Agnostic**: Works with any spreadsheet layout (no hardcoding)

**Evidence:**
```typescript
// taskpane.ts - Intelligent label mapping
const labelMap: { [label: string]: string } = {};
// Maps parameter names to cell addresses automatically
```

```python
# orchestrator.py - Uses labelMap for semantic access
label_map = context.get("labelMap", {}) or {}
target_cell = find_property_cell(property_name, context)
```

**Verdict**: ✅ **FULLY ALIGNED** - The semantic abstraction layer is well-implemented.

---

### ❌ VIOLATION: AI Performing Calculations

**Gameplan Says:**
> "Excel remains the source of truth for calculations. The AI never performs structural calculations itself."

**Implementation Status:**
- ❌ **System calculates values directly**: `calculate_beam_design()` performs math
- ❌ **Hardcoded formulas**: `moment = (load * span * span) / 8`
- ❌ **Bypasses Excel**: Writes calculated values instead of triggering Excel recalculation

**Evidence:**
```python
# orchestrator.py lines 1116-1147
def calculate_beam_design(params: Dict[str, Any], context: Dict[str, Any], code_context: str = "") -> Dict[str, Any]:
    """Calculate beam design parameters"""
    
    # Extract parameters
    span = params.get("value")
    load = 5.5  # Default load in kN/m
    
    # Calculate forces
    moment = (load * span * span) / 8  # M = wL²/8  ❌ VIOLATION
    shear = (load * span) / 2  # V = wL/2  ❌ VIOLATION
    deflection = (5 * load * (span * 1000) ** 4) / (384 * E * I)  ❌ VIOLATION
    
    # Writes calculated values directly
    updates.append({
        "address": moment_cell,
        "value": round(moment, 2),  # ❌ Should trigger Excel recalculation instead
        "formula": f"= ({load} * {span}^2) / 8"
    })
```

**What Should Happen (Per Gameplan):**
```python
# CORRECT APPROACH:
def calculate_beam_design(params, context):
    # 1. Write inputs to Excel
    write_input("span", params.get("span"))
    write_input("load", params.get("load"))
    
    # 2. Trigger Excel recalculation
    recalculate()  # Let Excel do the math
    
    # 3. Read outputs from Excel
    moment = read_output("moment")
    shear = read_output("shear")
    deflection = read_output("deflection")
    
    # 4. Explain results
    return {
        "action": "message",
        "message": f"Updated inputs and recalculated. Results: Moment = {moment} kN⋅m..."
    }
```

**Verdict**: ❌ **CRITICAL VIOLATION** - System violates core principle by performing calculations.

---

### ⚠️ PARTIAL: Controlled Execution Model

**Gameplan Says:**
> "All interaction with Excel occurs through a local agent... exposes a small, fixed tool API: read_input(name), write_input(name, value), execute_lookup(name, key), recalculate(), read_output(name)"

**Implementation Status:**
- ✅ **Has semantic interface**: Label mapping provides abstraction
- ⚠️ **Missing fixed tool API**: No explicit `read_input()`, `write_input()`, `recalculate()` functions
- ⚠️ **Direct cell access**: System can access arbitrary cells via labelMap
- ❌ **No recalculation trigger**: Doesn't explicitly trigger Excel recalculation

**Current Implementation:**
```python
# Current: Direct cell updates
target_cell = find_property_cell(property_name, context)
updates.append({"address": target_cell, "value": value})
```

**What's Missing:**
```python
# Should have explicit tool API:
def read_input(name: str) -> Any:
    """Read an input parameter from Excel"""
    cell = labelMap.get(name)
    return read_cell(cell)

def write_input(name: str, value: Any) -> None:
    """Write an input parameter to Excel"""
    cell = labelMap.get(name)
    write_cell(cell, value)

def recalculate() -> None:
    """Trigger Excel recalculation"""
    # Use Office.js or xlwings to trigger recalculation
    pass

def read_output(name: str) -> Any:
    """Read an output parameter from Excel"""
    cell = outputMap.get(name)
    return read_cell(cell)
```

**Verdict**: ⚠️ **PARTIAL** - Has semantic layer but missing explicit tool API and recalculation.

---

### ✅ ALIGNED: Runtime Workflow (Partially)

**Gameplan Says:**
> "1. Interprets intent at a planning level (no math). 2. Determines which Excel inputs must change. 3. Sends structured task to local agent. 4. Local agent updates inputs and triggers recalculation. 5. Outputs are read and returned. 6. AI explains results."

**Implementation Status:**
- ✅ **Step 1**: Intelligent routing classifies commands
- ✅ **Step 2**: Finds target cells via labelMap
- ✅ **Step 3**: Sends structured actions to frontend
- ❌ **Step 4**: Missing explicit recalculation trigger
- ⚠️ **Step 5**: Reads outputs but also calculates them
- ✅ **Step 6**: Explains results in engineering language

**Evidence:**
```python
# orchestrator.py - Intelligent routing
route_decision = await intelligent_route_command(command)
if route_decision == "update_value":
    target_cell = find_property_cell(property_name, context)
    # ✅ Finds inputs correctly
    # ❌ But then calculates instead of triggering Excel
```

**Verdict**: ⚠️ **PARTIAL** - Workflow is correct but missing recalculation step.

---

## Phase Alignment

### Phase 1: Excel as Authoritative Engine
**Status**: ⚠️ **IN PROGRESS**
- ✅ Semantic abstraction layer exists
- ✅ Label mapping works
- ❌ Still performing calculations itself
- ❌ Missing explicit recalculation trigger

### Phase 2: Observe Usage and Capture Semantics
**Status**: ✅ **ALIGNED**
- System tracks label mappings
- Context extraction captures real semantics
- Building code queries capture usage patterns

### Phase 3: Build Parallel Server-Side Engine
**Status**: ❌ **NOT STARTED**
- No parallel calculation engine yet
- This is future work per gameplan

### Phase 4: Migrate Users
**Status**: ❌ **NOT STARTED**
- Future phase

---

## Critical Issues to Fix

### 1. **Remove Calculation Functions** ❌ CRITICAL
**Location**: `backend/agents/orchestrator.py`
- **Lines 1116-1247**: `calculate_beam_design()`, `calculate_column_design()`, `perform_calculations()`
- **Action**: Delete these functions or refactor to only write inputs and read outputs

### 2. **Add Recalculation Trigger** ❌ CRITICAL
**Location**: `src/taskpane/taskpane.ts` and `backend/agents/orchestrator.py`
- **Action**: Add explicit `recalculate()` function that triggers Excel recalculation
- **Implementation**: Use Office.js `context.sync()` or xlwings to trigger recalculation

### 3. **Implement Fixed Tool API** ⚠️ IMPORTANT
**Location**: `backend/agents/orchestrator.py`
- **Action**: Create explicit tool functions:
  - `read_input(name)`
  - `write_input(name, value)`
  - `execute_lookup(name, key)`
  - `recalculate()`
  - `read_output(name)`

### 4. **Separate Inputs from Outputs** ⚠️ IMPORTANT
**Location**: Context extraction and label mapping
- **Action**: Distinguish between input parameters and output parameters
- **Implementation**: Add `inputMap` and `outputMap` instead of single `labelMap`

---

## What's Working Well

### ✅ Semantic Abstraction
- Intelligent label mapping
- Layout-agnostic design
- Context-aware parameter resolution

### ✅ Intelligent Routing
- LLM-based command classification
- Context-aware decision making
- Building code integration

### ✅ User Experience
- Real-time awareness
- Contextual help
- Formula verification (reads Excel formulas correctly)

---

## Recommended Refactoring

### Step 1: Remove Calculation Logic
```python
# DELETE or REFACTOR:
async def perform_calculations(...)  # Remove calculation logic
def calculate_beam_design(...)      # Remove calculation logic
def calculate_column_design(...)    # Remove calculation logic

# REPLACE WITH:
async def update_inputs_and_recalculate(inputs: Dict[str, Any], context: Dict[str, Any]):
    """Write inputs to Excel, trigger recalculation, read outputs"""
    # 1. Write inputs
    for name, value in inputs.items():
        cell = inputMap.get(name)
        write_cell(cell, value)
    
    # 2. Trigger Excel recalculation
    await trigger_excel_recalculation()
    
    # 3. Read outputs
    outputs = {}
    for name in outputMap.keys():
        cell = outputMap.get(name)
        outputs[name] = read_cell(cell)
    
    return outputs
```

### Step 2: Add Recalculation Trigger
```typescript
// taskpane.ts
async function triggerRecalculation(): Promise<void> {
    await Excel.run(async (context) => {
        const sheet = context.workbook.worksheets.getActiveWorksheet();
        // Force recalculation
        sheet.getUsedRange().calculate(true);
        await context.sync();
    });
}
```

### Step 3: Implement Tool API
```python
# orchestrator.py
class ExcelToolAPI:
    def __init__(self, context: Dict[str, Any]):
        self.inputMap = context.get("inputMap", {})
        self.outputMap = context.get("outputMap", {})
        self.lookupMap = context.get("lookupMap", {})
    
    def read_input(self, name: str) -> Any:
        """Read input parameter from Excel"""
        cell = self.inputMap.get(name)
        return self._read_cell(cell)
    
    def write_input(self, name: str, value: Any) -> None:
        """Write input parameter to Excel"""
        cell = self.inputMap.get(name)
        self._write_cell(cell, value)
    
    def recalculate(self) -> None:
        """Trigger Excel recalculation"""
        # Send command to frontend to trigger recalculation
        pass
    
    def read_output(self, name: str) -> Any:
        """Read output parameter from Excel"""
        cell = self.outputMap.get(name)
        return self._read_cell(cell)
```

---

## Conclusion

The implementation has a **strong foundation** with semantic abstraction and intelligent routing, but **violates the core principle** by performing calculations itself instead of treating Excel as the authoritative compute engine.

**Priority Actions:**
1. ❌ **CRITICAL**: Remove calculation functions
2. ❌ **CRITICAL**: Add recalculation trigger
3. ⚠️ **IMPORTANT**: Implement fixed tool API
4. ⚠️ **IMPORTANT**: Separate inputs from outputs

Once these are fixed, the system will fully align with the gameplan's vision of Excel as an external, deterministic compute engine.

