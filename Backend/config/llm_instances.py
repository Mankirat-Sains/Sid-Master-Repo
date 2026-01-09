"""
LLM Instance Configuration
Create and configure all LLM instances used throughout the system
"""
import os
import types

# Compat shim for newer openai package (>=1.x) with langchain_openai expecting DefaultHttpxClient
try:
    import openai  # type: ignore
except Exception:  # pragma: no cover
    openai = None

if openai:
    if not hasattr(openai, "DefaultHttpxClient"):
        class _DummyClient:
            def __init__(self, *args, **kwargs):
                pass
        openai.DefaultHttpxClient = _DummyClient  # type: ignore
    if not hasattr(openai, "DefaultAsyncHttpxClient"):
        class _DummyAsyncClient:
            def __init__(self, *args, **kwargs):
                pass
        openai.DefaultAsyncHttpxClient = _DummyAsyncClient  # type: ignore
    if not hasattr(openai, "AsyncOpenAI"):
        openai.AsyncOpenAI = getattr(openai, "AsyncClient", None) or getattr(openai, "OpenAI", None) or openai.DefaultAsyncHttpxClient  # type: ignore

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_anthropic import ChatAnthropic
from langchain_core.caches import BaseCache  # Fix for Pydantic v2 compatibility
from langchain_core.callbacks import Callbacks  # Fix for Pydantic v2 compatibility
from .settings import (
    FAST_MODEL, ROUTER_MODEL, GRADER_MODEL, SUPPORT_MODEL,
    SYNTHESIS_MODEL, CORRECTIVE_MODEL, EMB_MODEL,
    RAG_PLANNER_MODEL, VERIFY_MODEL, GROQ_API_KEY
)
from .logging_config import log_syn

# Try to import Groq SDK and create custom wrapper - if not available, will fall back to OpenAI
try:
    from groq import Groq
    from langchain_core.language_models.chat_models import BaseChatModel
    from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage
    from langchain_core.outputs import ChatGeneration, ChatResult
    from langchain_core.callbacks.manager import CallbackManagerForLLMRun
    from typing import Optional, List, Any, Iterator
    from pydantic import Field
    import os
    
    class ChatGroq(BaseChatModel):
        """Custom Groq wrapper compatible with LangChain 0.3.x"""
        
        model: str = Field(..., description="The model name to use")
        temperature: float = Field(default=0, description="Temperature for sampling")
        groq_api_key: Optional[str] = Field(default=None, description="Groq API key")
        max_tokens: Optional[int] = Field(default=None, description="Maximum tokens to generate")
        max_retries: int = Field(default=2, description="Maximum number of retries")
        timeout: Optional[float] = Field(default=None, description="Request timeout")
        
        def __init__(self, model: str, temperature: float = 0, groq_api_key: Optional[str] = None, **kwargs):
            # Get API key from parameter or environment
            api_key = groq_api_key or os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY must be provided or set in environment")
            
            # Pass all fields to super().__init__() for Pydantic v2 validation
            super().__init__(
                model=model,
                temperature=temperature,
                groq_api_key=api_key,
                max_tokens=kwargs.get("max_tokens"),
                max_retries=kwargs.get("max_retries", 2),
                timeout=kwargs.get("timeout"),
            )
            self._client = Groq(api_key=api_key)
        
        @property
        def _llm_type(self) -> str:
            return "groq"
        
        def _generate(
            self,
            messages: List[BaseMessage],
            stop: Optional[List[str]] = None,
            run_manager: Optional[CallbackManagerForLLMRun] = None,
            **kwargs: Any,
        ) -> ChatResult:
            # Convert LangChain messages to Groq format
            groq_messages = []
            for msg in messages:
                if isinstance(msg, HumanMessage):
                    groq_messages.append({"role": "user", "content": msg.content})
                elif isinstance(msg, AIMessage):
                    groq_messages.append({"role": "assistant", "content": msg.content})
                elif isinstance(msg, SystemMessage):
                    groq_messages.append({"role": "system", "content": msg.content})
            
            # Prepare API call parameters
            api_params = {
                "model": self.model,
                "messages": groq_messages,
                "temperature": self.temperature,
            }
            if self.max_tokens:
                api_params["max_tokens"] = self.max_tokens
            if stop:
                api_params["stop"] = stop
            api_params.update(kwargs)
            
            # Call Groq API with retries
            import time
            last_error = None
            for attempt in range(self.max_retries + 1):
                try:
                    response = self._client.chat.completions.create(**api_params)
                    break
                except Exception as e:
                    last_error = e
                    if attempt < self.max_retries:
                        time.sleep(2 ** attempt)  # Exponential backoff
                    else:
                        raise last_error
            
            # Convert response to LangChain format
            message = AIMessage(content=response.choices[0].message.content)
            generation = ChatGeneration(message=message)
            return ChatResult(generations=[generation])
        
        def _stream(
            self,
            messages: List[BaseMessage],
            stop: Optional[List[str]] = None,
            run_manager: Optional[CallbackManagerForLLMRun] = None,
            **kwargs: Any,
        ) -> Iterator[ChatGeneration]:
            # Convert LangChain messages to Groq format
            groq_messages = []
            for msg in messages:
                if isinstance(msg, HumanMessage):
                    groq_messages.append({"role": "user", "content": msg.content})
                elif isinstance(msg, AIMessage):
                    groq_messages.append({"role": "assistant", "content": msg.content})
                elif isinstance(msg, SystemMessage):
                    groq_messages.append({"role": "system", "content": msg.content})
            
            # Prepare API call parameters
            api_params = {
                "model": self.model,
                "messages": groq_messages,
                "temperature": self.temperature,
                "stream": True,
            }
            if self.max_tokens:
                api_params["max_tokens"] = self.max_tokens
            if stop:
                api_params["stop"] = stop
            api_params.update(kwargs)
            
            # Stream from Groq API
            stream = self._client.chat.completions.create(**api_params)
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield ChatGeneration(message=AIMessage(content=chunk.choices[0].delta.content))
    
    GROQ_AVAILABLE = True
