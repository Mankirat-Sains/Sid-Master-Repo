# ChatGPT Prompt for Excel Semantic Metadata Generation

Copy and paste this prompt into ChatGPT, then provide your Excel file information.

---

## 📋 PROMPT (Copy Everything Below)

```
You are an expert at analyzing engineering Excel spreadsheets and creating semantic metadata for AI agents.

I need you to analyze an Excel workbook and create semantic metadata that maps parameter names to cell addresses, organized into semantic groups.

## Your Task

Analyze the Excel workbook structure and create a JSON metadata file with:
1. **Inputs**: Parameters users can modify (grouped semantically)
2. **Outputs**: Calculated results from formulas (grouped semantically)
3. **Lookups**: Lookup tables or reference data

## How to Analyze

### Step 1: Understand the Workbook Structure
- Identify key sheets (e.g., INFO, Full Building, Locations, Tables)
- Understand what each sheet does
- Look for color legends that explain cell types (INPUT, OUTPUT, CALCULATION, etc.)

### Step 2: Detect Color Legend
- Find any legend or key that explains what colors mean
- Common categories: user_input, calculated_output, calculation, status_indicator
- If no legend exists, classify cells by:
  - Cells with formulas = outputs/calculations
  - Cells without formulas that users edit = inputs
  - Cells with pass/fail indicators = status_indicators

### Step 3: Classify Cells
For each sheet, identify:
- **Input cells**: User-editable parameters (often colored differently)
- **Output cells**: Calculated results (formulas)
- **Status cells**: Pass/fail indicators, utilization ratios

### Step 4: Understand Cell Meaning
For each input/output cell, determine:
- **Parameter name**: What engineering parameter it represents (e.g., "span", "load", "moment")
- **Description**: What it means in engineering terms
- **Units**: What units are used (m, kN, MPa, etc.)
- **Cell address**: Exact cell location (e.g., "B3", "G12")

Look at nearby cells to understand:
- Labels to the left/above = parameter name
- Values to the right = units or the actual value
- Headers above = section context

### Step 5: Create Semantic Groups
Group related parameters together. Examples:
- **location_data**: location_name, ground_snow_load, wind_load, ground_rain_load
- **project_parameters**: building_width, building_length, building_height
- **load_cases**: live_load_udl1, dead_load_udl1, live_load_udl2
- **design_summary**: governing_moment, governing_shear, governing_member, utilization_ratio
- **capacity_ratios**: moment_ratio, shear_ratio, deflection_ratio

## Output Format

Return ONLY valid JSON in this exact structure:

```json
{
  "inputs": {
    "group_name": {
      "type": "group",
      "sheet": "SheetName",
      "cells": {
        "parameter_name": "cell_address",
        "another_parameter": "cell_address"
      },
      "description": "What this group represents"
    }
  },
  "outputs": {
    "group_name": {
      "type": "group",
      "sheet": "SheetName",
      "cells": {
        "parameter_name": "cell_address"
      },
      "description": "What this group represents"
    }
  },
  "lookups": {
    "lookup_name": {
      "type": "table",
      "sheet": "SheetName",
      "range": "A1:D100",
      "description": "What this lookup table contains"
    }
  }
}
```

## Critical Rules

1. **Use semantic groups** - Don't create individual mappings for every cell. Group related parameters.
2. **Meaningful names** - Use clear, engineering-focused parameter names (e.g., "span", not "cell_b3")
3. **Exact cell addresses** - Use Excel format (e.g., "B3", "G12", "AA5")
4. **Sheet names** - Use exact sheet names from the workbook
5. **No hardcoding** - Understand the structure, don't assume patterns
6. **Focus on key parameters** - Don't include every single cell, focus on important inputs/outputs

## Example Output

```json
{
  "inputs": {
    "location_data": {
      "type": "group",
      "sheet": "INFO",
      "cells": {
        "location_name": "B2",
        "ground_snow_load": "B6",
        "ground_rain_load": "B7",
        "wind_load": "B8"
      },
      "description": "Location and environmental load parameters"
    },
    "project_parameters": {
      "type": "group",
      "sheet": "INFO",
      "cells": {
        "building_width": "B10",
        "building_length": "B11",
        "snow_loading_case": "B21"
      },
      "description": "Project dimensions and loading cases"
    }
  },
  "outputs": {
    "design_summary": {
      "type": "group",
      "sheet": "Full Building",
      "cells": {
        "governing_moment": "G12",
        "governing_shear": "G13",
        "governing_member": "G14",
        "utilization_ratio": "G15"
      },
      "description": "Key design results and governing values"
    },
    "capacity_ratios": {
      "type": "group",
      "sheet": "Full Building",
      "cells": {
        "moment_ratio": "H12",
        "shear_ratio": "H13",
        "deflection_ratio": "H14"
      },
      "description": "Capacity utilization ratios (Mf/Mr, Vf/Vr, etc.)"
    }
  },
  "lookups": {
    "location_lookup": {
      "type": "table",
      "sheet": "Locations",
      "range": "A1:D100",
      "description": "Lookup table for location-specific data (snow loads, wind loads, etc.)"
    }
  }
}
```

## What I'll Provide

I will give you:
1. Excel workbook name
2. Sheet names and their purposes
3. Sample data from key sheets (first 50 rows)
4. Information about color legend (if available)
5. Any specific cell addresses I've identified

## Your Response

Analyze the provided information and return ONLY the JSON metadata structure. No explanations, no markdown code blocks, just the raw JSON.

Ready? Here's my Excel workbook information:

[PASTE YOUR EXCEL INFORMATION HERE]
```

