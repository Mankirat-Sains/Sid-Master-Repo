#!/usr/bin/env python3
"""
Configuration Management for Local Agent

This module handles configuration loading and management for the local agent.
Configuration can be loaded from environment variables, config files, or
default values.

Author: Sidian Engineering Team
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    """
    Configuration for the local agent.
    
    Attributes:
        orchestrator_url: URL of the cloud orchestrator
        agent_id: Unique identifier for this agent instance
        agent_token: Authentication token for agent
        poll_interval: Seconds between polling for new tasks
        excel_visible: Whether to show Excel application
        calculation_timeout: Seconds to wait after triggering recalculation
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Path to log file (None for console only)
    """
    orchestrator_url: str
    agent_id: str
    agent_token: str
    poll_interval: float = 2.0
    excel_visible: bool = False
    calculation_timeout: float = 2.0
    log_level: str = "INFO"
    log_file: Optional[Path] = None


def load_config(config_path: Optional[Path] = None) -> AgentConfig:
    """
    Load configuration from file and environment variables.
    
    Configuration is loaded in this order (later overrides earlier):
    1. Default values
    2. Config file (if provided)
    3. Environment variables
    
    Environment variables:
        SIDOS_ORCHESTRATOR_URL: Cloud orchestrator URL
        SIDOS_AGENT_ID: Agent identifier
        SIDOS_AGENT_TOKEN: Authentication token
        SIDOS_POLL_INTERVAL: Polling interval in seconds
        SIDOS_EXCEL_VISIBLE: Show Excel (true/false)
        SIDOS_CALCULATION_TIMEOUT: Calculation timeout in seconds
        SIDOS_LOG_LEVEL: Logging level
        SIDOS_LOG_FILE: Path to log file
    
    Args:
        config_path: Optional path to JSON config file
    
    Returns:
        AgentConfig object with loaded configuration
    """
    # Start with defaults
    config = AgentConfig(
        orchestrator_url=os.getenv("SIDOS_ORCHESTRATOR_URL", "http://localhost:8000"),
        agent_id=os.getenv("SIDOS_AGENT_ID", "default-agent"),
        agent_token=os.getenv("SIDOS_AGENT_TOKEN", ""),
        poll_interval=float(os.getenv("SIDOS_POLL_INTERVAL", "2.0")),
        excel_visible=os.getenv("SIDOS_EXCEL_VISIBLE", "false").lower() == "true",
        calculation_timeout=float(os.getenv("SIDOS_CALCULATION_TIMEOUT", "2.0")),
        log_level=os.getenv("SIDOS_LOG_LEVEL", "INFO"),
        log_file=Path(os.getenv("SIDOS_LOG_FILE", "")) if os.getenv("SIDOS_LOG_FILE") else None
    )
    
    # Load from config file if provided
    if config_path and config_path.exists():
        import json
        try:
            with open(config_path, 'r') as f:
                file_config = json.load(f)
            
            # Override with file config
            if "orchestrator_url" in file_config:
                config.orchestrator_url = file_config["orchestrator_url"]
            if "agent_id" in file_config:
                config.agent_id = file_config["agent_id"]
            if "agent_token" in file_config:
                config.agent_token = file_config["agent_token"]
            if "poll_interval" in file_config:
                config.poll_interval = float(file_config["poll_interval"])
            if "excel_visible" in file_config:
                config.excel_visible = bool(file_config["excel_visible"])
            if "calculation_timeout" in file_config:
                config.calculation_timeout = float(file_config["calculation_timeout"])
            if "log_level" in file_config:
                config.log_level = file_config["log_level"]
            if "log_file" in file_config:
                config.log_file = Path(file_config["log_file"])
        
        except Exception as e:
            logger.warning(f"Failed to load config file: {e}")
    
    # Validate required fields
    if not config.agent_token:
        logger.warning("No agent token configured - authentication may fail")
    
    return config

