"""API routes for the AI service."""
from fastapi import APIRouter, HTTPException, Header, Depends
from pydantic import BaseModel
from typing import Optional
from src.services.chat import ChatService

router = APIRouter()


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str
    project_id: Optional[str] = None
    context: Optional[dict] = None


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    response: str
    model: str = "mock"


async def verify_api_key(x_api_key: str = Header(...)) -> str:
    """Verify API key from header."""
    from src.core.config import settings
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


@router.post("/chat")
async def chat(
    request: ChatRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Chat endpoint with OpenAI integration and Speckle context.
    
    When project_id is provided, fetches stream context (commits, comments) 
    via GraphQL and includes it in the AI prompt.
    """
    chat_service = ChatService()
    response = await chat_service.get_response(
        message=request.message,
        project_id=request.project_id,
        context=request.context
    )
    
    from src.core.config import settings
    return ChatResponse(
        response=response,
        model=settings.chat_model
    )


