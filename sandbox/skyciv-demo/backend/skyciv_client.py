"""SkyCiv API Client - Handles all SkyCiv API interactions"""
import httpx
import logging
import json
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class SkyCivClient:
    """Client for SkyCiv S3D API v3"""
    
    # Correct API endpoint with port 8085 (required for v3 API)
    API_BASE_URL = "https://api.skyciv.com:8085/v3"
    
    def __init__(self, username: str, api_key: str):
        self.username = username
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=60.0)
        logger.info(f"SkyCiv client initialized for user: {username}")
    
    async def start_session(self) -> str:
        """Start a new SkyCiv session"""
        payload = {
            "auth": {
                "username": self.username,
                "key": self.api_key
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
        
        try:
            logger.info(f"Calling SkyCiv API: {self.API_BASE_URL}")
            logger.debug(f"Payload: {json.dumps(payload, indent=2)[:500]}")
            
            # Add proper headers for JSON API
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            response = await self.client.post(
                self.API_BASE_URL, 
                json=payload,
                headers=headers
            )
            
            # Log response details
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response content-type: {response.headers.get('content-type', 'unknown')}")
            
            response_text = response.text
            logger.info(f"Response text (first 500 chars): {response_text[:500]}")
            
            # Check if response is empty
            if not response_text or response_text.strip() == "":
                raise ValueError("SkyCiv API returned empty response")
            
            # Check if response is HTML (error page or redirect)
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' in content_type or response_text.strip().startswith('<!DOCTYPE') or response_text.strip().startswith('<html'):
                logger.error(f"SkyCiv returned HTML instead of JSON")
                logger.error(f"This usually means:")
                logger.error(f"  1. Wrong API endpoint URL")
                logger.error(f"  2. Authentication failed (invalid credentials)")
                logger.error(f"  3. API endpoint requires different format")
                raise ValueError(
                    f"SkyCiv API returned HTML page instead of JSON. "
                    f"This suggests the endpoint or authentication is incorrect. "
                    f"Status: {response.status_code}, Content-Type: {content_type}"
                )
            
            # Check status code before parsing
            if response.status_code != 200:
                logger.error(f"SkyCiv API returned non-200 status: {response.status_code}")
                raise ValueError(f"SkyCiv API returned status {response.status_code}: {response_text[:500]}")
            
            response.raise_for_status()
            
            try:
                data = response.json()
            except Exception as json_error:
                logger.error(f"Failed to parse JSON response: {response_text}")
                raise ValueError(f"Invalid JSON response from SkyCiv: {json_error}")
            
            # SkyCiv API returns responses in a functions array
            # Each function call returns: {"status": 0, "session_id": "...", "msg": "..."}
            if "functions" in data:
                # Multiple functions were called
                function_responses = data["functions"]
                if not function_responses or len(function_responses) == 0:
                    raise ValueError("SkyCiv API returned empty functions array")
                
                result = function_responses[0]  # Get first function result
            else:
                # Single function response (backwards compatibility)
                result = data
            
            # Check for errors
            if result.get("status") != 0:
                error_msg = result.get("msg", "Unknown error")
                raise ValueError(f"SkyCiv API error: {error_msg}")
            
            # Extract session_id - it's directly in the function result object
            session_id = result.get("session_id")
            if not session_id:
                # Try alternative response structure (nested response)
                response_data = result.get("response", {})
                session_id = response_data.get("session_id")
            
            if not session_id:
                logger.error(f"Response data: {result}")
                raise ValueError("Failed to get session_id from SkyCiv response")
            
            logger.info(f"SkyCiv session started: {session_id}")
            return session_id
            
        except httpx.HTTPStatusError as e:
            error_text = e.response.text if hasattr(e.response, 'text') else str(e)
            logger.error(f"HTTP error starting session: {error_text}")
            raise
        except Exception as e:
            logger.error(f"Error starting session: {e}", exc_info=True)
            raise
    
    async def set_model(self, session_id: str, model: Dict[str, Any]) -> Dict[str, Any]:
        """Upload model to SkyCiv"""
        payload = {
            "auth": {
                "username": self.username,
                "key": self.api_key
            },
            "options": {
                "validate_input": True,
                "return_base64_image_on_error": True
            },
            "functions": [
                {
                    "function": "S3D.model.set",
                    "arguments": {
                        "s3d_model": model
                    }
                }
            ]
        }
        
        try:
            response = await self.client.post(self.API_BASE_URL, json=payload)
            response.raise_for_status()
            
            response_text = response.text
            logger.info(f"SkyCiv set_model response (first 1000 chars): {response_text[:1000]}")
            
            if not response_text or response_text.strip() == "":
                raise ValueError("SkyCiv API returned empty response")
            
            try:
                data = response.json()
            except Exception as json_error:
                logger.error(f"Failed to parse JSON response: {response_text}")
                raise ValueError(f"Invalid JSON response from SkyCiv: {json_error}")
            
            # Parse functions array response
            if "functions" in data:
                function_responses = data["functions"]
                if not function_responses or len(function_responses) == 0:
                    raise ValueError("SkyCiv API returned empty functions array")
                result = function_responses[0]
            else:
                result = data
            
            status = result.get('status')
            logger.info(f"Model set response status: {status}")
            
            # Log full response if there's an error
            if status != 0:
                error_msg = result.get('msg', 'Unknown error')
                logger.error(f"❌ Model set failed with status {status}: {error_msg}")
                logger.error(f"Full error response: {json.dumps(result, indent=2)}")
            
            return result
            
        except httpx.HTTPStatusError as e:
            error_text = e.response.text if hasattr(e.response, 'text') else str(e)
            logger.error(f"HTTP error setting model: {error_text}")
            raise
        except Exception as e:
            logger.error(f"Error setting model: {e}", exc_info=True)
            raise
    
    async def solve(self, session_id: str, analysis_type: str = "linear") -> Dict[str, Any]:
        """Run structural analysis"""
        payload = {
            "auth": {
                "username": self.username,
                "key": self.api_key
            },
            "options": {
                "validate_input": True
            },
            "functions": [
                {
                    "function": "S3D.model.solve",
                    "arguments": {
                        "analysis_type": analysis_type,
                        "repair_model": True
                    }
                }
            ]
        }
        
        try:
            response = await self.client.post(self.API_BASE_URL, json=payload)
            response.raise_for_status()
            
            response_text = response.text
            logger.debug(f"SkyCiv solve response: {response_text[:500]}")
            
            if not response_text or response_text.strip() == "":
                raise ValueError("SkyCiv API returned empty response")
            
            try:
                data = response.json()
            except Exception as json_error:
                logger.error(f"Failed to parse JSON response: {response_text}")
                raise ValueError(f"Invalid JSON response from SkyCiv: {json_error}")
            
            # Parse functions array response
            if "functions" in data:
                function_responses = data["functions"]
                if not function_responses or len(function_responses) == 0:
                    raise ValueError("SkyCiv API returned empty functions array")
                result = function_responses[0]
            else:
                result = data
            
            logger.info(f"Solve response status: {result.get('status')}")
            return result
            
        except httpx.HTTPStatusError as e:
            error_text = e.response.text if hasattr(e.response, 'text') else str(e)
            logger.error(f"HTTP error solving: {error_text}")
            raise
        except Exception as e:
            logger.error(f"Error solving: {e}", exc_info=True)
            raise
    
    async def get_results(self, session_id: str) -> Dict[str, Any]:
        """Fetch analysis results"""
        results = {}
        
        # Get member forces
        try:
            forces_payload = {
                "auth": {
                    "username": self.username,
                    "key": self.api_key
                },
                "options": {
                    "validate_input": True
                },
                "functions": [
                    {
                        "function": "S3D.results.get",
                        "arguments": {
                            "result": "member_forces"
                        }
                    }
                ]
            }
            
            forces_response = await self.client.post(self.API_BASE_URL, json=forces_payload)
            forces_response.raise_for_status()
            
            response_text = forces_response.text
            if response_text and response_text.strip():
                try:
                    forces_data = forces_response.json()
                    # Parse functions array response
                    if "functions" in forces_data:
                        function_responses = forces_data["functions"]
                        if function_responses and len(function_responses) > 0:
                            result = function_responses[0]
                            if result.get("status") == 0:
                                # Response data can be in "response" or "data" field
                                results["member_forces"] = result.get("response") or result.get("data", {})
                    else:
                        if forces_data.get("status") == 0:
                            results["member_forces"] = forces_data.get("response") or forces_data.get("data", {})
                except Exception as json_error:
                    logger.warning(f"Failed to parse member forces JSON: {json_error}")
                    results["member_forces"] = {}
            else:
                results["member_forces"] = {}
        except Exception as e:
            logger.warning(f"Could not fetch member forces: {e}")
            results["member_forces"] = {}
        
        # Get displacements
        try:
            displacements_payload = {
                "auth": {
                    "username": self.username,
                    "key": self.api_key
                },
                "options": {
                    "validate_input": True
                },
                "functions": [
                    {
                        "function": "S3D.results.get",
                        "arguments": {
                            "result": "displacements"
                        }
                    }
                ]
            }
            
            displacements_response = await self.client.post(self.API_BASE_URL, json=displacements_payload)
            displacements_response.raise_for_status()
            
            response_text = displacements_response.text
            if response_text and response_text.strip():
                try:
                    displacements_data = displacements_response.json()
                    # Parse functions array response
                    if "functions" in displacements_data:
                        function_responses = displacements_data["functions"]
                        if function_responses and len(function_responses) > 0:
                            result = function_responses[0]
                            if result.get("status") == 0:
                                # Response data can be in "response" or "data" field
                                results["displacements"] = result.get("response") or result.get("data", {})
                    else:
                        if displacements_data.get("status") == 0:
                            results["displacements"] = displacements_data.get("response") or displacements_data.get("data", {})
                except Exception as json_error:
                    logger.warning(f"Failed to parse displacements JSON: {json_error}")
                    results["displacements"] = {}
            else:
                results["displacements"] = {}
        except Exception as e:
            logger.warning(f"Could not fetch displacements: {e}")
            results["displacements"] = {}
        
        return results
    
    async def analyze_model_combined(self, model: Dict[str, Any], analysis_type: str = "linear") -> Dict[str, Any]:
        """
        Run complete analysis in a single API call.
        This is the recommended approach - combines session start, model set, and solve.
        """
        payload = {
            "auth": {
                "username": self.username,
                "key": self.api_key
            },
            "options": {
                "validate_input": True,
                "return_base64_image_on_error": True
            },
            "functions": [
                {
                    "function": "S3D.session.start",
                    "arguments": {
                        "keep_open": True
                    }
                },
                {
                    "function": "S3D.model.set",
                    "arguments": {
                        "s3d_model": model
                    }
                },
                {
                    "function": "S3D.model.solve",
                    "arguments": {
                        "analysis_type": analysis_type,
                        "repair_model": True
                    }
                }
            ]
        }
        
        try:
            logger.info(f"Running combined analysis via SkyCiv API: {self.API_BASE_URL}")
            
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            response = await self.client.post(
                self.API_BASE_URL,
                json=payload,
                headers=headers
            )
            
            logger.info(f"Response status: {response.status_code}")
            
            response_text = response.text
            logger.info(f"Response (first 1000 chars): {response_text[:1000]}")
            
            if not response_text or response_text.strip() == "":
                raise ValueError("SkyCiv API returned empty response")
            
            # Check for HTML response (error)
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' in content_type or response_text.strip().startswith('<!DOCTYPE'):
                raise ValueError(f"SkyCiv API returned HTML instead of JSON. Status: {response.status_code}")
            
            response.raise_for_status()
            
            try:
                data = response.json()
            except Exception as json_error:
                logger.error(f"Failed to parse JSON: {response_text[:500]}")
                raise ValueError(f"Invalid JSON response: {json_error}")
            
            # Parse the functions array response
            if "functions" not in data:
                raise ValueError(f"Unexpected response format: {data}")
            
            function_responses = data["functions"]
            if len(function_responses) < 3:
                raise ValueError(f"Expected 3 function responses, got {len(function_responses)}")
            
            # Check each function result
            session_result = function_responses[0]
            set_result = function_responses[1]
            solve_result = function_responses[2]
            
            # Check session start
            if session_result.get("status") != 0:
                raise ValueError(f"Session start failed: {session_result.get('msg')}")
            
            session_id = session_result.get("session_id")
            logger.info(f"Session started: {session_id}")
            
            # Check model set
            if set_result.get("status") != 0:
                error_msg = set_result.get("msg", "Unknown error")
                logger.error(f"Model set failed: {error_msg}")
                logger.error(f"Full response: {json.dumps(set_result, indent=2)}")
                raise ValueError(f"Model set failed: {error_msg}")
            
            logger.info("Model set successfully")
            
            # Check solve
            if solve_result.get("status") != 0:
                error_msg = solve_result.get("msg", "Unknown error")
                logger.error(f"Solve failed: {error_msg}")
                raise ValueError(f"Solve failed: {error_msg}")
            
            logger.info("Model solved successfully")
            
            return {
                "session_id": session_id,
                "solve_result": solve_result,
                "data": data
            }
            
        except httpx.HTTPStatusError as e:
            error_text = e.response.text if hasattr(e.response, 'text') else str(e)
            logger.error(f"HTTP error in combined analysis: {error_text}")
            raise
        except Exception as e:
            logger.error(f"Error in combined analysis: {e}", exc_info=True)
            raise
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
        logger.info("SkyCiv client closed")

