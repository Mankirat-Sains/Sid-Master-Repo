#!/usr/bin/env python3
"""
FastAPI Service Wrapper for DOCX Editing Agent
==============================================
This service exposes DOCX read/edit/sync operations over HTTP so the main
backend and deep desktop agent can call deterministic document mutations.

Usage:
    python doc_agent_api.py --config config.json --port 8002
"""

import logging
from datetime import datetime
import argparse
from pathlib import Path
from typing import Any, Dict, List, Optional, Literal

import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from local_doc_agent import DocAgent, DocOperationError, load_config

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("doc_agent_api.log"), logging.StreamHandler()],
)
logger = logging.getLogger("DocAgentAPI")

# -----------------------------------------------------------------------------
# FastAPI app
# -----------------------------------------------------------------------------
app = FastAPI(
    title="DOCX Service Agent API",
    description="HTTP API for deterministic DOCX edits (insert/replace/delete/style/reorder).",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# Models
# -----------------------------------------------------------------------------


OPS_SCHEMA_VERSION = 1


class DocOpenRequest(BaseModel):
    file_path: str
    doc_id: Optional[str] = None


class DocOperation(BaseModel):
    op: Literal[
        "replace_text",
        "insert_paragraph",
        "insert_heading",
        "delete_block",
        "set_style",
        "reorder_blocks",
    ]
    target: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Target block spec, typically {'index': int}",
    )
    text: Optional[str] = None
    level: Optional[int] = None
    style: Optional[str] = None
    save_as: Optional[str] = None
    from_index: Optional[int] = None
    to_index: Optional[int] = None

    model_config = {"extra": "forbid"}


class DocApplyRequest(BaseModel):
    schema_version: int = Field(default=OPS_SCHEMA_VERSION)
    doc_id: Optional[str] = None
    file_path: Optional[str] = None
    ops: List[DocOperation]
    save_as: Optional[str] = None

    model_config = {"extra": "forbid"}


class DocExportRequest(BaseModel):
    doc_id: str
    target_path: Optional[str] = None


class DocHistoryResponse(BaseModel):
    doc_id: str
    total: int
    history: List[Dict[str, Any]]


# -----------------------------------------------------------------------------
# Globals
# -----------------------------------------------------------------------------
_agent_config: Optional[Dict[str, Any]] = None
_doc_agent: Optional[DocAgent] = None
_history: Dict[str, List[Dict[str, Any]]] = {}


def get_agent() -> DocAgent:
    """Return a configured DocAgent or raise if missing."""
    global _doc_agent, _agent_config
    if _doc_agent is None:
        if _agent_config is None:
            raise HTTPException(status_code=503, detail="Agent not configured. Call /api/doc/configure first.")
        _doc_agent = DocAgent(_agent_config)
        logger.info("DocAgent initialized.")
    return _doc_agent


def _record_history(doc_id: str, entry: Dict[str, Any]) -> None:
    """Store limited history for a doc."""
    global _history
    entry["timestamp"] = datetime.utcnow().isoformat()
    _history.setdefault(doc_id, []).append(entry)
    _history[doc_id] = _history[doc_id][-200:]


# -----------------------------------------------------------------------------
# API endpoints
# -----------------------------------------------------------------------------


@app.get("/")
async def root():
    return {
        "service": "DOCX Service Agent API",
        "version": "1.0.0",
        "status": "running",
        "agent_configured": _doc_agent is not None,
        "endpoints": {
            "health": "/health",
            "open": "/api/doc/open",
            "apply": "/api/doc/apply",
            "export": "/api/doc/export",
            "history": "/api/doc/history",
        },
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "agent_configured": _doc_agent is not None,
        "config_loaded": _agent_config is not None,
    }