except ImportError as e:
    GROQ_AVAILABLE = False
    log_syn.warning(f"⚠️  Groq SDK not installed. Install with: pip install groq")
    log_syn.warning(f"   Error: {e}")

# Fix for Pydantic v2 compatibility - rebuild model before instantiation
ChatOpenAI.model_rebuild()

# =============================================================================
# HELPER FUNCTION: Create LLM instance (Groq or OpenAI)
# =============================================================================
def create_llm_instance(model_name: str, temperature: float = 0, **kwargs):
    """
    Create an LLM instance using Groq if available and model is a Groq model,
    otherwise fall back to OpenAI.
    
<<<<<<< Updated upstream
    Groq models: llama-3.1-*, mixtral-*, gemma-*, qwen-*
    
    Note: Groq doesn't support response_format parameter, so it's filtered out for Groq models.
    """
    # Check if model is a Groq model
    groq_models = ["llama-3.1", "mixtral", "gemma", "qwen"]
    is_groq_model = any(model_name.startswith(prefix) for prefix in groq_models)
    
    if is_groq_model and GROQ_AVAILABLE and GROQ_API_KEY:
        try:
            # Remove response_format for Groq (not supported)
            groq_kwargs = {k: v for k, v in kwargs.items() if k != "response_format"}
            return ChatGroq(
                model=model_name,
                temperature=temperature,
                groq_api_key=GROQ_API_KEY,
                **groq_kwargs
            )
        except Exception as e:
            log_syn.warning(f"⚠️  Failed to create Groq instance for {model_name}: {e}. Falling back to OpenAI.")
            return ChatOpenAI(model=FAST_MODEL, temperature=temperature, **kwargs)
    else:
        # Use OpenAI for non-Groq models or if Groq is not available
