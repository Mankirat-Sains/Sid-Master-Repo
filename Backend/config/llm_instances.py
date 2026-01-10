"""
LLM Instance Configuration
Create and configure all LLM instances used throughout the system
"""
import os
import types
from pathlib import Path

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

# Try to import Google Gemini SDKs
GOOGLE_VERTEX_AI_AVAILABLE = False
GOOGLE_GENAI_AVAILABLE = False

# Import service_account once (needed for both)
try:
    from google.oauth2 import service_account
    SERVICE_ACCOUNT_AVAILABLE = True
except ImportError:
    SERVICE_ACCOUNT_AVAILABLE = False
    log_syn.warning("⚠️  google.oauth2.service_account not available. Install with: pip install google-auth google-auth-oauthlib")

# Try Vertex AI SDK first (required for service account auth)
# Note: ChatVertexAI is deprecated but necessary for service account authentication
try:
    from langchain_google_vertexai import ChatVertexAI
    GOOGLE_VERTEX_AI_AVAILABLE = True
    log_syn.info("✅ Google Vertex AI SDK available (required for service account auth)")
except ImportError as e:
    log_syn.warning(f"⚠️  Google Vertex AI SDK not installed. Install with: pip install langchain-google-vertexai google-cloud-aiplatform")
    log_syn.warning(f"   Error: {e}")

# Try Generative AI SDK as fallback
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    GOOGLE_GENAI_AVAILABLE = True
    log_syn.info("✅ Google Generative AI SDK available")
except ImportError as e:
    log_syn.warning(f"⚠️  Google Generative AI SDK not installed. Install with: pip install langchain-google-genai")
    log_syn.warning(f"   Error: {e}")

GOOGLE_AVAILABLE = GOOGLE_VERTEX_AI_AVAILABLE or GOOGLE_GENAI_AVAILABLE

# Load Google credentials from environment
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")

# For all Gemini models, use "global" region (all Gemini models are available in global)
# This is the recommended region for all Gemini models on Vertex AI
VERTEX_AI_LOCATION = os.getenv("VERTEX_AI_LOCATION", "global")

