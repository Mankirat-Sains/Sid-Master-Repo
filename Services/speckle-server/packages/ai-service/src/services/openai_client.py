"""OpenAI client wrapper for chat interactions."""
from typing import List, Dict, Optional
from openai import AsyncOpenAI
from src.core.config import settings
import tiktoken


class OpenAIClient:
    """Wrapper for OpenAI API interactions."""
    
    def __init__(self):
        """Initialize OpenAI client."""
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.chat_model
        self.max_tokens = settings.max_tokens
        self.temperature = settings.temperature
        try:
            self.encoding = tiktoken.encoding_for_model(self.model)
        except KeyError:
            # Fallback to cl100k_base encoding if model not found
            self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        try:
            return len(self.encoding.encode(text))
        except Exception:
            # Fallback: approximate token count (1 token ≈ 4 characters)
            return len(text) // 4
    
    def truncate_context(self, context: str, max_tokens: int = 3000) -> str:
        """Truncate context to fit within token limit."""
        tokens = self.encoding.encode(context)
        if len(tokens) <= max_tokens:
            return context
        
        # Truncate to max_tokens
        truncated_tokens = tokens[:max_tokens]
        return self.encoding.decode(truncated_tokens)
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Send chat request to OpenAI.
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys
            system_prompt: Optional system prompt to prepend
        
        Returns:
            Assistant response text
        """
        # Build message list
        formatted_messages = []
        
        if system_prompt:
            formatted_messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        formatted_messages.extend(messages)
        
        # Call OpenAI API
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=formatted_messages,
            max_tokens=self.max_tokens,
            temperature=self.temperature
        )
        
        return response.choices[0].message.content