---

## 📝 How to Use This Prompt

### Step 1: Gather Excel Information

You need to provide ChatGPT with:
1. **Workbook name**
2. **Sheet names** and what they do
3. **Sample data** from key sheets (copy first 50 rows)
4. **Color legend** (if visible - describe what colors mean)
5. **Key cell addresses** you've identified (optional)

### Step 2: Format Your Excel Data

Create a text representation like this:

```
Workbook: Glulam Column.xlsx

Sheets:
- INFO: Contains project parameters and location data
- Full Building: Main calculation engine with design results
- Locations: Lookup table for location-specific data
- Tables: Material property lookup tables

Sheet: INFO (Sample Data - First 30 rows)
Row 1: A1: Project Name | B1: [value]
Row 2: A2: Location | B2: [location name]
Row 3: A3: [empty]
Row 4: A4: Ground snow load, Ss | B4: [value]
Row 5: A5: Ground rain load, Sr | B5: [value]
...

Color Legend (if visible):
- Orange/Peach color (FFFFCC99): INPUT cells
- Gray color (FFF2F2F2): CALCULATION and OUTPUT cells
- Red color (FFFF0000): FAIL indicators
- Green color (FF92D050): PASS indicators
```

### Step 3: Paste into ChatGPT

1. Copy the entire prompt above
2. Replace `[PASTE YOUR EXCEL INFORMATION HERE]` with your formatted Excel data
3. Send to ChatGPT
4. ChatGPT will return the JSON metadata

### Step 4: Save the JSON

Copy ChatGPT's JSON response and save it as `metadata.json` for use with the local agent.

---

## 🎯 Example: Complete Prompt with Data

```
[PASTE THE FULL PROMPT ABOVE]

Ready? Here's my Excel workbook information:

Workbook: Glulam Column.xlsx

Sheets:
- Sheet1: Main design calculations for glulam column

Sheet: Sheet1 (Sample Data)
Row 1: A1: Glulam Column Design | B1: [empty] | C1: [empty]
Row 2: A2: [empty] | B2: [empty] | C2: [empty]
Row 3: A3: Span | B3: 6.0 | C3: m
Row 4: A4: Load | B4: 50.0 | C4: kN
Row 5: A5: [empty] | B5: [empty] | C5: [empty]
Row 6: A6: Moment | B6: =B3*B4 | C6: kN⋅m
Row 7: A7: Shear | B7: =B4/2 | C7: kN

Color Legend:
- Yellow/Orange cells: Input parameters (B3, B4)
- Gray cells: Calculated values (B6, B7)

Key Observations:
- Column A contains labels
- Column B contains values (inputs) or formulas (outputs)
- Column C contains units
```

---

## ✅ What You'll Get

ChatGPT will return JSON like:

```json
{
  "inputs": {
    "design_parameters": {
      "type": "group",
      "sheet": "Sheet1",
      "cells": {
        "span": "B3",
        "load": "B4"
      },
      "description": "Design input parameters"
    }
  },
  "outputs": {
    "design_results": {
      "type": "group",
      "sheet": "Sheet1",
      "cells": {
        "moment": "B6",
        "shear": "B7"
      },
      "description": "Calculated design results"
    }
  },
  "lookups": {}
}
```

Save this as `metadata.json` and use it with the local agent!

