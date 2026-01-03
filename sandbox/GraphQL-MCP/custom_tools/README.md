# Custom Tools for GraphQL MCP

Build, test, and integrate custom tools that wrap GraphQL queries for specific use cases.

## What Are Custom Tools?

Custom tools are higher-level functions that:
- Wrap multiple GraphQL queries
- Process and analyze data
- Return formatted, useful results
- Make it easier for LLMs to answer specific questions

**Example:** Instead of the LLM constructing complex GraphQL queries to find beams, extract geometry, and calculate perimeter, it can just call `get_building_perimeter(project_id)`.

## Architecture

```
User Question
    ↓
LLM (GPT-4o)
    ↓
Tool Selection (GraphQL tools OR Custom tools)
    ↓
Tool Execution
    ↓
Result
```

## Available Tools

### 1. `get_building_perimeter`
Calculates building dimensions from beam geometry.

**Use when users ask:**
- "What is the building width?"
- "Which project has a width > 10 feet?"
- "Calculate the building perimeter"

**Parameters:**
- `project_id` (required): Project to analyze
- `unit` (optional): Output unit (feet, meters, etc.)

### 2. `find_beams`
Finds all beams/members in a project.

**Use when users ask:**
- "Find all steel beams"
- "List all beams in project X"
- "Show me wood members"

**Parameters:**
- `project_id` (required): Project to search
- `material_filter` (optional): Filter by material (steel, wood, etc.)
- `limit` (optional): Max results (default: 100)

## Quick Start

### 1. Test Tools

```bash
cd custom_tools
python3 test_tools.py
```

This will:
- Initialize the tool registry
- List available tools
- Test each tool with a real project
- Show results

### 2. Create Your Own Tool

Create a new file `custom_tools/my_tool.py`:

```python
from custom_tools.base_tool import BaseTool, ToolDefinition

class MyCustomTool(BaseTool):
    def get_definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="my_tool",
            description="What your tool does",
            parameters={
                "param1": {
                    "type": "string",
                    "description": "Parameter description",
                    "required": True
                }
            },
            handler=self.execute
        )
    
    def execute(self, param1: str) -> Dict[str, Any]:
        # Your tool logic here
        # Use self.graphql_client to query GraphQL
        return {
            "isError": False,
            "content": [{"type": "text", "text": "Result"}]
        }
```

### 3. Register Your Tool

In `custom_tools/tool_registry.py`:

```python
from custom_tools.my_tool import MyCustomTool

def _register_default_tools(self):
    if self.graphql_client:
        self.register(BuildingPerimeterTool(self.graphql_client))
        self.register(FindBeamsTool(self.graphql_client))
        self.register(MyCustomTool(self.graphql_client))  # Add this
```

### 4. Test Your Tool

```bash
python3 test_tools.py
```

## Integration with LLM

### Option 1: Use with test_natural_language.py

Update `test_natural_language.py` to include custom tools:

```python
from custom_tools.tool_registry import ToolRegistry

# In test_natural_language_query function:
tool_registry = ToolRegistry(graphql_client=graphql_tool)

# Get all tools
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
if message.tool_calls:
    for tool_call in message.tool_calls:
        tool_name = tool_call.function.name
        
        if tool_name in ["get_building_perimeter", "find_beams"]:
            # Custom tool
            result = tool_registry.execute_tool(tool_name, **tool_args)
        else:
            # GraphQL tool
            result = graphql_tool.query(...)
```

### Option 2: Standalone Script

See `test_natural_language_with_custom_tools.py` (example to be created).

## Tool Development Workflow

1. **Design** - What does the tool do? What parameters does it need?
2. **Implement** - Create tool class inheriting from `BaseTool`
3. **Test** - Run `test_tools.py` to verify it works
4. **Integrate** - Add to `tool_registry.py` and integrate with LLM
5. **Test with LLM** - Ask natural language questions
6. **Iterate** - Refine based on results

## Best Practices

### Tool Descriptions

Write clear descriptions so the LLM knows when to use your tool:

```python
description="""Calculate building perimeter from beams.

Use this when users ask about:
- Building width, length, or dimensions
- Building perimeter or footprint
- Which project has width > X"""
```

### Error Handling

Always return proper error format:

```python
return {
    "isError": True,
    "content": [{"type": "text", "text": "Error message"}]
}
```

### Parameter Validation

Use the base class validation:

```python
def execute(self, project_id: str, **kwargs):
    # BaseTool.run() will validate parameters
    # But you can add custom validation too
    if not project_id:
        raise ValueError("project_id is required")
```

### GraphQL Queries

Use the graphql_client provided:

```python
result = self.graphql_client.query(
    query_string,
    variables={"projectId": project_id}
)
```

## File Structure

```
custom_tools/
├── __init__.py
├── base_tool.py              # Base class for all tools
├── tool_registry.py           # Tool management
├── building_perimeter_tool.py # Example: Building dimensions
├── find_beams_tool.py         # Example: Find beams
├── test_tools.py              # Test all tools
├── README.md                  # This file
└── ADD_TOOLS_TO_MCP.md        # Guide for adding to MCP server
```

## Examples

### Example 1: Simple Query Tool

```python
class GetProjectInfoTool(BaseTool):
    def get_definition(self):
        return ToolDefinition(
            name="get_project_info",
            description="Get basic information about a project",
            parameters={
                "project_id": {"type": "string", "required": True}
            },
            handler=self.execute
        )
    
    def execute(self, project_id: str):
        query = """
        query GetProject($id: String!) {
          project(id: $id) {
            id
            name
            description
          }
        }
        """
        result = self.graphql_client.query(query, variables={"id": project_id})
        return {"isError": False, "content": [{"type": "text", "text": str(result)}]}
```

### Example 2: Complex Analysis Tool

```python
class AnalyzeStructureTool(BaseTool):
    def execute(self, project_id: str):
        # 1. Query for all elements
        # 2. Filter and categorize
        # 3. Calculate statistics
        # 4. Return formatted report
        
        elements = self._get_all_elements(project_id)
        stats = self._calculate_stats(elements)
        
        report = f"""
        Structure Analysis:
        - Total elements: {stats['total']}
        - Beams: {stats['beams']}
        - Columns: {stats['columns']}
        ...
        """
        
        return {
            "isError": False,
            "content": [{"type": "text", "text": report}],
            "data": stats
        }
```

## Testing

### Unit Test a Tool

```python
from custom_tools.building_perimeter_tool import BuildingPerimeterTool

# Mock graphql_client
tool = BuildingPerimeterTool(graphql_client=mock_client)
result = tool.execute(project_id="test123", unit="feet")
assert not result.get("isError")
```

### Integration Test

```bash
python3 test_tools.py
```

### Test with LLM

```bash
python3 test_natural_language.py
# Then ask: "What is the building perimeter of project X?"
```

## Troubleshooting

### "Tool not found"
- Make sure tool is registered in `tool_registry.py`
- Check tool name matches exactly

### "GraphQL client not available"
- Ensure graphql_client is passed to tool constructor
- Check GraphQL endpoint is configured

### "Parameter validation failed"
- Check parameter names match definition
- Ensure required parameters are provided

## Next Steps

1. ✅ Framework created
2. ✅ Example tools provided
3. ⏭️ Test tools (`python3 test_tools.py`)
4. ⏭️ Integrate with LLM
5. ⏭️ Create more tools for your use cases
6. ⏭️ (Optional) Add to MCP server in TypeScript

## See Also

- `ADD_TOOLS_TO_MCP.md` - How to add tools to MCP server
- `test_tools.py` - Test script
- `base_tool.py` - Base class documentation


