# How to Use the Intelligent Parser

## Quick Start with Your Excel File

### Step 1: Parse Your Workbook

```bash
cd "/Users/jameshinsperger/Desktop/Desktop - MacBook Pro (2)/Visual Studio/trainexcel/SidOS/parsing"

# Parse your Excel file
python parse_workbook.py \
    "/Users/jameshinsperger/Desktop/Desktop - MacBook Pro (2)/Sidian/SidOS/Glulam Column.xlsx" \
    -o "Glulam_Column_metadata.json"
```

This will:
1. ✅ Detect legend using AI (no hardcoding)
2. ✅ Classify cells by color
3. ✅ Understand cell meanings from context
4. ✅ Create semantic groups intelligently
5. ✅ Generate metadata for local agent

### Step 2: Test with Local Agent

```bash
cd "/Users/jameshinsperger/Desktop/Desktop - MacBook Pro (2)/Visual Studio/trainexcel/SidOS"

python test_local_agent.py \
    "/Users/jameshinsperger/Desktop/Desktop - MacBook Pro (2)/Sidian/SidOS/Glulam Column.xlsx" \
    "parsing/Glulam_Column_metadata.json"
```

## What Makes This Generic

### ✅ No Hardcoded Keywords
The original script had hardcoded keywords like:
```python
# OLD (hardcoded):
if any(kw in label_lower for kw in ['span', 'load', 'length', ...]):
```

**NEW (AI-driven):**
- AI analyzes nearby cells to understand meaning
- No keyword matching
- Works with any terminology

### ✅ No Hardcoded Sheet Names
The original script assumed sheets like "INFO", "Full Building".

**NEW (generic):**
- Analyzes any sheet structure
- AI determines sheet purpose
- Works with any sheet names

### ✅ No Hardcoded Locations
The original script assumed legend location.

**NEW (intelligent):**
- AI searches entire sheet for legend
- Finds legend anywhere (top, bottom, side)
- Understands any legend format

### ✅ Semantic Grouping
The parser creates semantic groups (not individual cells):
- `location_data`: Groups location-related parameters
- `project_parameters`: Groups project dimensions
- `design_summary`: Groups design results

This aligns with the gameplan: semantic abstraction, not individual cell mappings.

## Example Output

After parsing, you'll get metadata like:

```json
{
  "inputs": {
    "location_data": {
      "type": "group",
      "sheet": "INFO",
      "cells": {
        "location_name": "B2",
        "ground_snow_load": "B6",
        "wind_load": "B8"
      },
      "description": "Location and environmental load parameters"
    }
  },
  "outputs": {
    "design_summary": {
      "type": "group",
      "sheet": "Full Building",
      "cells": {
        "governing_moment": "G12",
        "governing_shear": "G13"
      },
      "description": "Key design results"
    }
  }
}
```

The local agent can then use these groups:
- `write_input("location_data", {"location_name": "Big Trout Lake", ...})`
- `read_output("design_summary")` → Returns all design results

## Cost & Time Estimates

- **Cost**: ~$0.10-0.50 per workbook (OpenAI API)
- **Time**: ~2-5 minutes per workbook
- **Accuracy**: High for spreadsheets with color legends

## Troubleshooting

**"OpenAI API key not set"**
- Set `OPENAI_API_KEY` environment variable
- Or use `--api-key` flag

**"No legend found"**
- Parser will still work, but less accurate
- Will classify by formulas only

**"Too many parameters"**
- Use semantic groups (default)
- Groups reduce complexity significantly

