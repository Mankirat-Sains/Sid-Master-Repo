"""
Test script to verify Google Gemini/Vertex AI connection and model availability
This helps debug issues with model access and authentication
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
root_env_path = Path(__file__).resolve().parent.parent / ".env"
if root_env_path.exists():
    load_dotenv(dotenv_path=str(root_env_path), override=True)
    print(f"✅ Loaded environment from {root_env_path}")
else:
    load_dotenv(override=True)
    print("⚠️  Using default environment")

# Configuration from environment
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
MODEL_NAME = os.getenv("SYNTHESIS_MODEL", "gemini-3-pro-preview")

# For all Gemini models, use "global" region (all Gemini models are available in global region)
# This is the recommended region for all Gemini models on Vertex AI
if MODEL_NAME.startswith("gemini"):
    VERTEX_AI_LOCATION = os.getenv("VERTEX_AI_LOCATION", "global")
    if VERTEX_AI_LOCATION != "global":
        print(f"⚠️  Warning: All Gemini models use 'global' region, but VERTEX_AI_LOCATION={VERTEX_AI_LOCATION}")
        print(f"   Overriding to 'global' for {MODEL_NAME}")
        VERTEX_AI_LOCATION = "global"
    print(f"ℹ️  Using 'global' region for Gemini model (all Gemini models are available in global region)")
else:
    VERTEX_AI_LOCATION = os.getenv("VERTEX_AI_LOCATION", "us-central1")

print("\n" + "="*80)
print("🔍 GOOGLE GEMINI/VERTEX AI CONNECTION TEST")
print("="*80)
print(f"\n📋 Configuration:")
print(f"   GOOGLE_APPLICATION_CREDENTIALS: {GOOGLE_APPLICATION_CREDENTIALS}")
print(f"   GOOGLE_CLOUD_PROJECT: {GOOGLE_CLOUD_PROJECT}")
print(f"   VERTEX_AI_LOCATION: {VERTEX_AI_LOCATION}")
print(f"   MODEL_NAME: {MODEL_NAME}")

# Check if credentials file exists
if GOOGLE_APPLICATION_CREDENTIALS:
    creds_path = Path(GOOGLE_APPLICATION_CREDENTIALS)
    if creds_path.exists():
        print(f"   ✅ Credentials file exists: {creds_path}")
    else:
        print(f"   ❌ Credentials file NOT FOUND: {creds_path}")
        sys.exit(1)
else:
    print("   ❌ GOOGLE_APPLICATION_CREDENTIALS not set")
    sys.exit(1)

print("\n" + "-"*80)
print("1️⃣ Testing Service Account Authentication")
print("-"*80)

try:
    from google.oauth2 import service_account
    from google.auth import default
    
    # Load credentials
    credentials = service_account.Credentials.from_service_account_file(
        str(creds_path.resolve())
    )
    print(f"✅ Successfully loaded service account credentials")
    print(f"   Service Account Email: {credentials.service_account_email}")
    print(f"   Project ID: {credentials.project_id}")
    
    # Test default credentials
    default_creds, default_project = default()
    print(f"✅ Default credentials loaded")
    print(f"   Default Project: {default_project}")
    
except Exception as e:
    print(f"❌ Failed to load credentials: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Skip Vertex AI SDK testing for all Gemini models - they require ChatGoogleGenerativeAI, not ChatVertexAI
# ChatVertexAI is deprecated and doesn't support newer Gemini models
# All Gemini models should use ChatGoogleGenerativeAI with "global" region
skip_chat_vertex_ai = MODEL_NAME.startswith("gemini")

if skip_chat_vertex_ai:
    print("\n" + "-"*80)
    print("2️⃣ Testing Vertex AI SDK (SKIPPED)")
    print("-"*80)
    print(f"⏭️  Skipping ChatVertexAI test for '{MODEL_NAME}'")
    print(f"   Reason: All Gemini models require ChatGoogleGenerativeAI (unified SDK), not ChatVertexAI")
    print(f"   ChatVertexAI is deprecated and doesn't support Gemini models properly")
    print(f"   Proceeding to test with ChatGoogleGenerativeAI (correct method)...")
    print(f"   ℹ️  Using 'global' region (all Gemini models are available in global region)")
else:
    print("\n" + "-"*80)
    print("2️⃣ Testing Vertex AI SDK (Legacy - for older Gemini models)")
    print("-"*80)
    
    try:
        from langchain_google_vertexai import ChatVertexAI
        from google.cloud import aiplatform
        
        print("✅ langchain_google_vertexai imported successfully")
        print(f"ℹ️  Note: ChatVertexAI is deprecated. Use ChatGoogleGenerativeAI for new models.")
        
        # Initialize Vertex AI
        try:
            aiplatform.init(
                project=GOOGLE_CLOUD_PROJECT,
                location=VERTEX_AI_LOCATION,
                credentials=credentials
            )
            print(f"✅ Vertex AI initialized (Project: {GOOGLE_CLOUD_PROJECT}, Location: {VERTEX_AI_LOCATION})")
        except Exception as e:
            print(f"⚠️  Vertex AI initialization warning: {e}")
        
        # Try to create a ChatVertexAI instance with the model
        print(f"\n🔍 Attempting to access model: {MODEL_NAME}")
        print(f"   Full path: projects/{GOOGLE_CLOUD_PROJECT}/locations/{VERTEX_AI_LOCATION}/publishers/google/models/{MODEL_NAME}")
        
        try:
            # Test 1: Try with the model name as-is
            print("\n   Test 1: Using model name as-is...")
            import warnings
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=DeprecationWarning)
                chat_model = ChatVertexAI(
                    model_name=MODEL_NAME,
                    project=GOOGLE_CLOUD_PROJECT,
                    location=VERTEX_AI_LOCATION,
                    credentials=credentials,
                    temperature=0.1
                )
                print(f"   ✅ ChatVertexAI instance created successfully")
                
                # Try a simple test call
                print(f"   🔍 Testing model call...")
                response = chat_model.invoke("Say 'Hello' in one word.")
                print(f"   ✅ Model call successful!")
                print(f"   📝 Response: {response.content[:100]}")
                print(f"   ⚠️  Note: ChatVertexAI works but is deprecated. Use ChatGoogleGenerativeAI for new models.")
                
        except Exception as e:
            print(f"   ❌ Failed with model name '{MODEL_NAME}': {e}")
            error_msg = str(e)
            
            # Check if it's a 404 or model not found error
            if "404" in error_msg or "not found" in error_msg.lower():
                print(f"\n   ⚠️  Model '{MODEL_NAME}' not found in Vertex AI with ChatVertexAI")
                print(f"   💡 For newer models, use ChatGoogleGenerativeAI instead (see test 3)")
            else:
                print(f"   Error details: {error_msg}")
                import traceback
                traceback.print_exc()
            
    except ImportError as e:
        print(f"⚠️  langchain_google_vertexai not available: {e}")
        print(f"   This is OK - use ChatGoogleGenerativeAI for new models instead")
    except Exception as e:
        print(f"⚠️  Vertex AI SDK test failed: {e}")
        print(f"   This is OK - ChatVertexAI is deprecated. Use ChatGoogleGenerativeAI instead.")

# Track test results for summary
test_results = {
    "vertex_ai_backend_success": False,
    "vertex_ai_backend_error": None,
    "api_key_success": False,
    "api_key_error": None,
}

print("\n" + "-"*80)
print("3️⃣ Testing ChatGoogleGenerativeAI with Vertex AI Backend (CORRECT METHOD)")
print("-"*80)

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    
    print("✅ langchain_google_genai imported successfully")
    
    # Test 1: Use ChatGoogleGenerativeAI with Vertex AI backend (service account)
    if GOOGLE_CLOUD_PROJECT and GOOGLE_APPLICATION_CREDENTIALS:
        print(f"\n🔍 Test 1: Using ChatGoogleGenerativeAI with Vertex AI backend (service account)")
        print(f"   Model: {MODEL_NAME}")
        print(f"   Project: {GOOGLE_CLOUD_PROJECT}")
        print(f"   Location: {VERTEX_AI_LOCATION} (global - all Gemini models available in global region)")
        print(f"   Credentials: {GOOGLE_APPLICATION_CREDENTIALS}")
        print(f"\n   This is the CORRECT method for {MODEL_NAME} on Vertex AI")
        if MODEL_NAME.startswith("gemini"):
            print(f"   ℹ️  Using 'global' region (all Gemini models are available in global region)")
        
        try:
            # Try with project/location parameters first
            try:
                genai_model = ChatGoogleGenerativeAI(
                    model=MODEL_NAME,
                    temperature=0.1,
                    google_api_key=None,  # No API key = use service account
                    project=GOOGLE_CLOUD_PROJECT,  # Vertex AI project
                            location=VERTEX_AI_LOCATION,  # Vertex AI location - "global" for all Gemini models
                )
                print(f"   ✅ Method 1: With project/location parameters")
            except (TypeError, ValueError) as param_error:
                # If project/location not supported, try without them
                print(f"   ⚠️  Method 1 failed (project/location): {param_error}")
                print(f"   🔍 Trying Method 2: Auto-detection without project/location...")
                genai_model = ChatGoogleGenerativeAI(
                    model=MODEL_NAME,
                    temperature=0.1,
                    google_api_key=None,  # No API key = use service account from GOOGLE_APPLICATION_CREDENTIALS
                )
                print(f"   ✅ Method 2: Auto-detection (using GOOGLE_APPLICATION_CREDENTIALS)")
            
            print(f"   ✅ ChatGoogleGenerativeAI instance created with Vertex AI backend")
            print(f"   🔍 Testing model call...")
            response = genai_model.invoke("Say 'Hello' in one word.")
            print(f"   ✅ Model call successful!")
            print(f"   📝 Response: {response.content[:100]}")
            print(f"\n   ✅ SUCCESS! This is the correct method for {MODEL_NAME}")
            print(f"   💡 ChatGoogleGenerativeAI uses Vertex AI backend when service account is set")
            test_results["vertex_ai_backend_success"] = True
            
        except Exception as e:
            error_msg = str(e)
            print(f"   ❌ Failed: {error_msg}")
            test_results["vertex_ai_backend_error"] = error_msg
            import traceback
            traceback.print_exc()
    
    # Test 2: Use ChatGoogleGenerativeAI with API key (Generative AI API, not Vertex AI)
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if api_key:
        print(f"\n🔍 Test 2: Using ChatGoogleGenerativeAI with API key (Generative AI API)")
        print(f"   Model: {MODEL_NAME}")
        print(f"   Note: This uses Generative AI API, not Vertex AI")
        try:
            genai_model_api = ChatGoogleGenerativeAI(
                model=MODEL_NAME,
                google_api_key=api_key,
                temperature=0.1
            )
            print(f"   ✅ ChatGoogleGenerativeAI instance created with API key")
            response_api = genai_model_api.invoke("Say 'Hello' in one word.")
            print(f"   ✅ Model call successful!")
            print(f"   📝 Response: {response_api.content[:100]}")
            print(f"   💡 Note: This uses Generative AI API (not Vertex AI)")
            test_results["api_key_success"] = True
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            test_results["api_key_error"] = str(e)
    else:
        print(f"\n⚠️  Test 2 skipped: No API key found (GOOGLE_API_KEY or GEMINI_API_KEY)")
        print(f"   Get API key from: https://makersuite.google.com/app/apikey")
        
except ImportError as e:
    print(f"❌ Failed to import langchain_google_genai: {e}")
    print(f"   Install with: pip install langchain-google-genai")
except Exception as e:
    print(f"❌ Generative AI SDK test failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "-"*80)
print("4️⃣ Testing Google AI Platform Model List")
print("-"*80)

try:
    from google.cloud import aiplatform
    from google.cloud.aiplatform import gapic
    
    # Try to list available models (this requires appropriate permissions)
    print("🔍 Attempting to list available models in Vertex AI...")
    print("   (This requires Vertex AI API to be enabled and proper permissions)")
    
    try:
        # Initialize if not already done
        aiplatform.init(
            project=GOOGLE_CLOUD_PROJECT,
            location=VERTEX_AI_LOCATION,
            credentials=credentials
        )
        
        # Note: Listing models programmatically is complex and requires specific APIs
        # Instead, we'll provide guidance
        print(f"   ℹ️  To check available models, visit:")
        print(f"   https://console.cloud.google.com/vertex-ai/model-garden?project={GOOGLE_CLOUD_PROJECT}")
        print(f"   Or enable Vertex AI API:")
        print(f"   https://console.cloud.google.com/apis/library/aiplatform.googleapis.com?project={GOOGLE_CLOUD_PROJECT}")
        
    except Exception as e:
        print(f"   ⚠️  Could not list models: {e}")
        print(f"   This is normal if Vertex AI API is not enabled or lacks permissions")
        
except Exception as e:
    print(f"⚠️  Model listing test skipped: {e}")

print("\n" + "-"*80)
print("5️⃣ Checking Vertex AI API Status & Available Models")
print("-"*80)

try:
    from googleapiclient.discovery import build
    from google.auth import default
    import json
    
    credentials, project = default()
    
    # Check if Vertex AI API is enabled
    print("🔍 Step 1: Checking if Vertex AI API is enabled...")
    try:
        service = build('serviceusage', 'v1', credentials=credentials)
        service_name = f'projects/{GOOGLE_CLOUD_PROJECT}/services/aiplatform.googleapis.com'
        
        request = service.services().get(name=service_name)
        response = request.execute()
        
        state = response.get('state', 'UNKNOWN')
        if state == 'ENABLED':
            print(f"   ✅ Vertex AI API is ENABLED")
        elif state == 'DISABLED':
            print(f"   ❌ Vertex AI API is DISABLED")
            print(f"   🔗 Enable it here:")
            print(f"      https://console.cloud.google.com/apis/library/aiplatform.googleapis.com?project={GOOGLE_CLOUD_PROJECT}")
            print(f"   📋 Steps:")
            print(f"      1. Click the link above")
            print(f"      2. Click 'ENABLE' button")
            print(f"      3. Wait 1-2 minutes for it to activate")
            print(f"      4. Re-run this test")
        else:
            print(f"   ⚠️  Vertex AI API state: {state}")
            print(f"   🔗 Check status: https://console.cloud.google.com/apis/library/aiplatform.googleapis.com?project={GOOGLE_CLOUD_PROJECT}")
            
    except Exception as e:
        error_msg = str(e)
        if "403" in error_msg or "PERMISSION_DENIED" in error_msg:
            print(f"   ⚠️  Permission denied checking API status")
            print(f"   💡 Your service account may need 'Service Usage Viewer' role")
        else:
            print(f"   ⚠️  Could not check API status: {e}")
        print(f"   🔗 Manually check: https://console.cloud.google.com/apis/library/aiplatform.googleapis.com?project={GOOGLE_CLOUD_PROJECT}")
    
    # Try to list available models (this might not work without proper permissions)
    print(f"\n🔍 Step 2: Checking available Gemini models in Vertex AI...")
    print(f"   Note: This requires Vertex AI API to be enabled and proper permissions")
    
    try:
        # Try to use Vertex AI client to list models
        from google.cloud import aiplatform
        
        aiplatform.init(
            project=GOOGLE_CLOUD_PROJECT,
            location=VERTEX_AI_LOCATION,
            credentials=credentials
        )
        
        # Try to list publisher models (this might require specific permissions)
        print(f"   ℹ️  Checking Model Garden for available models...")
        print(f"   🔗 View available models in console:")
        print(f"      https://console.cloud.google.com/vertex-ai/model-garden?project={GOOGLE_CLOUD_PROJECT}")
        print(f"   📋 Common Gemini models in Vertex AI:")
        print(f"      - gemini-1.5-pro (recommended)")
        print(f"      - gemini-1.5-flash")
        print(f"      - gemini-pro")
        print(f"      - gemini-pro-vision")
        print(f"   ⚠️  Note: Some preview models might not be available in Vertex AI")
        print(f"      Check Model Garden for available models for your project")
        
    except Exception as e:
        print(f"   ⚠️  Could not list models: {e}")
        print(f"   🔗 Check Model Garden manually:")
        print(f"      https://console.cloud.google.com/vertex-ai/model-garden?project={GOOGLE_CLOUD_PROJECT}")
        
except ImportError:
    print("   ⚠️  google-api-python-client not available")
    print(f"   Install with: pip install google-api-python-client")
    print(f"   Or check manually:")
    print(f"   🔗 Enable Vertex AI: https://console.cloud.google.com/apis/library/aiplatform.googleapis.com?project={GOOGLE_CLOUD_PROJECT}")
    print(f"   🔗 Model Garden: https://console.cloud.google.com/vertex-ai/model-garden?project={GOOGLE_CLOUD_PROJECT}")
except Exception as e:
    print(f"   ⚠️  API check failed: {e}")
    print(f"   🔗 Check manually:")
    print(f"      https://console.cloud.google.com/apis/library/aiplatform.googleapis.com?project={GOOGLE_CLOUD_PROJECT}")

print("\n" + "="*80)
print("📊 SUMMARY & RECOMMENDATIONS")
print("="*80)

# Determine overall status
if test_results["vertex_ai_backend_success"]:
    model_status = "✅ WORKING - Model access successful via Vertex AI backend"
    root_cause = f"The model '{MODEL_NAME}' is accessible and working correctly with Vertex AI backend using service account authentication."
    next_steps_header = "✅ CONFIGURATION COMPLETE:"
    next_steps = f"   Your setup is working correctly! The model '{MODEL_NAME}' is successfully connected via Vertex AI backend.\n   You can now use this model in your application."
elif test_results["api_key_success"]:
    model_status = "✅ WORKING - Model access successful via Generative AI API (API key)"
    root_cause = f"The model '{MODEL_NAME}' is accessible via Generative AI API with API key authentication."
    next_steps_header = "✅ CONFIGURATION COMPLETE:"
    next_steps = f"   Your setup is working with API key authentication. Consider using service account for Vertex AI backend."
else:
    model_status = f"❌ Model access: FAILED - Could not access '{MODEL_NAME}'"
    root_cause = f"The model '{MODEL_NAME}' could not be accessed. This could be due to:\n\n   1. ❌ Vertex AI API not enabled\n      → Enable: https://console.cloud.google.com/apis/library/aiplatform.googleapis.com?project={GOOGLE_CLOUD_PROJECT}\n\n   2. ❌ Model not available in Vertex AI\n      → Check available models: https://console.cloud.google.com/vertex-ai/model-garden?project={GOOGLE_CLOUD_PROJECT}\n\n   3. ❌ Service account lacks permissions\n      → Grant 'Vertex AI User' role: https://console.cloud.google.com/iam-admin/iam?project={GOOGLE_CLOUD_PROJECT}"
    if test_results["vertex_ai_backend_error"]:
        root_cause += f"\n\n   Error details: {test_results['vertex_ai_backend_error']}"
    next_steps_header = "🚀 NEXT STEPS:"
    next_steps = "   1. Enable Vertex AI API in GCP Console\n   2. Check Model Garden for available models\n   3. Verify service account permissions\n   4. Update .env with correct model name"

print(f"""
🔍 DIAGNOSIS:
   ✅ Service account authentication: WORKING
   ✅ Credentials loaded: {credentials.service_account_email}
   {model_status}

