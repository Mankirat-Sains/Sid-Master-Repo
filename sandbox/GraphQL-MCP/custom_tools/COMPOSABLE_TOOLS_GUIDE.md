# Minimal Composable Tools Guide

## Overview

This guide explains the minimal set of composable tools designed to handle inconsistent data structures and enable complex queries through tool composition.

## The Problem: Inconsistent Data Structures

Different BIM sources (IFC vs Revit) store element information in different locations:

**IFC Elements:**
- Type: `data.ifcType` (e.g., "IFCCOLUMN")
- Material: `data.properties.Attributes.Material` or `data.properties.Property Sets`

**Revit Elements:**
- Type: `data.category` (e.g., "Structural Columns") OR `data.family` (e.g., "Timber-Column") OR `data.parameters.Type`
- Material: `data.family` (e.g., "Timber-Column") OR `data.type` (e.g., "Wood Truss Roof w/ Steel") OR `data.parameters.Material`

This inconsistency makes it hard to create consistent queries.

## The Solution: Element Normalizer + Composable Tools

### 1. Element Normalizer (`element_normalizer.py`)

A shared utility that handles all inconsistency issues:

- **Extracts element type** from multiple locations with priority:
  1. `ifcType` (IFC)
  2. `category` (Revit)
  3. `family` (Revit)
  4. `parameters.Type` (Revit nested)
  5. `name` (fallback)
  6. `speckleType` (last resort)

- **Extracts material** from multiple locations:
  1. IFC properties (`properties.Attributes.Material`, `Property Sets`)
  2. Revit `parameters.Material`
  3. Revit `family` (parsed for keywords like "Timber")
  4. Revit `type` (parsed for keywords)
  5. `name` (parsed for keywords)

- **Normalizes output** to consistent format regardless of source

### 2. Minimal Composable Tools

#### `find_element_types`
Finds elements by type (Column, Beam, Wall, etc.)

**Usage:**
```python
registry.execute_tool(
    "find_element_types",
    project_id="...",
    model_id="...",
    element_type="Column",
    limit=100
)
```

**Returns:** Normalized list of elements with consistent type information

#### `find_material_types`
Finds elements by material (Timber, Steel, Concrete, etc.)

**Usage:**
```python
registry.execute_tool(
    "find_material_types",
    project_id="...",
    model_id="...",
    material="Timber",
    element_type="Column",  # Optional: combine filters
    limit=100
)
```

**Returns:** Normalized list of elements with consistent material information

## Tool Composition

These tools can be combined in sequence to answer complex queries:

### Example 1: "Find buildings with timber columns"

**Option A: Single combined call**
```python
result = registry.execute_tool(
    "find_material_types",
    project_id="...",
    material="Timber",
    element_type="Column"  # Combined filter
)
```

**Option B: Sequential composition**
```python
# Step 1: Find all columns
columns = registry.execute_tool(
    "find_element_types",
    project_id="...",
    element_type="Column"
)
column_ids = [e["element_id"] for e in columns["data"]["elements"]]

# Step 2: Filter columns by timber material
timber_columns = registry.execute_tool(
    "find_material_types",
    project_id="...",
    material="Timber",
    element_ids=column_ids  # Use pre-filtered list
)
```

### Example 2: "Find all steel beams"

```python
result = registry.execute_tool(
    "find_material_types",
    project_id="...",
    material="Steel",
    element_type="Beam"  # Combined filter
)
```

### Example 3: "Find all structural timber elements"

```python
# First find all timber
timber = registry.execute_tool(
    "find_material_types",
    project_id="...",
    material="Timber"
)

# Then filter by structural types (Column, Beam, etc.)
# (This would require additional filtering logic or a third tool)
```

## Benefits

1. **Handles Inconsistency**: Normalizer checks all possible locations automatically
2. **Composable**: Tools can be combined for complex queries
3. **Minimal Set**: Only 2 tools needed for most queries (type + material)
4. **Rule-Based Filtering**: All filtering happens client-side before LLM sees data
5. **Reusable**: Same tools work for many different query types

## Normalized Output Format

Both tools return elements in this consistent format:

```python
{
    "id": "...",
    "element_id": "...",
    "name": "Column#255",
    "element_type": {
        "type": "Column",  # Normalized
        "source_type": "family",  # Where it came from
        "source_value": "Timber-Column",  # Original value
        "is_structural": True
    },
    "material": {
        "material": "Timber",  # Normalized
        "source": "family",  # Where it came from
        "confidence": "medium"  # high/medium/low
    },
    "speckle_type": "Objects.BuiltElements.Revit.RevitColumn"
}
```

## Testing

Run the test script to see composition in action:

```bash
python custom_tools/test_composable_tools.py
```

This demonstrates:
1. Finding all columns
2. Finding all timber elements
3. Combining both to find timber columns
4. Alternative composition using element_ids

## Integration with LLM

When the LLM receives a query like "tell me a building that has timber columns":

1. LLM calls `find_element_types(type="Column")` → gets all columns
2. LLM calls `find_material_types(material="Timber", element_ids=[...])` → filters for timber
3. LLM receives only matching elements (not raw data)
4. LLM can then identify which projects/buildings contain these elements

All filtering is rule-based and happens before data reaches the LLM, avoiding token limit issues.


