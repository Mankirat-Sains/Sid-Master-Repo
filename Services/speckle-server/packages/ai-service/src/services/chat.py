"""Chat service for handling AI interactions."""
from typing import Optional, Dict
from src.services.openai_client import OpenAIClient
from src.services.speckle_client import SpeckleClient


class ChatService:
    """Service for handling chat interactions."""
    
    def __init__(self):
        """Initialize chat service with OpenAI and Speckle clients."""
        self.openai_client = OpenAIClient()
        self.speckle_client = SpeckleClient()
    
    async def get_response(
        self,
        message: str,
        project_id: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> str:
        """
        Get AI response for the given message with Speckle context.
        
        Args:
            message: User message
            project_id: Optional stream/project ID for context
            context: Optional additional context dict
        
        Returns:
            AI-generated response
        """
        # Build system prompt for BIM/AEC domain
        system_prompt = """You are an AI assistant specialized in Building Information Modeling (BIM) 
and Architecture, Engineering, and Construction (AEC) workflows. You help users understand and work 
with Speckle data models, which represent 3D geometry, building elements, and metadata.

When referencing Speckle objects, use their IDs in the format: streamId/objectId
Be helpful, accurate, and focus on practical BIM/AEC guidance."""
        
        # Build context from Speckle if project_id provided
        context_text = ""
        if project_id:
            try:
                # Build stream context (truncated to ~3000 tokens)
                stream_context = await self.speckle_client.build_stream_context(project_id)
                context_text = f"\n\nProject Context:\n{stream_context}"
                
                # Truncate context to fit token budget
                context_text = self.openai_client.truncate_context(context_text, max_tokens=3000)
            except Exception as e:
                # If context fetch fails, continue without it
                context_text = f"\n\n[Note: Could not fetch project context: {str(e)}]"
        
        # Add any additional context
        if context:
            context_text += f"\n\nAdditional context: {context}"
        
        # Build messages
        messages = [
            {
                "role": "user",
                "content": f"{message}{context_text}"
            }
        ]
        
        # Get response from OpenAI
        try:
            response = await self.openai_client.chat(
                messages=messages,
                system_prompt=system_prompt
            )
            return response
        except Exception as e:
            return f"Error generating response: {str(e)}"


