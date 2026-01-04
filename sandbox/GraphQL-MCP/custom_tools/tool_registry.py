#!/usr/bin/env python3
"""
Tool Registry
Manages all custom tools and provides them to the LLM
"""

import logging
from typing import Dict, List, Any, Optional
from custom_tools.base_tool import BaseTool
from custom_tools.building_perimeter_tool import BuildingPerimeterTool
from custom_tools.find_beams_tool import FindBeamsTool
from custom_tools.element_geometry_tool import ElementGeometryTool
from custom_tools.element_relationships_tool import ElementRelationshipsTool
from custom_tools.element_properties_tool import ElementPropertiesTool
from custom_tools.find_element_types_tool import FindElementTypesTool
from custom_tools.find_material_types_tool import FindMaterialTypesTool
from custom_tools.find_projects_by_material import FindProjectsByMaterialTool

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Registry for all custom MCP tools.
    
    This allows you to:
    1. Register custom tools
    2. Get tool definitions for LLM function calling
    3. Execute tools by name
    """
    
    def __init__(self, graphql_client=None):
        """
        Initialize the tool registry.
        
        Args:
            graphql_client: GraphQL client instance
        """
        self.graphql_client = graphql_client
        self._tools: Dict[str, BaseTool] = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Register default tools."""
        if self.graphql_client:
            # Minimal composable tools (can be combined)
            self.register(FindElementTypesTool(self.graphql_client))
            self.register(FindMaterialTypesTool(self.graphql_client))
            
            # Specialized tools
            self.register(BuildingPerimeterTool(self.graphql_client))
            self.register(FindBeamsTool(self.graphql_client))
            self.register(ElementGeometryTool(self.graphql_client))
            self.register(ElementRelationshipsTool(self.graphql_client))
            self.register(ElementPropertiesTool(self.graphql_client))
            
            # Fast search tools
            self.register(FindProjectsByMaterialTool(self.graphql_client))
    
    def register(self, tool: BaseTool):
        """
        Register a custom tool.
        
        Args:
            tool: Tool instance to register
        """
        definition = tool.get_definition()
        self._tools[definition.name] = tool
        logger.info(f"Registered tool: {definition.name}")
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """
        Get a tool by name.
        
        Args:
            name: Tool name
            
        Returns:
            Tool instance or None
        """
        return self._tools.get(name)
    
    def get_all_tool_definitions(self) -> List[Dict[str, Any]]:
        """
        Get all tool definitions in LLM function calling format.
        
        Returns:
            List of tool definitions
        """
        return [tool.to_mcp_tool_format() for tool in self._tools.values()]
    
    def execute_tool(self, name: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a tool by name.
        
        Args:
            name: Tool name
            **kwargs: Tool parameters
            
        Returns:
            Tool execution result
        """
        tool = self.get_tool(name)
        if not tool:
            return {
                "isError": True,
                "content": [{"type": "text", "text": f"Tool '{name}' not found"}]
            }
        
        return tool.run(**kwargs)
    
    def list_tools(self) -> List[str]:
        """
        List all registered tool names.
        
        Returns:
            List of tool names
        """
        return list(self._tools.keys())


