#!/usr/bin/env python3
"""
Base class for custom MCP tools
Provides the interface and structure for building custom tools
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ToolDefinition:
    """Definition of an MCP tool"""
    name: str
    description: str
    parameters: Dict[str, Any]  # Zod schema equivalent (JSON Schema format)
    handler: callable  # Function that executes the tool


class BaseTool(ABC):
    """
    Base class for custom MCP tools.
    
    Custom tools should inherit from this and implement:
    - get_definition(): Return ToolDefinition
    - execute(): Execute the tool logic
    """
    
    def __init__(self, graphql_client=None):
        """
        Initialize the tool.
        
        Args:
            graphql_client: GraphQL client instance (from python_client or graphql_mcp_tool)
        """
        self.graphql_client = graphql_client
        self._definition = None
    
    @abstractmethod
    def get_definition(self) -> ToolDefinition:
        """
        Get the tool definition (name, description, parameters).
        
        Returns:
            ToolDefinition object
        """
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the tool with given parameters.
        
        Args:
            **kwargs: Tool parameters
            
        Returns:
            Dict with 'content' (list of content items) and optionally 'isError' (bool)
        """
        pass
    
    def to_mcp_tool_format(self) -> Dict[str, Any]:
        """
        Convert tool definition to MCP tool format for LLM function calling.
        
        Returns:
            Dict in OpenAI function calling format
        """
        definition = self.get_definition()
        
        # Convert parameters to JSON Schema format
        properties = {}
        required = []
        
        for param_name, param_spec in definition.parameters.items():
            if isinstance(param_spec, dict):
                properties[param_name] = param_spec
                if param_spec.get("required", False):
                    required.append(param_name)
            else:
                # Simple type specification
                properties[param_name] = {
                    "type": param_spec if isinstance(param_spec, str) else "string",
                    "description": f"Parameter {param_name}"
                }
        
        return {
            "type": "function",
            "function": {
                "name": definition.name,
                "description": definition.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }
    
    def validate_parameters(self, **kwargs) -> bool:
        """
        Validate tool parameters.
        
        Args:
            **kwargs: Parameters to validate
            
        Returns:
            True if valid, raises ValueError if invalid
        """
        definition = self.get_definition()
        
        # Check required parameters
        for param_name, param_spec in definition.parameters.items():
            if isinstance(param_spec, dict) and param_spec.get("required", False):
                if param_name not in kwargs:
                    raise ValueError(f"Missing required parameter: {param_name}")
        
        return True
    
    def run(self, **kwargs) -> Dict[str, Any]:
        """
        Run the tool with validation.
        
        Args:
            **kwargs: Tool parameters
            
        Returns:
            Tool execution result
        """
        try:
            self.validate_parameters(**kwargs)
            return self.execute(**kwargs)
        except Exception as e:
            logger.error(f"Tool {self.get_definition().name} failed: {e}")
            return {
                "isError": True,
                "content": [
                    {
                        "type": "text",
                        "text": f"Tool execution failed: {str(e)}"
                    }
                ]
            }


