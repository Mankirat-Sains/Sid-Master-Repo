#!/usr/bin/env python3
"""
FastAPI Service Wrapper for Excel Sync Agent
===========================================
This service exposes the Excel Sync Agent functionality via HTTP API endpoints.
It can run as a standalone service or be integrated with the main backend.

Usage:
    python agent_api.py --config config.json --port 8001
"""

import json
import logging
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Import the agent classes from local_sync_agent
from local_sync_agent import SyncAgent, ExcelReader, load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('agent_api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('AgentAPI')

# Global agent instance
_agent_instance: Optional[SyncAgent] = None
_agent_config: Optional[Dict] = None
_sync_history: List[Dict[str, Any]] = []
_sync_status: Dict[str, Any] = {
    "status": "stopped",
    "last_sync": None,
    "active_projects": [],
    "errors": []
}

# FastAPI app
app = FastAPI(
    title="Excel Sync Agent API",
    description="HTTP API for Excel Sync Agent",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class SyncTriggerRequest(BaseModel):
    project_id: Optional[str] = None  # If None, sync all projects
    force: bool = False

class SyncStatusResponse(BaseModel):
    status: str
    last_sync: Optional[str]
    active_projects: List[str]
    errors: List[str]
    agent_configured: bool

class ProjectInfo(BaseModel):
    project_id: str
    project_name: str
    excel_file: str
    sheet_name: str
    cell_mappings: Dict[str, str]
    last_synced: Optional[str] = None
    file_exists: bool = False

class SyncResult(BaseModel):
    success: bool
    project_id: str
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: str

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_agent() -> SyncAgent:
    """Get or initialize the agent instance"""
    global _agent_instance, _agent_config
    
    if _agent_instance is None:
        if _agent_config is None:
            raise HTTPException(
                status_code=503,
                detail="Agent not configured. Call /api/agent/configure first."
            )
        _agent_instance = SyncAgent(_agent_config)
        logger.info("Agent instance initialized")
    
    return _agent_instance

def update_sync_status(status: str, project_id: Optional[str] = None, error: Optional[str] = None):
    """Update global sync status"""
    global _sync_status
    
    _sync_status["status"] = status
    _sync_status["last_sync"] = datetime.utcnow().isoformat()
    
    if project_id and project_id not in _sync_status["active_projects"]:
        _sync_status["active_projects"].append(project_id)
    
    if error:
        _sync_status["errors"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "error": error,
            "project_id": project_id
        })
        # Keep only last 10 errors
        _sync_status["errors"] = _sync_status["errors"][-10:]

def add_sync_history(project_id: str, success: bool, message: str, data: Optional[Dict] = None):
    """Add entry to sync history"""
    global _sync_history
    
    entry = {
        "project_id": project_id,
        "success": success,
        "message": message,
        "data": data,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    _sync_history.append(entry)
    # Keep only last 100 entries
    _sync_history = _sync_history[-100:]

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Excel Sync Agent API",
        "version": "1.0.0",
        "status": "running",
        "agent_configured": _agent_instance is not None,
        "endpoints": {
            "health": "/health",
            "status": "/api/agent/status",
            "projects": "/api/agent/projects",
            "sync": "/api/agent/sync",
            "history": "/api/agent/history",
            "configure": "/api/agent/configure"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "agent_configured": _agent_instance is not None,
        "config_loaded": _agent_config is not None
    }

@app.post("/api/agent/configure")
async def configure_agent(config: Dict[str, Any]):
    """
    Configure the agent with a new configuration.
    This allows dynamic configuration without restarting the service.
    """
    global _agent_instance, _agent_config
    
    try:
        # Validate config structure
        required_keys = ["platform_url", "api_key", "projects"]
        for key in required_keys:
            if key not in config:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required config key: {key}"
                )
        
        # Validate projects
        if not isinstance(config["projects"], list) or len(config["projects"]) == 0:
            raise HTTPException(
                status_code=400,
                detail="Config must contain at least one project"
            )
        
        # Store config and reset agent instance
        _agent_config = config
        _agent_instance = None  # Will be recreated on next use
        
        logger.info(f"Agent configured with {len(config['projects'])} projects")
        
        return {
            "status": "configured",
            "projects_count": len(config["projects"]),
            "message": "Agent configuration updated successfully"
        }
    
    except Exception as e:
        logger.error(f"Configuration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/agent/status", response_model=SyncStatusResponse)
async def get_sync_status():
    """Get current sync status"""
    return SyncStatusResponse(
        status=_sync_status["status"],
        last_sync=_sync_status["last_sync"],
        active_projects=_sync_status["active_projects"],
        errors=[e.get("error", "") for e in _sync_status["errors"]],
        agent_configured=_agent_instance is not None
    )

@app.get("/api/agent/projects", response_model=List[ProjectInfo])
async def get_projects():
    """Get list of all configured projects with their status"""
    if _agent_config is None:
        raise HTTPException(
            status_code=503,
            detail="Agent not configured"
        )
    
    projects = []
    for project_config in _agent_config.get("projects", []):
        excel_path = Path(project_config.get("excel_file", ""))
        
        # Find last sync for this project
        last_synced = None
        for entry in reversed(_sync_history):
            if entry.get("project_id") == project_config.get("project_id"):
                if entry.get("success"):
                    last_synced = entry.get("timestamp")
                    break
        
        projects.append(ProjectInfo(
            project_id=project_config.get("project_id", ""),
            project_name=project_config.get("project_name", ""),
            excel_file=str(excel_path),
            sheet_name=project_config.get("sheet_name", ""),
            cell_mappings=project_config.get("cell_mappings", {}),
            last_synced=last_synced,
            file_exists=excel_path.exists()
        ))
    
    return projects

@app.post("/api/agent/sync", response_model=SyncResult)
async def trigger_sync(request: SyncTriggerRequest, background_tasks: BackgroundTasks):
    """
    Trigger a sync for a specific project or all projects.
    Returns immediately and syncs in the background.
    """
    if _agent_config is None:
        raise HTTPException(
            status_code=503,
            detail="Agent not configured"
        )
    
    agent = get_agent()
    
    if request.project_id:
        # Sync specific project
        project_config = None
        for proj in _agent_config.get("projects", []):
            if proj.get("project_id") == request.project_id:
                project_config = proj
                break
        
        if not project_config:
            raise HTTPException(
                status_code=404,
                detail=f"Project '{request.project_id}' not found"
            )
        
        # Run sync in background
        background_tasks.add_task(sync_project_task, project_config)
        
        return SyncResult(
            success=True,
            project_id=request.project_id,
            message=f"Sync initiated for project {request.project_id}",
            timestamp=datetime.utcnow().isoformat()
        )
    else:
        # Sync all projects
        background_tasks.add_task(sync_all_projects_task)
        
        return SyncResult(
            success=True,
            project_id="all",
            message="Sync initiated for all projects",
            timestamp=datetime.utcnow().isoformat()
        )

def sync_project_task(project_config: Dict):
    """Background task to sync a single project"""
    project_id = project_config.get("project_id", "unknown")
    
    try:
        update_sync_status("syncing", project_id)
        logger.info(f"Starting sync for project {project_id}")
        
        agent = get_agent()
        success = agent.sync_project(project_config)
        
        if success:
            # Read the data that was synced
            reader = ExcelReader(project_config.get("excel_file"))
            data = reader.read_cells(
                project_config.get("sheet_name"),
                project_config.get("cell_mappings", {})
            )
            
            add_sync_history(
                project_id,
                True,
                f"Successfully synced project {project_id}",
                data
            )
            update_sync_status("idle", project_id)
            logger.info(f"Successfully synced project {project_id}")
        else:
            add_sync_history(
                project_id,
                False,
                f"Failed to sync project {project_id}"
            )
            update_sync_status("idle", project_id, f"Sync failed for {project_id}")
            logger.error(f"Failed to sync project {project_id}")
    
    except Exception as e:
        error_msg = f"Error syncing project {project_id}: {str(e)}"
        logger.error(error_msg, exc_info=True)
        add_sync_history(project_id, False, error_msg)
        update_sync_status("idle", project_id, error_msg)

def sync_all_projects_task():
    """Background task to sync all projects"""
    try:
        update_sync_status("syncing")
        logger.info("Starting sync for all projects")
        
        agent = get_agent()
        agent.sync_all_projects()
        
        update_sync_status("idle")
        logger.info("Completed sync for all projects")
    
    except Exception as e:
        error_msg = f"Error syncing all projects: {str(e)}"
        logger.error(error_msg, exc_info=True)
        update_sync_status("idle", error=error_msg)

@app.get("/api/agent/history")
async def get_sync_history(limit: int = 50):
    """Get sync history"""
    return {
        "history": _sync_history[-limit:],
        "total": len(_sync_history)
    }

@app.get("/api/agent/project/{project_id}/data")
async def get_project_data(project_id: str):
    """Get current data from a project's Excel file without syncing"""
    if _agent_config is None:
        raise HTTPException(
            status_code=503,
            detail="Agent not configured"
        )
    
    project_config = None
    for proj in _agent_config.get("projects", []):
        if proj.get("project_id") == project_id:
            project_config = proj
            break
    
    if not project_config:
        raise HTTPException(
            status_code=404,
            detail=f"Project '{project_id}' not found"
        )
    
    excel_path = Path(project_config.get("excel_file", ""))
    if not excel_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Excel file not found: {excel_path}"
        )
    
    try:
        reader = ExcelReader(str(excel_path))
        data = reader.read_cells(
            project_config.get("sheet_name"),
            project_config.get("cell_mappings", {})
        )
        
        return {
            "project_id": project_id,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Error reading project data: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error reading Excel file: {str(e)}"
        )

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Excel Sync Agent API Service')
    parser.add_argument('--config', help='Path to configuration JSON file')
    parser.add_argument('--port', type=int, default=8001, help='Port to run the API on')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    
    args = parser.parse_args()
    
    # Load config if provided
    if args.config:
        try:
            global _agent_config
            _agent_config = load_config(args.config)
            logger.info(f"Loaded configuration from {args.config}")
            logger.info(f"Configured with {len(_agent_config.get('projects', []))} projects")
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            logger.warning("Starting without configuration. Use /api/agent/configure to configure.")
    
    print("\n" + "="*60)
    print("🚀 EXCEL SYNC AGENT API SERVICE")
    print("="*60)
    print(f"📡 Server: http://{args.host}:{args.port}")
    print(f"💚 Health check: http://{args.host}:{args.port}/health")
    print(f"📊 Status: http://{args.host}:{args.port}/api/agent/status")
    print("="*60 + "\n")
    
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="info"
    )

if __name__ == '__main__':
    main()
