"""Configuration settings for the AI service."""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings."""
    
    # API Configuration
    api_key: str = "change-me-in-production"
    port: int = 8001
    host: str = "0.0.0.0"
    
    # CORS Configuration
    cors_origins: List[str] = ["*"]
    
    # Database Configuration (for future use with pgvector)
    database_url: str = ""
    
    # OpenAI Configuration
    openai_api_key: str = ""
    chat_model: str = "gpt-4o-mini"
    max_tokens: int = 20000
    temperature: float = 0.7
    
    # Speckle GraphQL Configuration
    speckle_graphql_url: str = "http://localhost:3000/graphql"
    speckle_service_token: str = ""
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = False


settings = Settings()


