#!/usr/bin/env python3
"""
GraphQL Schema Parser
Extracts useful information from GraphQL schema for LLM consumption
"""

import json
import re
from typing import Dict, Any, List, Optional


def parse_schema_summary(schema_text: str) -> Dict[str, Any]:
    """
    Parse GraphQL schema and extract a clean summary for LLM.
    
    Returns a structured summary with:
    - Available queries
    - Query signatures
    - Example queries
    """
    
    summary = {
        "queries": [],
        "query_examples": [],
        "types": {}
    }
    
    # Try to parse as JSON first (if it's introspection result)
    try:
        schema_data = json.loads(schema_text)
        if "data" in schema_data and "__schema" in schema_data["data"]:
            return parse_introspection_result(schema_data["data"]["__schema"])
    except (json.JSONDecodeError, KeyError):
        pass
    
    # Try to parse as SDL (Schema Definition Language)
    return parse_sdl_schema(schema_text)


def parse_introspection_result(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Parse GraphQL introspection JSON result"""
    
    summary = {
        "queries": [],
        "query_examples": [],
        "types": {}
    }
    
    # Find Query type
    query_type = None
    for type_def in schema.get("types", []):
        if type_def.get("name") == "Query":
            query_type = type_def
            break
    
    if not query_type:
        return summary
    
    # Extract all query fields
    for field in query_type.get("fields", []):
        field_name = field.get("name")
        field_desc = field.get("description", "")
        
        # Get arguments
        args = []
        for arg in field.get("args", []):
            arg_name = arg.get("name")
            arg_type = get_type_string(arg.get("type", {}))
            is_required = "!" in arg_type
            args.append({
                "name": arg_name,
                "type": arg_type.replace("!", ""),
                "required": is_required
            })
        
        # Get return type
        return_type = get_type_string(field.get("type", {}))
        
        query_info = {
            "name": field_name,
            "description": field_desc,
            "arguments": args,
            "return_type": return_type
        }
        
        summary["queries"].append(query_info)
        
        # Generate example query
        example = generate_example_query(field_name, args, return_type)
        if example:
            summary["query_examples"].append(example)
    
    return summary


def get_type_string(type_obj: Dict[str, Any], depth: int = 0) -> str:
    """Recursively get type string from GraphQL type object"""
    if depth > 5:  # Prevent infinite recursion
        return "String"
    
    kind = type_obj.get("kind", "")
    name = type_obj.get("name")
    
    if kind == "NON_NULL":
        of_type = type_obj.get("ofType", {})
        return get_type_string(of_type, depth + 1) + "!"
    elif kind == "LIST":
        of_type = type_obj.get("ofType", {})
        return "[" + get_type_string(of_type, depth + 1) + "]"
    elif name:
        return name
    else:
        return "String"


def generate_example_query(field_name: str, args: List[Dict], return_type: str) -> str:
    """Generate an example GraphQL query"""
    
    # Build arguments string
    args_str = ""
    if args:
        required_args = [a for a in args if a.get("required")]
        if required_args:
            # Only include required args in example
            args_list = [f'{a["name"]}: "{a["name"].upper()}_VALUE"' for a in required_args[:2]]
            args_str = "(" + ", ".join(args_list) + ")"
    
    # Build selection set based on return type
    selection = "{ id name }"
    if "Project" in return_type:
        selection = "{ id name description }"
    elif "Stream" in return_type:
        selection = "{ id name description }"
    elif "Commit" in return_type:
        selection = "{ id message author { name } }"
    
    return f"{{ {field_name}{args_str} {selection} }}"


def parse_sdl_schema(schema_text: str) -> Dict[str, Any]:
    """Parse SDL (Schema Definition Language) format"""
    
    summary = {
        "queries": [],
        "query_examples": [],
        "types": {}
    }
    
    # Find Query type definition
    query_match = re.search(r'type Query\s*\{([^}]+)\}', schema_text, re.DOTALL)
    if not query_match:
        return summary
    
    query_body = query_match.group(1)
    
    # Extract field definitions
    field_pattern = r'(\w+)(\([^)]*\))?\s*:\s*([^\n]+)'
    for match in re.finditer(field_pattern, query_body):
        field_name = match.group(1)
        args_str = match.group(2) or ""
        return_type = match.group(3).strip().rstrip('!').rstrip(']').rstrip('[')
        
        # Parse arguments
        args = []
        if args_str:
            args_match = re.findall(r'(\w+):\s*([^\s,)]+)', args_str)
            for arg_name, arg_type in args_match:
                is_required = arg_type.endswith('!')
                args.append({
                    "name": arg_name,
                    "type": arg_type.rstrip('!'),
                    "required": is_required
                })
        
        query_info = {
            "name": field_name,
            "description": "",
            "arguments": args,
            "return_type": return_type
        }
        
        summary["queries"].append(query_info)
        
        # Generate example
        example = generate_example_query(field_name, args, return_type)
        if example:
            summary["query_examples"].append(example)
    
    return summary


def format_schema_for_llm(schema_summary: Dict[str, Any]) -> str:
    """Format schema summary for LLM consumption"""
    
    lines = ["# GraphQL Schema Summary\n"]
    
    lines.append("## Available Queries:\n")
    for query in schema_summary.get("queries", [])[:20]:  # Limit to 20 queries
        lines.append(f"### {query['name']}")
        if query.get("description"):
            lines.append(f"  {query['description']}")
        
        if query.get("arguments"):
            lines.append("  Arguments:")
            for arg in query["arguments"]:
                req = " (required)" if arg.get("required") else " (optional)"
                lines.append(f"    - {arg['name']}: {arg['type']}{req}")
        
        lines.append(f"  Returns: {query.get('return_type', 'Unknown')}")
        lines.append("")
    
    if schema_summary.get("query_examples"):
        lines.append("## Example Queries:\n")
        for example in schema_summary["query_examples"][:10]:  # Limit to 10 examples
            lines.append(f"```graphql\n{example}\n```\n")
    
    # Add IFC-specific query patterns
    lines.append("\n## IFC Element Query Patterns:\n")
    lines.append("""
To find IFC elements (beams, columns, etc.) in a project:

**Path:** Project → Version → referencedObject → Object.children → objects[].data

**Key Fields:**
- `Object.data: JSONObject` - Contains IFC element data (ifcType, properties, etc.)
- `Object.children: ObjectCollection` - Traverses the IFC element tree
- `Version.referencedObject: String` - Root object ID for a version

**Example Query Structure:**
```graphql
query FindIFCElements($projectId: String!, $objectId: String!) {
  project(id: $projectId) {
    object(id: $objectId) {
      children(limit: 1000, depth: 5) {
        objects {
          id
          data  # <-- Parse this JSON to check ifcType, properties
        }
      }
    }
  }
}
```

**Important Notes:**
1. The `data` field returns a JSONObject (string) - you must parse it client-side
2. IFC elements have: `data.ifcType` (e.g., "IfcBeam", "IfcColumn")
3. Material info is in: `data.properties.Attributes.Material` or `data.properties.PropertySets`
4. GraphQL cannot filter jsonb content - fetch data, then filter programmatically
5. For "steel beams": filter where `ifcType === "IfcBeam"` AND material contains "steel"
""")
    
    return "\n".join(lines)


if __name__ == "__main__":
    # Test with a sample schema
    test_schema = """
    type Query {
      project(id: String!): Project
      projects(limit: Int): [Project!]!
      stream(id: String!): Stream
      streams(limit: Int): [Stream!]!
    }
    
    type Project {
      id: String!
      name: String!
      description: String
    }
    """
    
    summary = parse_sdl_schema(test_schema)
    formatted = format_schema_for_llm(summary)
    print(formatted)


