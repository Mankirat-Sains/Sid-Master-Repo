# SidOS Local Agent

**Production-grade local agent for Excel as a deterministic compute engine.**

This is the foundation that implements the gameplan's core principle: **Excel remains the source of truth for all calculations.** The AI orchestrates, Excel computes.

## 🎯 Core Principle

**Excel is the compute engine. The agent orchestrates.**

- ✅ Excel performs all mathematical operations (via formulas)
- ✅ Agent writes inputs, triggers recalculation, reads outputs
- ❌ Agent NEVER performs structural engineering calculations itself

## 🏗️ Architecture

```
Cloud Orchestrator → Local Agent → Excel Workbook
                      (this code)
```

The local agent:
1. Receives tasks from cloud orchestrator
2. Executes Excel operations using fixed tool API
3. Reports results back to orchestrator

## 📦 Components

### `excel_tools.py` - Excel Tool API
The core interface for Excel interaction:
- `read_input(name)` - Read input parameter
- `write_input(name, value)` - Write input parameter
- `recalculate()` - Trigger Excel recalculation (CRITICAL)
- `read_output(name)` - Read output parameter
- `execute_lookup(name, key)` - Execute lookup operation

### `semantic_loader.py` - Semantic Metadata
Loads semantic interface definitions that map parameter names to cell addresses.

### `agent_service.py` - Main Service
Executes tasks and manages Excel operations.

### `config.py` - Configuration
Manages agent configuration (orchestrator URL, credentials, etc.)

## 🚀 Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Ensure Excel is installed (xlwings requires it)
```

### Basic Usage

```python
from local_agent import ExcelToolAPI, load_metadata

# Load semantic metadata
metadata = load_metadata("semantic_metadata/examples/example_metadata.json")

# Create Excel Tool API
with ExcelToolAPI("workbook.xlsx", metadata) as api:
    # Write inputs
    api.write_input("span", 15.0)
    api.write_input("load", 5.5)
    
    # Trigger Excel recalculation (Excel does the math!)
    api.recalculate()
    
    # Read outputs (from Excel formulas)
    moment = api.read_output("moment")
    shear = api.read_output("shear")
    
    print(f"Moment: {moment} kN⋅m")
    print(f"Shear: {shear} kN")
```

### CLI Usage

```bash
# Execute a task from JSON
python -m local_agent.agent_service \
    --workbook "Design.xlsx" \
    --metadata "metadata.json" \
    --tool-sequence '[
        {"tool": "write_input", "params": {"name": "span", "value": 15.0}},
        {"tool": "write_input", "params": {"name": "load", "value": 5.5}},
        {"tool": "recalculate", "params": {}},
        {"tool": "read_output", "params": {"name": "moment"}}
    ]'
```

## 📋 Semantic Metadata Format

Semantic metadata defines the interface between semantic names and Excel cells:

```json
{
  "inputs": {
    "span": {
      "sheet": "INFO",
      "address": "B3",
      "description": "Beam span in meters"
    }
  },
  "outputs": {
    "moment": {
      "sheet": "Full Building",
      "address": "G12",
      "description": "Maximum moment in kN⋅m"
    }
  },
  "lookups": {
    "location_snow_load": {
      "type": "vlookup",
      "sheet": "Tables",
      "range": "A1:D100"
    }
  }
}
```

## ✅ What This Achieves

1. **Excel is the compute engine** - All calculations happen in Excel formulas
2. **Semantic abstraction** - Works with any Excel layout via metadata
3. **Fixed tool API** - Controlled interface prevents accidental corruption
4. **Production-ready** - Clean code, error handling, logging

## 🔧 Configuration

Configuration can be set via:
- Environment variables (prefixed with `SIDOS_`)
- Config file (JSON)
- Default values

See `config.py` for details.

## 🧪 Testing

```bash
# Run tests (requires Excel installed)
python -m pytest tests/
```

## 📝 Code Quality

- ✅ Production-grade error handling
- ✅ Comprehensive logging
- ✅ Type hints throughout
- ✅ Clear documentation
- ✅ Clean, maintainable code

## 🚨 Critical Notes

1. **xlwings requires Excel installed** - This is a Windows/Mac requirement
2. **Workbook must exist** - Agent doesn't create workbooks
3. **Semantic metadata is required** - Must define inputs/outputs mapping
4. **Recalculation is critical** - Always call `recalculate()` after writing inputs

## 📚 Next Steps

1. ✅ Phase 1 Complete: Local agent foundation
2. 🔄 Phase 2: Cloud orchestrator integration
3. 🔄 Phase 3: Streamlit UI
4. 🔄 Phase 4: Full deployment

## 🤝 Contributing

This is production code. Maintain:
- Clear comments
- Error handling
- Logging
- Type hints
- Documentation

## 📄 License

Part of the Sidian Engineering platform.

