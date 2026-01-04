# Intelligent Excel Parser

**AI-driven, generic Excel parser with zero hardcoding.**

This parser creates semantic metadata for Excel workbooks by intelligently understanding their structure, regardless of layout, color scheme, or terminology.

## 🎯 Key Features

### ✅ Zero Hardcoding
- **No hardcoded keywords**: AI understands any terminology
- **No hardcoded locations**: Finds legend anywhere in sheet
- **No hardcoded layouts**: Works with any spreadsheet structure
- **No hardcoded colors**: AI interprets any color scheme

### ✅ AI-Driven Understanding
- **Legend Detection**: AI finds and interprets legends automatically
- **Cell Classification**: Classifies cells by color using legend
- **Context Understanding**: AI analyzes nearby cells to understand meaning
- **Semantic Grouping**: Intelligently groups related parameters

### ✅ Aligned with Gameplan
- Creates semantic groups (not individual cells)
- Works with any Excel layout
- Generates metadata for local agent
- Supports the gameplan's vision

## 🚀 Quick Start

### Basic Usage

```python
from parsing import IntelligentExcelParser

# Create parser
parser = IntelligentExcelParser()

# Parse workbook
metadata = parser.parse_workbook(
    "workbook.xlsx",
    output_path="metadata.json"
)
```

### Command Line

```bash
# Parse a workbook
python -m parsing.intelligent_excel_parser "workbook.xlsx" -o "metadata.json"

# Convert parser output to local agent format
python -m parsing.metadata_converter parser_output.json -o agent_metadata.json --flatten
```

## 📋 How It Works

### Step 1: Legend Detection
The AI scans the workbook and finds color legends automatically:
- No assumptions about legend location
- No hardcoded keywords
- AI understands any legend format

### Step 2: Cell Classification
Cells are classified by their colors using the detected legend:
- Input cells (user-editable)
- Output cells (calculated results)
- Calculation cells (formulas)
- Status indicators (pass/fail)
- Capacity ratios (utilization)

### Step 3: Context Understanding
For each classified cell, AI analyzes nearby cells to understand:
- Parameter name (from nearby labels)
- Units (from nearby cells or embedded in labels)
- Engineering meaning (from context)

### Step 4: Semantic Grouping
AI groups related parameters together:
- `location_data`: location_name, ground_snow_load, wind_load
- `project_parameters`: building_width, building_length
- `design_summary`: governing_moment, governing_shear

### Step 5: Metadata Generation
Creates metadata in format required by local agent:
- Semantic groups (for high-level operations)
- Individual cell mappings (for direct access)

## 📊 Output Format

### Parser Output
```json
{
  "workbook_path": "workbook.xlsx",
  "legend_detected": true,
  "semantic_interface": {
    "inputs": {
      "location_data": {
        "type": "group",
        "sheet": "INFO",
        "cells": {
          "location_name": "B2",
          "ground_snow_load": "B6"
        }
      }
    },
    "outputs": {
      "design_summary": {
        "type": "group",
        "sheet": "Full Building",
        "cells": {
          "governing_moment": "G12",
          "governing_shear": "G13"
        }
      }
    }
  }
}
```

### Local Agent Format (Flattened)
```json
{
  "inputs": {
    "location_name": {
      "sheet": "INFO",
      "address": "B2",
      "group": "location_data"
    },
    "ground_snow_load": {
      "sheet": "INFO",
      "address": "B6",
      "group": "location_data"
    }
  },
  "outputs": {
    "governing_moment": {
      "sheet": "Full Building",
      "address": "G12",
      "group": "design_summary"
    }
  }
}
```

## 🔧 Integration with Local Agent

```python
from parsing import IntelligentExcelParser, convert_to_local_agent_format
from local_agent import ExcelToolAPI

# Parse workbook
parser = IntelligentExcelParser()
parser_output = parser.parse_workbook("workbook.xlsx")

# Convert to local agent format
metadata = convert_to_local_agent_format(parser_output, flatten_groups=True)

# Use with local agent
with ExcelToolAPI("workbook.xlsx", metadata) as api:
    api.write_input("location_name", "Big Trout Lake")
    api.recalculate()
    moment = api.read_output("governing_moment")
```

## 🎯 Why This Approach

### Aligned with Gameplan
- **Semantic abstraction**: Works with any layout
- **Intelligent grouping**: Creates meaningful groups
- **No hardcoding**: Fully AI-driven
- **Generic**: Works with any Excel file

### Production Ready
- Comprehensive error handling
- Detailed logging
- Type hints throughout
- Clean, maintainable code

## 📝 Requirements

- openpyxl: Excel file reading
- openai: AI-driven understanding
- python-dotenv: Environment variables

## 🚨 Important Notes

1. **Requires OpenAI API key**: Set `OPENAI_API_KEY` environment variable
2. **Cost**: ~$0.10-0.50 per workbook (depending on size)
3. **Time**: ~2-5 minutes per workbook (AI processing)
4. **Accuracy**: High for well-structured spreadsheets with legends

## 🔄 Workflow

1. **Parse workbook** → Creates semantic groups
2. **Convert metadata** → Formats for local agent
3. **Use with local agent** → Execute Excel operations

This creates a complete pipeline: Parse → Convert → Execute

