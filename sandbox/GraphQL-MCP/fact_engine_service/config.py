"""Configuration for Fact Engine Service"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env from parent directory (GraphQL-MCP/.env)
parent_dir = Path(__file__).parent.parent
env_file = parent_dir / ".env"
if env_file.exists():
    load_dotenv(env_file)
else:
    # Fallback to local .env
    load_dotenv()


class Settings(BaseSettings):
    """Application settings"""
    
    # Database Configuration
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_NAME: str = os.getenv("DB_NAME", "speckle")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_USE_ASYNC: bool = os.getenv("DB_USE_ASYNC", "false").lower() == "true"
    
    # GraphQL Configuration
    GRAPHQL_ENDPOINT: Optional[str] = os.getenv("GRAPHQL_ENDPOINT")
    GRAPHQL_AUTH_TOKEN: Optional[str] = os.getenv("GRAPHQL_AUTH_TOKEN")
    GRAPHQL_USE_MCP: bool = os.getenv("GRAPHQL_USE_MCP", "false").lower() == "true"
    
    # LLM Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")
    PLANNER_TEMPERATURE: float = float(os.getenv("PLANNER_TEMPERATURE", "0.1"))
    COMPOSER_TEMPERATURE: float = float(os.getenv("COMPOSER_TEMPERATURE", "0.3"))
    
    # Service Configuration
    SERVICE_HOST: str = os.getenv("SERVICE_HOST", "0.0.0.0")
    SERVICE_PORT: int = int(os.getenv("SERVICE_PORT", "8000"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

