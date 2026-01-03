"""
LLM Instance Configuration
Create and configure all LLM instances used throughout the system
"""
import os
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_anthropic import ChatAnthropic
from langchain_core.caches import BaseCache  # Fix for Pydantic v2 compatibility
from langchain_core.callbacks import Callbacks  # Fix for Pydantic v2 compatibility
from .settings import (
    FAST_MODEL, ROUTER_MODEL, GRADER_MODEL, SUPPORT_MODEL,
    SYNTHESIS_MODEL, CORRECTIVE_MODEL, EMB_MODEL
)
from .logging_config import log_syn

# Fix for Pydantic v2 compatibility - rebuild model before instantiation
ChatOpenAI.model_rebuild()

# =============================================================================
# FAST MODELS (cheaper, faster)
# =============================================================================
llm_fast = ChatOpenAI(model=FAST_MODEL, temperature=0)
llm_router = ChatOpenAI(model=ROUTER_MODEL, temperature=0)
llm_grader = ChatOpenAI(model=GRADER_MODEL, temperature=0)
llm_support = ChatOpenAI(model=SUPPORT_MODEL, temperature=0)
llm_verify = ChatOpenAI(
    model=FAST_MODEL, 
    temperature=0,
    max_retries=1, 
    timeout=25,
    response_format={"type": "json_object"}
)


# =============================================================================
# HIGH-QUALITY MODELS (more expensive, better quality)
# =============================================================================
def make_llm(model_name: str, temperature: float = 0.1):
    """
    Create an LLM instance based on the model name.
    Supports both OpenAI and Anthropic models.
    """
    try:
        if model_name.startswith("claude"):
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not found in environment")
            return ChatAnthropic(
                model=model_name,
                temperature=temperature,
                anthropic_api_key=api_key
            )
        else:
            return ChatOpenAI(model=model_name, temperature=temperature)
    except Exception as e:
        log_syn.error(f"Failed to create LLM for {model_name}: {e}")
        raise


llm_synthesis = make_llm(SYNTHESIS_MODEL, temperature=0.1)
llm_corrective = make_llm(CORRECTIVE_MODEL, temperature=0.1)

# =============================================================================
# EMBEDDINGS
# =============================================================================
emb = OpenAIEmbeddings(model=EMB_MODEL)

