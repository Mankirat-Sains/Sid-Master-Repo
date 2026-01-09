"""FastAPI server for SkyCiv Demo - Load models and run analysis"""
import logging
import json
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from skyciv_client import SkyCivClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SkyCiv Demo API",
    description="Load SkyCiv models and run structural analysis",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize SkyCiv client
skyciv_client: Optional[SkyCivClient] = None

# Path to model files
MODELS_DIR = Path(__file__).parent.parent / "models"


@app.on_event("startup")
async def startup():
    """Initialize service components"""
    global skyciv_client
    
    try:
        skyciv_client = SkyCivClient(
            username=os.getenv("SKYCIV_USERNAME", "admin@sidian.ai"),
            api_key=os.getenv("SKYCIV_API_KEY", "RxqSvo6QGRGphKlaLM2QcBKJqL1D4GXtFJLYMmt3cESAj82bjMTsCgkODJKHR88u")
        )
        logger.info("✅ SkyCiv client initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize SkyCiv client: {e}")


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    if skyciv_client:
        await skyciv_client.close()
    logger.info("Service shutdown complete")


# Request/Response models
class AnalyzeRequest(BaseModel):
    model_name: str  # "script1" or "script2"
    analysis_type: Optional[str] = "linear"


class AnalyzeResponse(BaseModel):
    session_id: str
    model_name: str
    status: str
    results: Optional[Dict[str, Any]] = None
    visualization_data: Dict[str, Any]
    error: Optional[str] = None


class ModelInfo(BaseModel):
    name: str
    description: str
    node_count: int
    member_count: int
    units: Dict[str, str]


