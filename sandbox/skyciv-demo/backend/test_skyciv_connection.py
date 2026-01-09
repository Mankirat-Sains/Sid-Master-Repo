#!/usr/bin/env python3
"""Simple test script to debug SkyCiv API connection"""
import asyncio
import httpx
import json

SKYCIV_USERNAME = "admin@sidian.ai"
SKYCIV_API_KEY = "RxqSvo6QGRGphKlaLM2QcBKJqL1D4GXtFJLYMmt3cESAj82bjMTsCgkODJKHR88u"

# Correct endpoint with port 8085 (required for v3 API)
API_ENDPOINTS = [
    "https://api.skyciv.com:8085/v3",  # This is the correct one with port
    "https://api.skyciv.com/v3",  # Without port (may not work)
    "https://platform.skyciv.com/api/v3",  # Returns HTML
]

async def test_endpoint(client, api_url, payload, headers):
    """Test a single endpoint"""
    print(f"\n{'='*60}")
    print(f"Testing: {api_url}")
    print(f"{'='*60}")
    
    try:
        print("Sending request...")
        response = await client.post(api_url, json=payload, headers=headers)
        
        print(f"Response Status: {response.status_code}")
        content_type = response.headers.get('content-type', 'unknown')
        print(f"Content-Type: {content_type}")
        
        response_text = response.text
        
        # Check if it's JSON
        if 'application/json' in content_type.lower():
            print("✅ Got JSON response!")
            try:
                data = response.json()
                print(f"\nParsed JSON:")
                print(json.dumps(data, indent=2))
                
                # SkyCiv API returns responses in a functions array
                if "functions" in data:
                    print("\n✅ Response has 'functions' array (correct format)")
                    function_responses = data["functions"]
                    if function_responses and len(function_responses) > 0:
                        result = function_responses[0]
                        print(f"Function response status: {result.get('status')}")
                        
                        if result.get("status") == 0:
                            # session_id is directly in the function result object
                            session_id = result.get("session_id")
                            if not session_id:
                                # Try nested response structure
                                response_data = result.get("response", {})
                                session_id = response_data.get("session_id")
                            
                            if session_id:
                                print(f"\n🎉 SUCCESS! Session ID: {session_id}")
                                print(f"\n✅ Working endpoint: {api_url}")
                                return True
                            else:
                                print(f"⚠️  No session_id found in result: {result}")
                        else:
                            print(f"⚠️  API returned status: {result.get('status')}")
                            print(f"Message: {result.get('msg', 'No message')}")
                    else:
                        print("⚠️  Functions array is empty")
                else:
                    # Try old format (backwards compatibility)
                    print("\n⚠️  Response doesn't have 'functions' array (old format?)")
                    if data.get("status") == 0:
                        session_id = data.get("response", {}).get("session_id") or data.get("session_id")
                        if session_id:
                            print(f"\n🎉 SUCCESS! Session ID: {session_id}")
                            print(f"\n✅ Working endpoint: {api_url}")
                            return True
                    else:
                        print(f"⚠️  API returned status: {data.get('status')}")
                        print(f"Message: {data.get('msg', 'No message')}")
            except Exception as e:
                print(f"❌ Failed to parse JSON: {e}")
                print(f"Response: {response_text[:500]}")
        
        # Check if it's HTML
        elif 'text/html' in content_type.lower() or response_text.strip().startswith('<!DOCTYPE'):
            print("❌ Got HTML response (login page or error)")
            print(f"Response preview: {response_text[:200]}...")
        
        else:
            print(f"⚠️  Unexpected content type: {content_type}")
            print(f"Response: {response_text[:500]}")
            
    except httpx.TimeoutException:
        print("❌ Request timed out!")
    except httpx.RequestError as e:
        print(f"❌ Request error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    
    return False

async def test_connection():
    """Test SkyCiv API connection"""
    payload = {
        "auth": {
            "username": SKYCIV_USERNAME,
            "key": SKYCIV_API_KEY
        },
        "options": {
            "validate_input": True
        },
        "functions": [
            {
                "function": "S3D.session.start",
                "arguments": {
                    "keep_open": True
                }
            }
        ]
    }
    
    print("=" * 60)
    print("Testing SkyCiv API Connection")
    print("=" * 60)
    print(f"Username: {SKYCIV_USERNAME}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print()
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Try each endpoint
        for api_url in API_ENDPOINTS:
            success = await test_endpoint(client, api_url, payload, headers)
            if success:
                print(f"\n{'='*60}")
                print("✅ Found working endpoint!")
                print(f"{'='*60}")
                return
        
        print(f"\n{'='*60}")
        print("❌ None of the endpoints returned valid JSON")
        print(f"{'='*60}")
        print("\nPossible issues:")
        print("1. API credentials might be invalid or expired")
        print("2. API endpoint URL might have changed")
        print("3. API might require different authentication method")
        print("4. Check SkyCiv API documentation for correct endpoint")
        print("\nNext steps:")
        print("- Verify API key is active in SkyCiv account")
        print("- Check SkyCiv API documentation for correct endpoint")
        print("- Contact SkyCiv support if credentials are correct")

if __name__ == "__main__":
    asyncio.run(test_connection())