=======
    Groq models: llama-3.3-*, llama-3.1-*, mixtral-*, gemma-*
    
    Note: Groq doesn't support response_format parameter, so it's filtered out for Groq models.
    """
    # Check if model is a Groq model (confirmed working models with full paths)
    # Groq supports models with prefixes like meta-llama/, openai/, etc.
    groq_models = [
        "llama-3.3",              # llama-3.3-70b-versatile
        "llama-3.1",              # llama-3.1-8b-instant
        "mixtral",                # mixtral-8x7b-32768
        "gemma",                  # gemma-7b-it
        "meta-llama/",            # meta-llama/llama-4-scout-17b-16e-instruct
        "openai/gpt-oss",         # openai/gpt-oss-120b, openai/gpt-oss-20b
        "moonshotai/kimi",        # moonshotai/kimi-k2-instruct
        "qwen/qwen3"              # qwen/qwen3-32b
    ]
    is_groq_model = any(model_name.startswith(prefix) for prefix in groq_models)
    
    # Debug logging
    log_syn.info(f"🔍 create_llm_instance: model_name='{model_name}', is_groq={is_groq_model}, GROQ_AVAILABLE={GROQ_AVAILABLE}, GROQ_API_KEY={'SET' if GROQ_API_KEY else 'NOT SET'}")
    
    if is_groq_model and GROQ_AVAILABLE and GROQ_API_KEY:
        # Remove response_format for Groq (not supported)
        groq_kwargs = {k: v for k, v in kwargs.items() if k != "response_format"}
        log_syn.info(f"✅ Creating Groq instance: {model_name}")
        # NO FALLBACK - raise error if Groq fails so we can debug
        return ChatGroq(
            model=model_name,
            temperature=temperature,
            groq_api_key=GROQ_API_KEY,
            **groq_kwargs
        )
    else:
        # Use OpenAI for non-Groq models or if Groq is not available
        if not is_groq_model:
            log_syn.warning(f"⚠️  Model '{model_name}' not recognized as Groq model, using OpenAI")
        elif not GROQ_AVAILABLE:
            log_syn.warning(f"⚠️  Groq SDK not available, using OpenAI for '{model_name}'")
        elif not GROQ_API_KEY:
            log_syn.warning(f"⚠️  GROQ_API_KEY not set, using OpenAI for '{model_name}'")
>>>>>>> Stashed changes
        return ChatOpenAI(model=model_name, temperature=temperature, **kwargs)


# =============================================================================
# FAST MODELS (cheaper, faster) - Using Groq for speed
# =============================================================================
llm_fast = create_llm_instance(FAST_MODEL, temperature=0)
llm_router = create_llm_instance(ROUTER_MODEL, temperature=0)
llm_grader = create_llm_instance(GRADER_MODEL, temperature=0)
llm_support = create_llm_instance(SUPPORT_MODEL, temperature=0)
llm_verify = create_llm_instance(
    VERIFY_MODEL, 
    temperature=0,
    max_retries=1, 
    timeout=25
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
# LOG MODEL CONFIGURATION AT STARTUP
# =============================================================================
def log_model_configuration():
    """Log all model configurations at system startup"""
    log_syn.info("=" * 80)
    log_syn.info("🤖 LLM MODEL CONFIGURATION")
    log_syn.info("=" * 80)
    
<<<<<<< Updated upstream
    # Fast models
    log_syn.info(f"⚡ FAST_MODEL: {FAST_MODEL} ({'Groq' if any(FAST_MODEL.startswith(p) for p in ['llama-3.1', 'mixtral', 'gemma', 'qwen']) else 'OpenAI'})")
    log_syn.info(f"⚡ ROUTER_MODEL: {ROUTER_MODEL} ({'Groq' if any(ROUTER_MODEL.startswith(p) for p in ['llama-3.1', 'mixtral', 'gemma', 'qwen']) else 'OpenAI'})")
    log_syn.info(f"⚡ GRADER_MODEL: {GRADER_MODEL} ({'Groq' if any(GRADER_MODEL.startswith(p) for p in ['llama-3.1', 'mixtral', 'gemma', 'qwen']) else 'OpenAI'})")
    log_syn.info(f"⚡ SUPPORT_MODEL: {SUPPORT_MODEL} ({'Groq' if any(SUPPORT_MODEL.startswith(p) for p in ['llama-3.1', 'mixtral', 'gemma', 'qwen']) else 'OpenAI'})")
    log_syn.info(f"⚡ RAG_PLANNER_MODEL: {RAG_PLANNER_MODEL} ({'Groq' if any(RAG_PLANNER_MODEL.startswith(p) for p in ['llama-3.1', 'mixtral', 'gemma', 'qwen']) else 'OpenAI'})")
    log_syn.info(f"⚡ VERIFY_MODEL: {VERIFY_MODEL} ({'Groq' if any(VERIFY_MODEL.startswith(p) for p in ['llama-3.1', 'mixtral', 'gemma', 'qwen']) else 'OpenAI'})")
=======
    # Helper function to check if model is Groq
    def is_groq_model(model_name):
        groq_prefixes = [
            "llama-3.3", "llama-3.1", "mixtral", "gemma",
            "meta-llama/", "openai/gpt-oss", "moonshotai/kimi", "qwen/qwen3"
        ]
        return any(model_name.startswith(p) for p in groq_prefixes)
    
    # Fast models
    log_syn.info(f"⚡ FAST_MODEL: {FAST_MODEL} ({'Groq' if is_groq_model(FAST_MODEL) else 'OpenAI'})")
    log_syn.info(f"⚡ ROUTER_MODEL: {ROUTER_MODEL} ({'Groq' if is_groq_model(ROUTER_MODEL) else 'OpenAI'})")
    log_syn.info(f"⚡ GRADER_MODEL: {GRADER_MODEL} ({'Groq' if is_groq_model(GRADER_MODEL) else 'OpenAI'})")
    log_syn.info(f"⚡ SUPPORT_MODEL: {SUPPORT_MODEL} ({'Groq' if is_groq_model(SUPPORT_MODEL) else 'OpenAI'})")
    log_syn.info(f"⚡ RAG_PLANNER_MODEL: {RAG_PLANNER_MODEL} ({'Groq' if is_groq_model(RAG_PLANNER_MODEL) else 'OpenAI'})")
    log_syn.info(f"⚡ VERIFY_MODEL: {VERIFY_MODEL} ({'Groq' if is_groq_model(VERIFY_MODEL) else 'OpenAI'})")
>>>>>>> Stashed changes
    
    # High-quality models (synthesis - keep as OpenAI/Anthropic)
    log_syn.info(f"🎯 SYNTHESIS_MODEL: {SYNTHESIS_MODEL} (OpenAI/Anthropic)")
    log_syn.info(f"🎯 CORRECTIVE_MODEL: {CORRECTIVE_MODEL} (OpenAI/Anthropic)")
    
    # Groq status
    if GROQ_AVAILABLE:
        if GROQ_API_KEY:
            log_syn.info(f"✅ Groq API: Configured")
        else:
            log_syn.warning(f"⚠️  Groq API: Key not found (GROQ_API_KEY)")
    else:
        log_syn.warning(f"⚠️  Groq: Not available (install with: pip install langchain-groq)")
    
    log_syn.info("=" * 80)

# Log configuration when module is imported
log_model_configuration()

# =============================================================================
# EMBEDDINGS
# =============================================================================
emb = OpenAIEmbeddings(model=EMB_MODEL)