@app.get("/models")
async def list_models():
    """List available model files"""
    models = []
    
    logger.info(f"Listing models from directory: {MODELS_DIR}")
    
    # Check for script1.json
    script1_path = MODELS_DIR / "script1.json"
    if script1_path.exists():
        try:
            with open(script1_path, 'r') as f:
                model_data = json.load(f)
                models.append({
                    "name": "script1",
                    "description": "SkyCiv Model 1",
                    "node_count": len(model_data.get("nodes", {})),
                    "member_count": len(model_data.get("members", {})),
                    "units": model_data.get("settings", {}).get("units", {})
                })
                logger.info(f"Loaded script1.json: {len(model_data.get('nodes', {}))} nodes, {len(model_data.get('members', {}))} members")
        except Exception as e:
            logger.error(f"Error reading script1.json: {e}", exc_info=True)
    
    # Check for script2.json
    script2_path = MODELS_DIR / "script2.json"
    if script2_path.exists():
        try:
            with open(script2_path, 'r') as f:
                model_data = json.load(f)
                models.append({
                    "name": "script2",
                    "description": "SkyCiv Model 2",
                    "node_count": len(model_data.get("nodes", {})),
                    "member_count": len(model_data.get("members", {})),
                    "units": model_data.get("settings", {}).get("units", {})
                })
                logger.info(f"Loaded script2.json: {len(model_data.get('nodes', {}))} nodes, {len(model_data.get('members', {}))} members")
        except Exception as e:
            logger.error(f"Error reading script2.json: {e}", exc_info=True)
    
    logger.info(f"Returning {len(models)} models")
    return {"models": models}


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_model(request: AnalyzeRequest):
    """
    Load a model and run SkyCiv analysis
    """
    try:
        # Load model file
        model_path = MODELS_DIR / f"{request.model_name}.json"
        if not model_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Model file not found: {request.model_name}.json"
            )
        
        logger.info(f"Loading model: {model_path}")
        with open(model_path, 'r') as f:
            model_data = json.load(f)
        
        # Start SkyCiv session
        logger.info("Starting SkyCiv session...")
        session_id = await skyciv_client.start_session()
        logger.info(f"Session started: {session_id}")
        
        # Upload model to SkyCiv
        logger.info("Uploading model to SkyCiv...")
        logger.info(f"Model has {len(model_data.get('nodes', {}))} nodes and {len(model_data.get('members', {}))} members")
        set_result = await skyciv_client.set_model(session_id, model_data)
        
        if set_result.get("status") != 0:
            error_msg = set_result.get("msg", "Unknown error")
            logger.error(f"SkyCiv model.set failed: {error_msg}")
            logger.error(f"Full error response: {json.dumps(set_result, indent=2)[:1000]}")
            raise HTTPException(
                status_code=400,
                detail=f"Failed to set model: {error_msg}"
            )
        
        logger.info("Model uploaded successfully")
        
        # Run analysis
        logger.info("Running analysis...")
        solve_result = await skyciv_client.solve(session_id, analysis_type=request.analysis_type)
        
        if solve_result.get("status") != 0:
            error_msg = solve_result.get("msg", "Analysis failed")
            raise HTTPException(
                status_code=400,
                detail=f"Analysis failed: {error_msg}"
            )
        
        logger.info("Analysis complete")
        
        # Get results
        logger.info("Fetching results...")
        results = await skyciv_client.get_results(session_id)
        
        # Format visualization data
        visualization_data = format_visualization_data(model_data, results)
        
        return AnalyzeResponse(
            session_id=session_id,
            model_name=request.model_name,
            status="success",
            results=results,
            visualization_data=visualization_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in analyze_model: {e}", exc_info=True)
        return AnalyzeResponse(
            session_id="",
            model_name=request.model_name,
            status="error",
            visualization_data={},
            error=str(e)
        )


@app.get("/model/{model_name}")
async def get_model_info(model_name: str):
    """Get information about a specific model"""
    model_path = MODELS_DIR / f"{model_name}.json"
    if not model_path.exists():
        raise HTTPException(status_code=404, detail="Model not found")
    
    with open(model_path, 'r') as f:
        model_data = json.load(f)
    
    return {
        "name": model_name,
        "nodes": model_data.get("nodes", {}),
        "members": model_data.get("members", {}),
        "settings": model_data.get("settings", {}),
        "node_count": len(model_data.get("nodes", {})),
        "member_count": len(model_data.get("members", {}))
    }


def format_visualization_data(model: Dict[str, Any], results: Dict[str, Any]) -> Dict[str, Any]:
    """Format model and results for 3D visualization"""
    nodes = model.get("nodes", {})
    members = model.get("members", {})
    
    # Extract node positions
    node_positions = []
    for node_id, node_data in nodes.items():
        node_positions.append({
            "id": str(node_id),
            "x": float(node_data.get("x", 0)),
            "y": float(node_data.get("y", 0)),
            "z": float(node_data.get("z", 0))
        })
    
    # Extract member connections
    member_lines = []
    for member_id, member_data in members.items():
        member_lines.append({
            "id": str(member_id),
            "start": str(member_data.get("node_A", member_data.get("node_start", ""))),
            "end": str(member_data.get("node_B", member_data.get("node_end", ""))),
            "section_id": member_data.get("section_id", 0)
        })
    
    # Extract forces/displacements if available
    forces = results.get("member_forces", {}) if results else {}
    displacements = results.get("displacements", {}) if results else {}
    
    # Get units for display
    units = model.get("settings", {}).get("units", {})
    vertical_axis = model.get("settings", {}).get("vertical_axis", "Y")
    
    return {
        "nodes": node_positions,
        "members": member_lines,
        "forces": forces,
        "displacements": displacements,
        "units": units,
        "vertical_axis": vertical_axis
    }


@app.get("/test-skyciv")
async def test_skyciv_connection():
    """Test SkyCiv API connection"""
    try:
        logger.info("Testing SkyCiv connection...")
        session_id = await skyciv_client.start_session()
        return {
            "status": "success",
            "session_id": session_id,
            "message": "Successfully connected to SkyCiv API"
        }
    except Exception as e:
        logger.error(f"SkyCiv connection test failed: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "message": "Failed to connect to SkyCiv API"
        }


@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "ok",
        "service": "skyciv-demo",
        "models_available": len(list(MODELS_DIR.glob("*.json"))) if MODELS_DIR.exists() else 0
    }

