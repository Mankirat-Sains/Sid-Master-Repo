"""FastAPI entrypoint for Fact Engine Service"""
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from config import settings
from planner import SemanticPlanner
from executor import FactExecutor
from composer import AnswerComposer
from models.answer import Answer

# Configure logging - ensure it's visible
log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    force=True  # Force reconfiguration even if logging was already configured
)

# Set log level for all our modules (using full module paths)
logging.getLogger("planner.planner").setLevel(log_level)
logging.getLogger("executor.executor").setLevel(log_level)
logging.getLogger("composer.composer").setLevel(log_level)
logging.getLogger("extractors").setLevel(log_level)
logging.getLogger("db").setLevel(log_level)
# Also set root logger to ensure everything is visible
logging.getLogger().setLevel(log_level)

logger = logging.getLogger(__name__)
logger.info(f"Logging configured at level: {settings.LOG_LEVEL}")
logger.info("=" * 80)
logger.info("Service starting - logs will appear below")
logger.info("=" * 80)

# Initialize FastAPI app
app = FastAPI(
    title="Fact Engine Service",
    description="Answer structural engineering questions by extracting and composing facts",
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

# Initialize components
planner: Optional[SemanticPlanner] = None
executor: Optional[FactExecutor] = None
composer: Optional[AnswerComposer] = None


@app.on_event("startup")
async def startup():
    """Initialize service components"""
    global planner, executor, composer
    
    try:
        planner = SemanticPlanner()
        logger.info("✅ Semantic planner initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize planner: {e}")
    
    try:
        use_graphql = settings.GRAPHQL_ENDPOINT is not None
        executor = FactExecutor(use_graphql=use_graphql)
        logger.info(f"✅ Fact executor initialized (GraphQL: {use_graphql})")
    except Exception as e:
        logger.error(f"❌ Failed to initialize executor: {e}")
    
    try:
        composer = AnswerComposer()
        logger.info("✅ Answer composer initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize composer: {e}")


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    from db.connection import db
    from db.graphql_client import graphql_client
    
    await db.close()
    graphql_client.close()
    logger.info("Service shutdown complete")


# Request/Response models
class QueryRequest(BaseModel):
    question: str
    use_graphql: Optional[bool] = None


class QueryResponse(BaseModel):
    answer: Answer
    fact_plan: Optional[dict] = None
    fact_result: Optional[dict] = None


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Fact Engine Service",
        "status": "running",
        "graphql_enabled": settings.GRAPHQL_ENDPOINT is not None
    }