# Log if using Gemini models
SYNTHESIS_MODEL = os.getenv("SYNTHESIS_MODEL", "")
if SYNTHESIS_MODEL.startswith("gemini"):
    log_syn.info(f"ℹ️  Using 'global' region for Gemini models (all Gemini models are available in global region)")

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
    Supports OpenAI, Anthropic, and Google Gemini models.
    """
    try:
        # Check for Gemini models (gemini-2.5-pro, gemini-3-pro-preview, etc.)
        # Note: Newer models (2.5+, 3+) require ChatGoogleGenerativeAI with Vertex AI backend
        if model_name.startswith("gemini") and GOOGLE_AVAILABLE:
            log_syn.info(f"🔍 Detected Gemini model: {model_name}")
            
            # Check if service account credentials are set
            if not GOOGLE_APPLICATION_CREDENTIALS:
                raise ValueError(
                    "GOOGLE_APPLICATION_CREDENTIALS not found in environment. "
                    "Please set it to the path of your service account JSON file."
                )
            
            # Verify the credentials file exists
            creds_path = Path(GOOGLE_APPLICATION_CREDENTIALS)
            if not creds_path.exists():
                raise FileNotFoundError(
                    f"Google service account credentials file not found: {GOOGLE_APPLICATION_CREDENTIALS}"
                )
            
            log_syn.info(f"✅ Using Google service account credentials: {GOOGLE_APPLICATION_CREDENTIALS}")
            
            # Set GOOGLE_APPLICATION_CREDENTIALS environment variable if not already set
            # This ensures the Google client libraries can find the credentials
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(creds_path.resolve())
            
            # Load credentials explicitly to verify they're valid (if service_account is available)
            credentials = None
            if SERVICE_ACCOUNT_AVAILABLE:
                try:
                    credentials = service_account.Credentials.from_service_account_file(
                        str(creds_path.resolve())
                    )
                    log_syn.info(f"✅ Successfully loaded service account credentials for: {credentials.service_account_email}")
                except Exception as cred_error:
                    log_syn.error(f"❌ Failed to load service account credentials: {cred_error}")
                    raise
            
            # CRITICAL: For gemini-3-pro-preview and other new models, use ChatGoogleGenerativeAI 
            # from langchain-google-genai with Vertex AI backend (not ChatVertexAI).
            # ChatGoogleGenerativeAI supports BOTH API keys (Generative AI API) AND service accounts (Vertex AI backend).
            # When using service accounts, we configure it to use Vertex AI backend.
            
            # IMPORTANT: All Gemini models use "global" region
            # All Gemini models (gemini-1.5, gemini-2.5, gemini-3.0, etc.) are available in global region
            model_location = "global"
            if not model_name.startswith("gemini"):
                # Only use VERTEX_AI_LOCATION for non-Gemini models (if any)
                model_location = VERTEX_AI_LOCATION
            else:
                log_syn.info(f"ℹ️  Gemini model detected ({model_name}) - using 'global' region (all Gemini models available in global)")
            
            if GOOGLE_GENAI_AVAILABLE:
                # Check if we have service account credentials (preferred for Vertex AI)
                if GOOGLE_CLOUD_PROJECT and GOOGLE_APPLICATION_CREDENTIALS:
                    log_syn.info(f"✅ Using ChatGoogleGenerativeAI with Vertex AI backend (service account)")
                    log_syn.info(f"   Project: {GOOGLE_CLOUD_PROJECT}")
                    log_syn.info(f"   Location: {model_location} (global - all Gemini models available in global region)")
                    log_syn.info(f"   Model: {model_name}")
                    log_syn.info(f"   Credentials: {GOOGLE_APPLICATION_CREDENTIALS}")
                    log_syn.info(f"   Note: ChatGoogleGenerativeAI auto-detects Vertex AI backend from service account")
                    
                    # Use ChatGoogleGenerativeAI with Vertex AI backend
                    # When no API key is provided AND GOOGLE_APPLICATION_CREDENTIALS is set,
                    # it automatically uses Vertex AI backend with service account
                    try:
                        # Try with project/location if supported
                        return ChatGoogleGenerativeAI(
                            model=model_name,
                            temperature=temperature,
                            google_api_key=None,  # No API key = use service account
                            project=GOOGLE_CLOUD_PROJECT,  # Vertex AI project (may be auto-detected)
                            location=model_location,  # Vertex AI location - always "global" for all Gemini models
                        )
                    except TypeError:
                        # If project/location not supported, use without them (auto-detection)
                        log_syn.info(f"   Using auto-detection (project/location parameters not needed)")
                        return ChatGoogleGenerativeAI(
                            model=model_name,
                            temperature=temperature,
                            google_api_key=None,  # No API key = use service account from GOOGLE_APPLICATION_CREDENTIALS
                        )
                
                # Fallback: Use API key if available (Generative AI API, not Vertex AI)
                api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
                if api_key:
                    log_syn.info(f"✅ Using ChatGoogleGenerativeAI with Generative AI API (API key)")
                    log_syn.info(f"   Model: {model_name}")
                    return ChatGoogleGenerativeAI(
                        model=model_name,
                        temperature=temperature,
                        google_api_key=api_key
                    )
                else:
                    raise ValueError(
                        f"For Gemini model '{model_name}', you need either:\n"
                        f"  1. Service account with GOOGLE_APPLICATION_CREDENTIALS, GOOGLE_CLOUD_PROJECT set (recommended for Vertex AI)\n"
                        f"  2. API key with GOOGLE_API_KEY or GEMINI_API_KEY set (for Generative AI API)"
                    )
            
            # Fallback: Try deprecated ChatVertexAI if GenAI SDK not available
            # NOTE: ChatVertexAI doesn't support gemini-3-* models, but we'll try anyway as fallback
            if GOOGLE_VERTEX_AI_AVAILABLE and GOOGLE_CLOUD_PROJECT:
                import warnings
                log_syn.warning("⚠️  ChatGoogleGenerativeAI not available, falling back to deprecated ChatVertexAI")
                log_syn.warning(f"   Note: ChatVertexAI may not support {model_name} - install langchain-google-genai instead")
                
                # Use "global" region for all Gemini models (all Gemini models are available in global)
                fallback_location = "global" if model_name.startswith("gemini") else VERTEX_AI_LOCATION
                if model_name.startswith("gemini"):
                    log_syn.warning(f"   ⚠️  Using 'global' region for Gemini model - ChatVertexAI may not support {model_name}")
                
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore", message=".*ChatVertexAI.*deprecated.*")
                    warnings.filterwarnings("ignore", category=DeprecationWarning, module="langchain_google_vertexai")
                    if credentials:
                        return ChatVertexAI(
                            model_name=model_name,
                            temperature=temperature,
                            project=GOOGLE_CLOUD_PROJECT,
                            location=fallback_location,
                            credentials=credentials
                        )
                    else:
                        return ChatVertexAI(
                            model_name=model_name,
                            temperature=temperature,
                            project=GOOGLE_CLOUD_PROJECT,
                            location=fallback_location
                        )
            
            # If neither SDK is available
            raise ImportError(
                "langchain-google-genai is required for gemini-3-pro-preview and other new Gemini models. "
                "Install with: pip install langchain-google-genai google-auth google-auth-oauthlib"
            )
        
        # Check for Anthropic Claude models
        elif model_name.startswith("claude"):
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not found in environment")
            return ChatAnthropic(
                model=model_name,
                temperature=temperature,
                anthropic_api_key=api_key
            )
        
        # Default to OpenAI for other models
        else:
            log_syn.info(f"🔍 Using OpenAI for model: {model_name}")
            return ChatOpenAI(model=model_name, temperature=temperature)
            
    except Exception as e:
        log_syn.error(f"Failed to create LLM for {model_name}: {e}")
        import traceback
        log_syn.error(f"Traceback: {traceback.format_exc()}")
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
    
    # Fast models
    log_syn.info(f"⚡ FAST_MODEL: {FAST_MODEL} ({'Groq' if any(FAST_MODEL.startswith(p) for p in ['llama-3.1', 'mixtral', 'gemma', 'qwen']) else 'OpenAI'})")
    log_syn.info(f"⚡ ROUTER_MODEL: {ROUTER_MODEL} ({'Groq' if any(ROUTER_MODEL.startswith(p) for p in ['llama-3.1', 'mixtral', 'gemma', 'qwen']) else 'OpenAI'})")
    log_syn.info(f"⚡ GRADER_MODEL: {GRADER_MODEL} ({'Groq' if any(GRADER_MODEL.startswith(p) for p in ['llama-3.1', 'mixtral', 'gemma', 'qwen']) else 'OpenAI'})")
    log_syn.info(f"⚡ SUPPORT_MODEL: {SUPPORT_MODEL} ({'Groq' if any(SUPPORT_MODEL.startswith(p) for p in ['llama-3.1', 'mixtral', 'gemma', 'qwen']) else 'OpenAI'})")
    log_syn.info(f"⚡ RAG_PLANNER_MODEL: {RAG_PLANNER_MODEL} ({'Groq' if any(RAG_PLANNER_MODEL.startswith(p) for p in ['llama-3.1', 'mixtral', 'gemma', 'qwen']) else 'OpenAI'})")
    log_syn.info(f"⚡ VERIFY_MODEL: {VERIFY_MODEL} ({'Groq' if any(VERIFY_MODEL.startswith(p) for p in ['llama-3.1', 'mixtral', 'gemma', 'qwen']) else 'OpenAI'})")
    
    # High-quality models (synthesis - check for Gemini/OpenAI/Anthropic)
    synthesis_provider = "OpenAI"
    if SYNTHESIS_MODEL.startswith("gemini"):
        synthesis_provider = "Google Gemini"
    elif SYNTHESIS_MODEL.startswith("claude"):
        synthesis_provider = "Anthropic"
    
    corrective_provider = "OpenAI"
    if CORRECTIVE_MODEL.startswith("gemini"):
        corrective_provider = "Google Gemini"
    elif CORRECTIVE_MODEL.startswith("claude"):
        corrective_provider = "Anthropic"
    
    log_syn.info(f"🎯 SYNTHESIS_MODEL: {SYNTHESIS_MODEL} ({synthesis_provider})")
    log_syn.info(f"🎯 CORRECTIVE_MODEL: {CORRECTIVE_MODEL} ({corrective_provider})")
    
    # Groq status
    if GROQ_AVAILABLE:
        if GROQ_API_KEY:
            log_syn.info(f"✅ Groq API: Configured")
        else:
            log_syn.warning(f"⚠️  Groq API: Key not found (GROQ_API_KEY)")
    else:
        log_syn.warning(f"⚠️  Groq: Not available (install with: pip install groq)")
    
    # Google Gemini/Vertex AI status
    if GOOGLE_AVAILABLE:
        if GOOGLE_APPLICATION_CREDENTIALS:
            creds_path = Path(GOOGLE_APPLICATION_CREDENTIALS)
            if creds_path.exists():
                log_syn.info(f"✅ Google Service Account: {GOOGLE_APPLICATION_CREDENTIALS}")
                if GOOGLE_CLOUD_PROJECT:
                    log_syn.info(f"✅ Google Cloud Project: {GOOGLE_CLOUD_PROJECT}")
                if VERTEX_AI_LOCATION:
                    log_syn.info(f"✅ Vertex AI Location: {VERTEX_AI_LOCATION}")
                if GOOGLE_GENAI_AVAILABLE:
                    log_syn.info(f"✅ Using Generative AI SDK (ChatGoogleGenerativeAI - recommended)")
                    log_syn.info(f"   ChatGoogleGenerativeAI supports both service accounts (Vertex AI backend) and API keys")
                elif GOOGLE_VERTEX_AI_AVAILABLE:
                    log_syn.warning(f"⚠️  Using deprecated Vertex AI SDK (ChatVertexAI)")
                    log_syn.info(f"   Install langchain-google-genai for better Gemini model support")
            else:
                log_syn.warning(f"⚠️  Google credentials file not found: {GOOGLE_APPLICATION_CREDENTIALS}")
        else:
            log_syn.warning(f"⚠️  GOOGLE_APPLICATION_CREDENTIALS not set")
    else:
        if SYNTHESIS_MODEL.startswith("gemini") or CORRECTIVE_MODEL.startswith("gemini"):
            log_syn.warning(f"⚠️  Google Gemini SDK not available but Gemini model configured")
            log_syn.warning(f"   Install with: pip install langchain-google-genai google-auth google-auth-oauthlib")
    
    log_syn.info("=" * 80)

# Log configuration when module is imported
log_model_configuration()

# =============================================================================
# EMBEDDINGS
# =============================================================================
emb = OpenAIEmbeddings(model=EMB_MODEL)
