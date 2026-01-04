"""
FastAPI endpoint for text-to-SQL service.
Similar to Supabase's generate-v4.ts but adapted for this system.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import os
from assistant import TextToSQLAssistant

app = FastAPI(title="Text-to-SQL API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    """Request model for text-to-SQL queries."""
    question: str = Field(..., description="Natural language question to convert to SQL")
    connection_string: str = Field(..., description="PostgreSQL connection string")
    model: Optional[str] = Field(default="gpt-4o", description="OpenAI model to use")
    execute: Optional[bool] = Field(default=True, description="Whether to execute the generated SQL")
    limit: Optional[int] = Field(default=None, description="Limit for SELECT queries")


class QueryResponse(BaseModel):
    """Response model for text-to-SQL queries."""
    sql: Optional[str] = Field(None, description="Generated SQL query")
    sql_queries: Optional[List[str]] = Field(None, description="List of all SQL queries (if multiple)")
    reasoning: Optional[str] = Field(None, description="Reasoning for the query approach")
    results: Optional[Dict[str, Any]] = Field(None, description="Query results if executed")
    results_list: Optional[List[Dict[str, Any]]] = Field(None, description="List of all execution results (if multiple queries)")
    error: Optional[str] = Field(None, description="Error message if any")
    tool_calls: Optional[List[Dict[str, Any]]] = Field(None, description="Tool calls made during generation")
    tool_results: Optional[List[Dict[str, Any]]] = Field(None, description="Results from tool calls")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    message: str


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "message": "Text-to-SQL API is running"
    }


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Convert natural language to SQL and optionally execute it.
    
    This endpoint:
    1. Takes a natural language question
    2. Uses AI to generate SQL based on the database schema
    3. Optionally executes the SQL and returns results
    """
    try:
        # Initialize assistant
        assistant = TextToSQLAssistant(
            connection_string=request.connection_string,
            model=request.model or "gpt-4o"
        )
        
        # Generate SQL
        if request.execute:
            result = assistant.query(request.question)
        else:
            result = assistant.generate_response(request.question)
            result["results"] = None
        
        # Format response
        response = QueryResponse(
            sql=result.get("sql"),
            sql_queries=result.get("sql_queries"),
            reasoning=result.get("reasoning"),
            results=result.get("results"),
            results_list=result.get("results_list"),
            error=result.get("error"),
            tool_calls=result.get("tool_calls", []),
            tool_results=result.get("tool_results", [])
        )
        
        return response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate", response_model=QueryResponse)
async def generate_only(request: QueryRequest):
    """
    Generate SQL only without executing it.
    Useful for reviewing SQL before execution.
    """
    try:
        assistant = TextToSQLAssistant(
            connection_string=request.connection_string,
            model=request.model or "gpt-4o"
        )
        
        result = assistant.generate_response(request.question)
        
        return QueryResponse(
            sql=result.get("sql"),
            sql_queries=result.get("sql_queries"),
            reasoning=result.get("reasoning"),
            results=None,
            results_list=None,
            error=result.get("error"),
            tool_calls=result.get("tool_calls", []),
            tool_results=result.get("tool_results", [])
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/schema")
async def get_schema(connection_string: str):
    """
    Get database schema information.
    Useful for understanding what tables and columns are available.
    """
    try:
        from tools import DatabaseTools
        db_tools = DatabaseTools(connection_string)
        
        tables = db_tools.list_tables()
        schema_info = db_tools.get_schema_info()
        
        return {
            "tables": tables,
            "schema_info": schema_info
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)


