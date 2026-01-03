"""Shared SQL query templates for candidate discovery"""
from typing import List, Optional, Dict, Any


def build_candidate_discovery_query(
    commit_id: Optional[str] = None,
    speckle_types: Optional[List[str]] = None,
    closure_ids: Optional[List[str]] = None,
    string_filters: Optional[Dict[str, str]] = None
) -> tuple[str, Dict[str, Any]]:
    """
    Build SQL query for Phase 1: Candidate Discovery
    
    Follows canonical pattern:
    Step A: Identify model scope (commit → root)
    Step B: Query elements within closure scope
    Step C: Filter for engineering meaning
    
    This phase uses coarse filters to reduce millions of elements to hundreds.
    Never inspects full projects or returns raw JSON to LLM.
    
    Args:
        commit_id: Optional commit ID to scope the query
        speckle_types: List of Speckle types to filter (e.g., ['Column', 'Beam'])
        closure_ids: List of object IDs to check in closure
        string_filters: Dict of field -> value for string matching
    
    Returns:
        Tuple of (SQL query, parameters dict)
    """
    params: Dict[str, Any] = {}
    conditions = []
    
    # Step A: Get root object and closure from commit
    if commit_id:
        # Step A query: Get commit root and closure
        query = """
        WITH commit_root AS (
            SELECT
                c.id AS commit_id,
                o.id AS root_object_id,
                o.data->'__closure' AS closure
            FROM commits c
            JOIN objects o ON o.id = c."referencedObject"
            WHERE c.id = %(commit_id)s
        )
        SELECT 
            elem.id,
            elem."speckleType",
            elem.data,
            cr.root_object_id as root_id,
            root.data->>'name' as root_name,
            root.data->>'number' as root_number
        FROM commit_root cr
        CROSS JOIN jsonb_each_text(cr.closure) closure_entry
        JOIN objects elem ON elem.id = closure_entry.key
        LEFT JOIN objects root ON root.id = cr.root_object_id
        WHERE 1=1
        """
        params["commit_id"] = commit_id
    else:
        # Fallback: query without commit scope (less efficient)
        query = """
        SELECT 
            elem.id,
            elem."speckleType",
            elem.data,
            root.id as root_id,
            root.data->>'name' as root_name,
            root.data->>'number' as root_number
        FROM public.objects elem
        LEFT JOIN public.objects root ON root.data->'__closure' ? elem.id
        WHERE 1=1
        """
    
    # Step C: Filter for engineering meaning (Speckle type)
    if speckle_types:
        placeholders = []
        for i, stype in enumerate(speckle_types):
            param_name = f"type_{i}"
            params[param_name] = f"%{stype}%"
            placeholders.append(f"elem.\"speckleType\" ILIKE %({param_name})s")
        conditions.append(f"({' OR '.join(placeholders)})")
    
    # Filter by closure membership (if closure_ids provided)
    if closure_ids:
        placeholders = []
        for i, cid in enumerate(closure_ids):
            param_name = f"closure_{i}"
            params[param_name] = cid
            if commit_id:
                # Already scoped by closure in CTE
                pass
            else:
                placeholders.append(f"root.data->'__closure' ? %({param_name})s")
        if placeholders:
            conditions.append(f"({' OR '.join(placeholders)})")
    
    # String filters on data JSONB
    if string_filters:
        for field, value in string_filters.items():
            param_name = f"str_{field}"
            params[param_name] = f"%{value}%"
            # Fix: use proper JSONB path syntax
            conditions.append(f"elem.data->>'{field}' ILIKE %({param_name})s")
    
    if conditions:
        query += " AND " + " AND ".join(conditions)
    
    # Limit results to prevent overload
    query += " LIMIT 1000"
    
    return query, params


def build_project_query(project_ids: Optional[List[str]] = None) -> tuple[str, Dict[str, Any]]:
    """
    Build query to get project metadata
    
    Args:
        project_ids: Optional list of project IDs to filter
    
    Returns:
        Tuple of (SQL query, parameters dict)
    """
    params: Dict[str, Any] = {}
    
    query = """
    SELECT 
        id,
        data->>'name' as name,
        data->>'number' as number,
        data->>'description' as description
    FROM public.objects
    WHERE "speckleType" = 'Project'
    """
    
    if project_ids:
        placeholders = []
        for i, pid in enumerate(project_ids):
            param_name = f"proj_{i}"
            params[param_name] = pid
            placeholders.append(f"id = :{param_name}")
        query += " AND (" + " OR ".join(placeholders) + ")"
    
    return query, params

