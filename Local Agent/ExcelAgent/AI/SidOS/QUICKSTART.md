# Quick Start Guide - 2 Day Sprint

## What We Built

✅ **Production-grade local agent** that implements the gameplan's core principle:
- Excel is the compute engine (all calculations in Excel formulas)
- Agent orchestrates (writes inputs, triggers recalculation, reads outputs)
- Semantic abstraction (works with any Excel layout via metadata)

## File Structure

```
SidOS/
├── local_agent/
│   ├── __init__.py              # Package exports
│   ├── excel_tools.py           # ⭐ Core Excel Tool API
│   ├── semantic_loader.py      # Metadata loader
│   ├── agent_service.py        # Main service entry point
│   └── config.py               # Configuration management
├── semantic_metadata/
│   └── examples/
│       └── example_metadata.json  # Example semantic interface
├── tests/
│   └── test_excel_tools.py     # Test suite
├── test_local_agent.py         # Quick test script
├── requirements.txt            # Dependencies
├── README.md                   # Full documentation
└── QUICKSTART.md              # This file
```

## Installation (5 minutes)

```bash
# 1. Install dependencies
cd SidOS
pip install -r requirements.txt

# 2. Verify xlwings can access Excel
python -c "import xlwings as xw; print('✅ xlwings ready')"
```

## Test It Works (2 minutes)

### Step 1: Create a test Excel file

Create `test_workbook.xlsx` with:
- Sheet1, cell B3: `15` (this will be "span" input)
- Sheet1, cell B4: `5.5` (this will be "load" input)
- Sheet1, cell G12: `=B3*B4*B3/8` (this will be "moment" output - formula!)

### Step 2: Create metadata

Create `test_metadata.json`:
```json
{
  "inputs": {
    "span": {"sheet": "Sheet1", "address": "B3"},
    "load": {"sheet": "Sheet1", "address": "B4"}
  },
  "outputs": {
    "moment": {"sheet": "Sheet1", "address": "G12"}
  },
  "lookups": {}
}
```

### Step 3: Run test

```bash
python test_local_agent.py test_workbook.xlsx test_metadata.json
```

**Expected output:**
```
✅ Loaded 2 inputs, 1 outputs
✅ Wrote span = 15.0 m
✅ Wrote load = 5.5 kN/m
✅ Recalculation complete
✅ Moment: 154.6875 kN⋅m  ← This comes from Excel formula!
```

## The Critical Test

**If the moment value comes from Excel's formula calculation, you've succeeded!**

The formula `=B3*B4*B3/8` in Excel calculates: `15 * 5.5 * 15 / 8 = 154.6875`

This proves:
- ✅ Agent writes inputs to Excel
- ✅ Excel recalculates formulas
- ✅ Agent reads outputs from Excel
- ✅ **Excel is the compute engine** (not Python!)

## Using in Code

```python
from local_agent import ExcelToolAPI, load_metadata

# Load metadata
metadata = load_metadata("test_metadata.json")

# Use context manager (auto-closes)
with ExcelToolAPI("test_workbook.xlsx", metadata) as api:
    # Write inputs
    api.write_input("span", 20.0)
    api.write_input("load", 6.0)
    
    # CRITICAL: Trigger Excel recalculation
    api.recalculate()
    
    # Read outputs (from Excel formulas!)
    moment = api.read_output("moment")
    print(f"Moment: {moment}")  # Excel calculated this!
```

## CLI Usage

```bash
python -m local_agent.agent_service \
    --workbook "test_workbook.xlsx" \
    --metadata "test_metadata.json" \
    --tool-sequence '[
        {"tool": "write_input", "params": {"name": "span", "value": 15.0}},
        {"tool": "write_input", "params": {"name": "load", "value": 5.5}},
        {"tool": "recalculate", "params": {}},
        {"tool": "read_output", "params": {"name": "moment"}}
    ]'
```

## What Makes This Production-Grade

1. **Error Handling**: Comprehensive exception handling with clear error messages
2. **Logging**: Detailed logging for debugging and audit trails
3. **Type Hints**: Full type annotations for IDE support and documentation
4. **Documentation**: Clear docstrings explaining every function
5. **Validation**: Metadata validation ensures correct structure
6. **Context Managers**: Safe resource management (auto-closes workbooks)
7. **Clean Code**: Readable, maintainable, extensible

## Next Steps

1. ✅ **Phase 1 Complete**: Local agent foundation works
2. 🔄 **Phase 2**: Integrate with cloud orchestrator
3. 🔄 **Phase 3**: Build Streamlit UI
4. 🔄 **Phase 4**: Full deployment

## Troubleshooting

**"xlwings is not available"**
- Install: `pip install xlwings`
- Ensure Excel is installed

**"Workbook not found"**
- Check file path is correct
- Use absolute paths if relative paths fail

**"Input 'span' not found in semantic metadata"**
- Check metadata file has correct structure
- Verify parameter names match

**"Failed to open workbook"**
- Ensure Excel is installed
- Check file isn't open in another program
- Verify file isn't corrupted

## Success Criteria

✅ Can write inputs to Excel  
✅ Can trigger Excel recalculation  
✅ Can read outputs from Excel  
✅ All calculations happen in Excel (not Python)  
✅ Works with any Excel layout (via metadata)  

**If all checkboxes are ✅, Phase 1 is complete!**