@app.get("/health")
async def health():
    """Detailed health check"""
    return {
        "status": "healthy",
        "components": {
            "planner": planner is not None,
            "executor": executor is not None,
            "composer": composer is not None,
            "graphql": settings.GRAPHQL_ENDPOINT is not None
        }
    }


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Answer a natural language question about structural engineering data.
    
    This endpoint:
    1. Converts the question to a FactPlan (semantic planner)
    2. Executes the plan to extract facts (fact executor)
    3. Composes a human-readable answer (answer composer)
    """
    import asyncio
    import time
    
    logger.info("=" * 80)
    logger.info("MAIN: Starting query processing")
    logger.info(f"MAIN: Question: {request.question}")
    total_start_time = time.time()
    
    if not planner or not executor or not composer:
        logger.error("MAIN: Service components not initialized")
        raise HTTPException(
            status_code=503,
            detail="Service components not initialized"
        )
    
    try:
        # Step 1: Plan (fast, LLM call)
        logger.info("MAIN: Step 1 - Planning phase")
        plan_start_time = time.time()
        fact_plan = planner.plan(request.question)
        plan_time = (time.time() - plan_start_time) * 1000
        logger.info(f"MAIN: Planning complete - took {plan_time:.2f}ms")
        
        # Step 2: Execute (THIS CAN HANG - run in thread pool with timeout)
        logger.info("MAIN: Step 2 - Execution phase")
        use_graphql = request.use_graphql if request.use_graphql is not None else (settings.GRAPHQL_ENDPOINT is not None)
        logger.info(f"MAIN: Using GraphQL: {use_graphql}")
        
        if use_graphql != executor.use_graphql:
            # Recreate executor with correct mode
            logger.info(f"MAIN: Switching executor mode from {executor.use_graphql} to {use_graphql}")
            executor.use_graphql = use_graphql
        
        exec_start_time = time.time()
        # Run executor in thread pool to avoid blocking async event loop
        loop = asyncio.get_event_loop()
        fact_result = await asyncio.wait_for(
            loop.run_in_executor(None, executor.execute, fact_plan),
            timeout=180.0  # 3 minute timeout
        )
        exec_time = (time.time() - exec_start_time) * 1000
        logger.info(f"MAIN: Execution complete - took {exec_time:.2f}ms")
        logger.info(f"MAIN: Execution results - {len(fact_result.projects)} projects, {fact_result.total_elements_processed} elements processed")
        
        # Step 3: Compose (fast, LLM call)
        logger.info("MAIN: Step 3 - Composition phase")
        compose_start_time = time.time()
        answer = composer.compose(request.question, fact_result)
        compose_time = (time.time() - compose_start_time) * 1000
        logger.info(f"MAIN: Composition complete - took {compose_time:.2f}ms")
        
        # Convert to dict (Pydantic v2 compatible)
        fact_plan_dict = fact_plan.model_dump() if hasattr(fact_plan, 'model_dump') else fact_plan.dict()
        fact_result_dict = fact_result.model_dump() if hasattr(fact_result, 'model_dump') else fact_result.dict()
        
        total_time = (time.time() - total_start_time) * 1000
        logger.info("MAIN: Query processing complete")
        logger.info(f"MAIN: Timing summary - Planning: {plan_time:.2f}ms, Execution: {exec_time:.2f}ms, Composition: {compose_time:.2f}ms, Total: {total_time:.2f}ms")
        logger.info(f"MAIN: Final answer confidence: {answer.confidence:.2f}")
        logger.info("=" * 80)
        
        return QueryResponse(
            answer=answer,
            fact_plan=fact_plan_dict,
            fact_result=fact_result_dict
        )
    
    except asyncio.TimeoutError:
        total_time = (time.time() - total_start_time) * 1000
        logger.error(f"MAIN: Query execution timed out after {total_time:.2f}ms (3 minute limit)")
        raise HTTPException(
            status_code=504,
            detail="Query execution timed out. The GraphQL queries may be taking too long. Try reducing the number of projects or check your GraphQL connection."
        )
    except Exception as e:
        total_time = (time.time() - total_start_time) * 1000
        logger.error(f"MAIN: Error processing query after {total_time:.2f}ms: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )


@app.get("/facts")
async def list_facts():
    """List all available fact types"""
    from executor.registry import registry
    
    return {
        "available_facts": registry.list_available_facts()
    }


@app.get("/test-graphql")
async def test_graphql():
    """Test GraphQL connection with one project - useful for debugging"""
    from db.graphql_client import graphql_client
    
    try:
        logger.info("Testing GraphQL connection...")
        projects = graphql_client.get_projects(limit=1)
        
        if not projects:
            return {"error": "No projects found", "status": "failed"}
        
        project = projects[0]
        logger.info(f"Testing with project: {project.get('name', project.get('id'))}")
        
        root_id = graphql_client.get_latest_root_object_id(project["id"])
        
        if not root_id:
            return {
                "error": f"Could not get root object for project {project['id']}",
                "project": project.get("name"),
                "status": "failed"
            }
        
        logger.info(f"Got root object: {root_id}, fetching children...")
        objects = graphql_client.get_filtered_children(
            project_id=project["id"],
            root_object_id=root_id,
            limit=10  # Just get 10 objects for testing
        )
        
        return {
            "status": "success",
            "project": project.get("name"),
            "project_id": project["id"],
            "root_id": root_id,
            "objects_found": len(objects),
            "sample_objects": [
                {
                    "id": obj.get("id"),
                    "speckleType": obj.get("speckleType")
                }
                for obj in objects[:3]  # Return first 3 as samples
            ]
        }
    except Exception as e:
        logger.error(f"GraphQL test failed: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.SERVICE_HOST,
        port=settings.SERVICE_PORT,
        reload=True
    )

