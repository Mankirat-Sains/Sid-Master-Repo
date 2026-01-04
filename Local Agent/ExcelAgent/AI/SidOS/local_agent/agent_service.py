#!/usr/bin/env python3
"""
Local Agent Service - Main Entry Point

This is the main service that runs on the customer's machine. It:
1. Connects to the cloud orchestrator
2. Polls for tasks
3. Executes Excel operations using ExcelToolAPI
4. Reports results back to orchestrator

The agent runs as a background service and executes tasks as they arrive.

Author: Sidian Engineering Team
"""

import sys
import json
import logging
import asyncio
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

# Import local modules
from excel_tools import ExcelToolAPI, ExcelToolAPIError, execute_tool_sequence
from semantic_loader import load_metadata, SemanticMetadataError
from config import load_config, AgentConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LocalAgent:
    """
    Local Agent - Executes Excel operations on behalf of cloud orchestrator.
    
    This agent runs on the customer's machine and provides the Excel Tool API
    interface. It receives tasks from the cloud orchestrator, executes them
    using Excel, and reports results back.
    
    The agent maintains the critical principle: Excel is the source of truth
    for all calculations. The agent never performs calculations itself.
    """
    
    def __init__(self, config: AgentConfig):
        """
        Initialize local agent with configuration.
        
        Args:
            config: Agent configuration
        """
        self.config = config
        logger.info(f"Initializing local agent: {config.agent_id}")
    
    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task received from the orchestrator.
        
        A task contains:
        - task_id: Unique task identifier
        - workbook_path: Path to Excel workbook
        - semantic_metadata: Semantic interface definition
        - tool_sequence: Sequence of tool operations to execute
        
        Args:
            task: Task dictionary from orchestrator
        
        Returns:
            Result dictionary with execution results
        """
        task_id = task.get("task_id", "unknown")
        workbook_path = task.get("workbook_path")
        semantic_metadata = task.get("semantic_metadata", {})
        tool_sequence = task.get("tool_sequence", [])
        
        logger.info(f"Executing task {task_id}")
        logger.debug(f"Workbook: {workbook_path}")
        logger.debug(f"Tool sequence: {len(tool_sequence)} operations")
        
        if not workbook_path:
            return {
                "task_id": task_id,
                "status": "error",
                "error": "Missing workbook_path in task"
            }
        
        if not Path(workbook_path).exists():
            return {
                "task_id": task_id,
                "status": "error",
                "error": f"Workbook not found: {workbook_path}"
            }
        
        try:
            # Execute tool sequence
            result = execute_tool_sequence(
                workbook_path=workbook_path,
                semantic_metadata=semantic_metadata,
                tool_sequence=tool_sequence,
                visible=self.config.excel_visible
            )
            
            if result["success"]:
                logger.info(f"Task {task_id} completed successfully")
                return {
                    "task_id": task_id,
                    "status": "completed",
                    "results": result["results"],
                    "outputs": result["outputs"],
                    "error": None
                }
            else:
                logger.error(f"Task {task_id} failed: {result['error']}")
                return {
                    "task_id": task_id,
                    "status": "error",
                    "results": result["results"],
                    "outputs": result["outputs"],
                    "error": result["error"]
                }
        
        except ExcelToolAPIError as e:
            logger.error(f"Excel Tool API error in task {task_id}: {e}")
            return {
                "task_id": task_id,
                "status": "error",
                "error": f"Excel Tool API error: {str(e)}"
            }
        
        except Exception as e:
            logger.error(f"Unexpected error in task {task_id}: {e}", exc_info=True)
            return {
                "task_id": task_id,
                "status": "error",
                "error": f"Unexpected error: {str(e)}"
            }
    
    def execute_task_from_json(self, task_json: str) -> Dict[str, Any]:
        """
        Execute a task from JSON string (for CLI usage).
        
        Args:
            task_json: JSON string containing task definition
        
        Returns:
            Result dictionary
        """
        try:
            task = json.loads(task_json)
            return self.execute_task(task)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in task: {e}")
            return {
                "status": "error",
                "error": f"Invalid JSON: {str(e)}"
            }


def main():
    """
    Main entry point for local agent service.
    
    Can run in two modes:
    1. CLI mode: Execute a single task from command line
    2. Service mode: Run continuously, polling for tasks (future)
    """
    parser = argparse.ArgumentParser(
        description="Sidian Local Agent - Excel Tool API Service"
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file"
    )
    parser.add_argument(
        "--task",
        type=str,
        help="JSON task to execute (CLI mode)"
    )
    parser.add_argument(
        "--workbook",
        type=Path,
        help="Path to Excel workbook (for CLI mode)"
    )
    parser.add_argument(
        "--metadata",
        type=Path,
        help="Path to semantic metadata file (for CLI mode)"
    )
    parser.add_argument(
        "--tool-sequence",
        type=str,
        help="JSON tool sequence (for CLI mode)"
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Set up logging
    if config.log_file:
        file_handler = logging.FileHandler(config.log_file)
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        logger.addHandler(file_handler)
    
    logging.getLogger().setLevel(getattr(logging, config.log_level))
    
    # Create agent
    agent = LocalAgent(config)
    
    # CLI mode: Execute single task
    if args.task:
        # Task provided as JSON string
        result = agent.execute_task_from_json(args.task)
        print(json.dumps(result, indent=2))
        sys.exit(0 if result.get("status") == "completed" else 1)
    
    elif args.workbook and args.metadata and args.tool_sequence:
        # Task components provided separately
        try:
            metadata = load_metadata(args.metadata)
            tool_sequence = json.loads(args.tool_sequence)
            
            task = {
                "task_id": "cli-task",
                "workbook_path": str(args.workbook),
                "semantic_metadata": metadata,
                "tool_sequence": tool_sequence
            }
            
            result = agent.execute_task(task)
            print(json.dumps(result, indent=2))
            sys.exit(0 if result.get("status") == "completed" else 1)
        
        except Exception as e:
            logger.error(f"CLI execution failed: {e}", exc_info=True)
            print(json.dumps({
                "status": "error",
                "error": str(e)
            }, indent=2))
            sys.exit(1)
    
    else:
        # Service mode (future: polling for tasks)
        logger.info("Service mode not yet implemented")
        logger.info("Use --task, or --workbook + --metadata + --tool-sequence for CLI mode")
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