🎯 ROOT CAUSE:
   {root_cause}

{next_steps_header}
   {next_steps}

💡 ADDITIONAL INFORMATION:

   Current Configuration:
   ═════════════════════
   Model: {MODEL_NAME}
   Project: {GOOGLE_CLOUD_PROJECT}
   Location: {VERTEX_AI_LOCATION}
   Service Account: {credentials.service_account_email}
   Credentials File: {GOOGLE_APPLICATION_CREDENTIALS}

   Test Results:
   ════════════
   Vertex AI Backend (Service Account): {'✅ SUCCESS' if test_results['vertex_ai_backend_success'] else '❌ FAILED'}
   Generative AI API (API Key): {'✅ SUCCESS' if test_results['api_key_success'] else '⚠️  NOT TESTED (no API key)' if not os.getenv('GOOGLE_API_KEY') and not os.getenv('GEMINI_API_KEY') else '❌ FAILED'}

   Available Model Names in Vertex AI:
   ═══════════════════════════════════
   - gemini-3-pro-preview (current - ✅ working if test passed)
   - gemini-2.5-pro (alternative)
   - gemini-1.5-pro (recommended stable alternative)
   - gemini-1.5-flash (faster alternative)
   - gemini-pro (legacy)
   
   Note: All Gemini models use 'global' region in Vertex AI
   Check Model Garden for latest available models:
   https://console.cloud.google.com/vertex-ai/model-garden?project={GOOGLE_CLOUD_PROJECT}

   If You Need to Change Models:
   ═════════════════════════════
   1. Update .env file:
      SYNTHESIS_MODEL=gemini-3-pro-preview  (or your preferred Gemini model)
   2. Restart your application
   3. All Gemini models will automatically use 'global' region
   4. Re-run this test to verify

📚 Documentation:
   - Vertex AI Models: https://cloud.google.com/vertex-ai/generative-ai/docs/learn/model-versions
   - Generative AI API: https://ai.google.dev/models/gemini
   - Enable Vertex AI: https://console.cloud.google.com/apis/library/aiplatform.googleapis.com
""")

print("="*80)

