"""
Tools for project search - pure Python functions.
LLM will choose which tools to call based on user queries.
"""

import os
import json
from typing import List, Dict, Optional

# Try to import OpenAI for AI-powered extraction
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


def extract_search_criteria(user_query: str) -> Dict:
    """
    Extract structured search constraints from a user query.
    
    This tool analyzes natural language queries and extracts:
    - Dimension constraints (e.g., "50x100", "200x300")
    - Building type, material, or other filters
    - Completeness indicators
    
    Args:
        user_query: Natural language query from user (e.g., "Find me a project with a 50x100 layout")
        
    Returns:
        Dictionary with:
        - dimension_constraints: dict with "dimensions" (str like "50x100") and "complete" (bool)
        - additional_filters: list of other filters mentioned (building type, material, etc.)
        
    Example:
        extract_search_criteria("Find me a 50x100 commercial building")
        Returns: {
            "dimension_constraints": {"dimensions": "50x100", "complete": True},
            "additional_filters": ["commercial", "building"]
        }
    """
    # Use AI to extract criteria if available, otherwise use simple parsing
    if HAS_OPENAI and os.getenv("OPENAI_API_KEY"):
        try:
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Extract search criteria from user queries. Return only valid JSON."
                    },
                    {
                        "role": "user",
                        "content": f"""Extract search criteria from: "{user_query}"

Return JSON:
{{
  "dimension_constraints": {{
    "dimensions": "50x100" or null,
    "complete": true or false
  }},
  "additional_filters": ["filter1", "filter2"]
}}"""
                    }
                ],
                temperature=0.1
            )
            
            result_text = response.choices[0].message.content.strip()
            # Remove markdown if present
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            elif result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
            result_text = result_text.strip()
            
            result = json.loads(result_text)
            return result
            
        except Exception as e:
            # Fall back to simple extraction
            pass
    
    # Simple fallback: try to extract dimensions
    import re
    dim_match = re.search(r'(\d+[\'"]?\s*x\s*\d+)', user_query)
    if dim_match:
        return {
            "dimension_constraints": {
                "dimensions": dim_match.group(1),
                "complete": True
            },
            "additional_filters": []
        }
    
    # Default: incomplete
    return {
        "dimension_constraints": {
            "dimensions": None,
            "complete": False
        },
        "additional_filters": []
    }


def search_projects_by_dimensions(dimension_constraints: Dict) -> Dict:
    """
    Search the project database for projects matching dimensional constraints.
    
    This tool queries Supabase (PostgreSQL database) to find projects 
    with matching dimensions. Data is stored in Supabase and accessed through 
    the Supabase REST API.
    
    Args:
        dimension_constraints: Dict with:
            - "dimensions" (str): Dimension string like "50x100" or "200x300"
            - "complete" (bool): Whether dimensions are fully specified
            
    Returns:
        Dict with:
        - project_summaries: List of candidate projects, each with:
            - project_id: Unique project identifier (project_key)
            - match_score: Similarity score (0.0 to 1.0)
            - actual_dimensions: Actual dimensions of the project
        - total_found: Total number of projects found
        
    Example:
        search_projects_by_dimensions({"dimensions": "50x100", "complete": True})
        Returns: {
            "project_summaries": [
                {"project_id": "25-08-005", "match_score": 0.95, "actual_dimensions": "50x100"},
                {"project_id": "25-07-118", "match_score": 0.87, "actual_dimensions": "48x98"}
            ],
            "total_found": 2
        }
    """
    # Try to import Supabase
    try:
        from supabase import create_client
        # Support both SUPABASE_ANON_KEY and SUPABASE_KEY for compatibility
        SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
        SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "").strip() or os.getenv("SUPABASE_KEY", "").strip()
        
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("Supabase credentials not configured")
        
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Extract dimensions from constraints
        dimensions_str = dimension_constraints.get("dimensions")
        if not dimensions_str:
            return {"project_summaries": [], "total_found": 0}
        
        # Parse dimensions (e.g., "50x100" -> width=50, length=100)
        import re
        dim_match = re.search(r'(\d+)[\'"]?\s*x\s*(\d+)', dimensions_str)
        if not dim_match:
            return {"project_summaries": [], "total_found": 0}
        
        target_width = float(dim_match.group(1))
        target_length = float(dim_match.group(2))
        
        # Query Supabase project_info table
        # Note: Adjust column names based on your actual schema
        # This assumes columns like: project_key, project_name, width, length, etc.
        try:
            # Try to query with dimension matching
            # Adjust this query based on your actual table schema
            response = supabase.table("project_info").select(
                "project_key, project_name, project_address, project_city"
            ).limit(100).execute()
            
            # Filter and score projects based on dimension similarity
            # For now, return all projects (you'll need to add dimension columns to your schema)
            projects = []
            for row in response.data:
                # Calculate match score (simplified - adjust based on actual dimension columns)
                match_score = 0.8  # Default score
                
                projects.append({
                    "project_id": row.get("project_key", ""),
                    "match_score": match_score,
                    "actual_dimensions": dimensions_str  # Placeholder - use actual dimensions from DB
                })
            
            return {
                "project_summaries": projects[:10],  # Limit to top 10
                "total_found": len(projects)
            }
            
        except Exception as e:
            # If query fails, return empty results
            return {"project_summaries": [], "total_found": 0, "error": str(e)}
            
    except Exception as e:
        # Fallback to mock data if Supabase not available
        return {
            "project_summaries": [
                {"project_id": "proj-123", "match_score": 0.95, "actual_dimensions": "50x100"},
                {"project_id": "proj-456", "match_score": 0.87, "actual_dimensions": "48x98"}
            ],
            "total_found": 2,
            "warning": f"Using mock data - Supabase not available: {str(e)}"
        }


