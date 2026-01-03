# Adding Custom Tools to the MCP Server

## Overview

After building and testing your custom tools, you can add them to the MCP server so the LLM can use them directly.

## Current Architecture

The MCP server (`src/index.ts`) currently has two tools:
1. `introspect-schema` - Gets GraphQL schema
2. `query-graphql` - Executes GraphQL queries

Your custom tools are higher-level abstractions that:
- Wrap multiple GraphQL queries
- Process and analyze data
- Return formatted results

## Two Approaches

### Approach 1: Python Tools (Recommended for Testing)

Keep tools in Python and expose them via the Python client. This is what you're doing now with `test_natural_language.py`.

**Pros:**
- Easy to develop and test
- Can use Python libraries for data processing
- No need to modify TypeScript MCP server

**Cons:**
- Tools only available when using Python client
- Not part of the core MCP server

### Approach 2: Add to MCP Server (TypeScript)

Add tools directly to the MCP server in TypeScript.

**Pros:**
- Available to all MCP clients (not just Python)
- Part of the core server
- Better integration

**Cons:**
- Need to rewrite in TypeScript
- More complex to maintain

## Recommended Workflow

1. **Build in Python** (you are here)
   - Create tools in `custom_tools/`
   - Test with `test_tools.py`
   - Test with LLM in `test_natural_language.py`

2. **Use Python Tools** (for now)
   - Integrate `ToolRegistry` into `test_natural_language.py`
   - LLM can use custom tools alongside GraphQL queries

3. **Add to MCP Server** (later, if needed)
   - Rewrite tools in TypeScript
   - Add to `src/index.ts`
   - Rebuild MCP server

## Integrating Python Tools with LLM

Update `test_natural_language.py` to include custom tools:

```python
from custom_tools.tool_registry import ToolRegistry

# In test_natural_language_query function:
# Initialize tool registry
tool_registry = ToolRegistry(graphql_client=graphql_tool)

# Get all tools (GraphQL + custom)
all_tools = graphql_tool.get_tool_definitions()
custom_tools = tool_registry.get_all_tool_definitions()
all_tools.extend(custom_tools)

# Pass to LLM
response = openai_client.chat.completions.create(
    model="gpt-4o",
    messages=messages,
    tools=[{"type": "function", "function": t["function"]} for t in all_tools],
    tool_choice="auto"
)

# Handle tool calls
if tool_name in ["get_building_perimeter", "find_beams"]:
    # Execute custom tool
    result = tool_registry.execute_tool(tool_name, **tool_args)
else:
    # Execute GraphQL tool
    result = graphql_tool.query(...)
```

## Adding Tools to MCP Server (TypeScript)

If you want to add tools to the MCP server itself:

### Step 1: Create Tool in TypeScript

Create `src/tools/building-perimeter.ts`:

```typescript
import { z } from "zod";
import { fetchGraphQL } from "../helpers/graphql.js";

export async function getBuildingPerimeter(
  projectId: string,
  unit: string = "feet"
) {
  // Implementation similar to Python version
  // Query for versions, objects, extract coordinates, calculate
  // Return formatted result
}

export const buildingPerimeterTool = {
  name: "get_building_perimeter",
  description: "Calculate building perimeter from beams",
  parameters: {
    project_id: z.string(),
    unit: z.string().optional().default("feet"),
  },
  handler: async ({ project_id, unit }) => {
    const result = await getBuildingPerimeter(project_id, unit);
    return {
      content: [{ type: "text", text: result }],
    };
  },
};
```

### Step 2: Register in MCP Server

In `src/index.ts`:

```typescript
import { buildingPerimeterTool } from "./tools/building-perimeter.js";

// Register tool
server.tool(
  buildingPerimeterTool.name,
  buildingPerimeterTool.description,
  buildingPerimeterTool.parameters,
  buildingPerimeterTool.handler
);
```

### Step 3: Rebuild

```bash
bun run build
```

## Best Practices

1. **Test First**: Always test tools in Python before adding to MCP
2. **Document**: Add clear descriptions so LLM knows when to use tools
3. **Error Handling**: Return clear error messages
4. **Parameters**: Use Zod schemas for validation
5. **Performance**: Consider pagination for large datasets

## Example: Complete Integration

See `test_natural_language_with_custom_tools.py` (to be created) for a complete example of:
- Loading custom tools
- Combining with GraphQL tools
- LLM using both types of tools
- Handling tool execution

## Next Steps

1. ✅ Build tools in Python (done)
2. ✅ Test tools (done)
3. ⏭️ Integrate with test_natural_language.py
4. ⏭️ Test with LLM
5. ⏭️ (Optional) Add to MCP server in TypeScript