@app.post("/api/doc/configure")
async def configure_agent(config: Dict[str, Any]):
    """
    Load configuration dynamically without restarting the service.
    Expected keys: workspace_dir (optional), docs: [{doc_id, file_path}]
    """
    global _agent_config, _doc_agent
    if not isinstance(config, dict):
        raise HTTPException(status_code=400, detail="Config must be a JSON object.")

    docs = config.get("docs", [])
    if not isinstance(docs, list):
        raise HTTPException(status_code=400, detail="Config.docs must be a list.")

    _agent_config = config
    _doc_agent = None  # recreated lazily
    logger.info(f"DocAgent configured with {len(docs)} docs")
    return {"status": "configured", "docs_count": len(docs), "message": "Doc agent configuration updated"}


@app.post("/api/doc/open")
async def open_doc(request: DocOpenRequest):
    agent = get_agent()
    try:
        opened = agent.open_doc(request.file_path, request.doc_id)
        _record_history(opened["doc_id"], {"event": "open", "file_path": opened["file_path"]})
        return opened
    except DocOperationError as exc:
        logger.error(f"Open failed: {exc}")
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:  # pragma: no cover - defensive
        logger.error(f"Unexpected open error: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/doc/apply")
async def apply_ops(request: DocApplyRequest, background_tasks: BackgroundTasks):
    agent = get_agent()
    if not request.doc_id and not request.file_path:
        raise HTTPException(status_code=400, detail="doc_id or file_path is required to apply operations.")
    if not request.ops:
        raise HTTPException(status_code=400, detail="ops list cannot be empty.")
    if request.schema_version != OPS_SCHEMA_VERSION:
        raise HTTPException(status_code=400, detail=f"Unsupported schema_version {request.schema_version}. Expected {OPS_SCHEMA_VERSION}.")

    def _run_ops():
        try:
            result = agent.apply_ops(
                doc_id=request.doc_id,
                file_path=str(Path(request.file_path).resolve()) if request.file_path else None,
                ops=[op.model_dump() for op in request.ops],
                save_as=request.save_as,
            )
            _record_history(result["doc_id"], {"event": "apply", "change_summary": result.get("change_summary", [])})
            return result
        except Exception as exc:
            logger.error(f"Apply failed: {exc}", exc_info=True)
            raise

    # Run synchronously so client gets result immediately (ops are quick)
    try:
        return _run_ops()
    except DocOperationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/doc/export")
async def export_doc(request: DocExportRequest):
    agent = get_agent()
    try:
        exported = agent.export_doc(request.doc_id, request.target_path)
        _record_history(exported["doc_id"], {"event": "export", "target_path": exported.get("target_path")})
        return exported
    except DocOperationError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:  # pragma: no cover - defensive
        logger.error(f"Export failed: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/doc/history", response_model=DocHistoryResponse)
async def get_history(doc_id: str, limit: int = 100):
    agent = get_agent()  # Ensure configured
    _ = agent  # silence lint - ensures configuration is loaded
    entries = _history.get(doc_id, [])[-limit:]
    return DocHistoryResponse(doc_id=doc_id, total=len(_history.get(doc_id, [])), history=entries)


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="DOCX Service Agent API")
    parser.add_argument("--config", help="Path to configuration JSON file")
    parser.add_argument("--port", type=int, default=8002, help="Port to run the API on")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    args = parser.parse_args()

    if args.config:
        try:
            global _agent_config
            _agent_config = load_config(args.config)
            logger.info(f"Loaded config from {args.config} with {len(_agent_config.get('docs', []))} docs")
        except Exception as exc:
            logger.error(f"Failed to load config: {exc}")
            logger.warning("Starting without configuration. Use /api/doc/configure to configure.")

    print("\n" + "=" * 60)
    print("🚀 DOCX SERVICE AGENT API")
    print("=" * 60)
    print(f"📡 Server: http://{args.host}:{args.port}")
    print(f"💚 Health check: http://{args.host}:{args.port}/health")
    print(f"📑 Open doc:    http://{args.host}:{args.port}/api/doc/open")
    print(f"🛠️  Apply ops:   http://{args.host}:{args.port}/api/doc/apply")
    print("=" * 60 + "\n")

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