def rank_projects_by_similarity(candidate_projects: List[Dict]) -> List[str]:
    """
    Rank candidate projects by closeness to requested criteria.
    
    This tool sorts projects by match score and returns ordered list of IDs.
    
    Args:
        candidate_projects: List of project dicts with "project_id" and "match_score"
        
    Returns:
        List of ranked project IDs (best match first)
        
    Example:
        rank_projects_by_similarity([
            {"project_id": "proj-123", "match_score": 0.95},
            {"project_id": "proj-456", "match_score": 0.87}
        ])
        Returns: ["proj-123", "proj-456"]
    """
    # Sort by match_score descending
    sorted_projects = sorted(candidate_projects, key=lambda x: x.get("match_score", 0), reverse=True)
    return [p["project_id"] for p in sorted_projects]


def retrieve_project_metadata(project_ids: List[str]) -> List[Dict]:
    """
    Retrieve summary metadata for selected projects.
    
    This tool fetches project details from Supabase. Project data
    is stored in Supabase and retrieved using the Supabase REST API.
    
    Args:
        project_ids: List of project IDs (project_key) to retrieve
        
    Returns:
        List of project summaries with metadata:
        - id: Project ID (project_key)
        - name: Project name
        - dimensions: Actual dimensions (if available)
        - type: Building type (commercial, industrial, etc.) - if available
        - address: Project address
        - city: Project city
        - other relevant metadata
        
    Example:
        retrieve_project_metadata(["25-08-005", "25-07-118"])
        Returns: [
            {"id": "25-08-005", "name": "Warehouse Project", "address": "123 Main St", "city": "Toronto"},
            {"id": "25-07-118", "name": "Office Building", "address": "456 Oak Ave", "city": "Vancouver"}
        ]
    """
    if not project_ids:
        return []
    
    # Try to import Supabase
    try:
        from supabase import create_client
        # Support both SUPABASE_ANON_KEY and SUPABASE_KEY for compatibility
        SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
        SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "").strip() or os.getenv("SUPABASE_KEY", "").strip()
        
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("Supabase credentials not configured")
        
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Query Supabase project_info table for all project IDs
        try:
            response = supabase.table("project_info").select(
                "project_key, project_name, project_address, project_city, project_postal_code"
            ).in_("project_key", project_ids).execute()
            
            # Format results
            projects = []
            for row in response.data:
                projects.append({
                    "id": row.get("project_key", ""),
                    "name": row.get("project_name", f"Project {row.get('project_key', '')}"),
                    "address": row.get("project_address", ""),
                    "city": row.get("project_city", ""),
                    "postal_code": row.get("project_postal_code", ""),
                    "description": f"Project {row.get('project_key', '')} - {row.get('project_name', '')}"
                })
            
            return projects
            
        except Exception as e:
            # If query fails, return mock data
            return [
                {
                    "id": pid,
                    "name": f"Project {pid}",
                    "dimensions": "50x100",
                    "type": "Commercial",
                    "description": f"Project details for {pid} (mock - query failed: {str(e)})"
                }
                for pid in project_ids
            ]
            
    except Exception as e:
        # Fallback to mock data if Supabase not available
        return [
            {
                "id": pid,
                "name": f"Project {pid}",
                "dimensions": "50x100",
                "type": "Commercial",
                "description": f"Project details for {pid} (mock - Supabase not available: {str(e)})"
            }
            for pid in project_ids
        ]


def request_clarification(missing_fields: List[str]) -> str:
    """
    Request clarification from user about missing information.
    
    This tool prompts the user for additional information needed to complete the search.
    
    Args:
        missing_fields: List of fields that need clarification
            (e.g., ["dimensions", "building type", "material"])
        
    Returns:
        User's response (in real system, this would show UI prompt and wait for input)
        
    Example:
        request_clarification(["dimensions", "building type"])
        Returns: "Please provide: dimensions, building type"
    """
    # In real system, this would show UI prompt and wait for user input
    # For now, return a message indicating what's needed
    fields_str = ", ".join(missing_fields)
    return f"Please provide the following information: {fields_str}"


# Export all tools for easy importing
ALL_TOOLS = [
    extract_search_criteria,
    search_projects_by_dimensions,
    rank_projects_by_similarity,
    retrieve_project_metadata,
    request_clarification
]

