"""
Project Metadata Functions
Fetch project information from Supabase project_info table
"""
from typing import List, Dict, Optional
from supabase import create_client
from config.settings import SUPABASE_URL, SUPABASE_KEY, PROJECT_RE
from config.logging_config import log_db


def fetch_project_metadata(project_ids: List[str]) -> Dict[str, Dict[str, str]]:
    """
    Fetch project names and addresses from Supabase project_info table for ALL project IDs.
    
    Args:
        project_ids: List of ALL unique project IDs from retrieved chunks
                    Example: ["25-08-005", "25-01-007", "25-07-118", "24-12-003"]
    
    Returns:
        Dict mapping EVERY project_id to {name, address, city, postal_code}
        Example: {
            "25-08-005": {"name": "Smith Residence", "address": "123 Main St...", "city": "Toronto", "postal_code": "M5V 3A8"},
            "25-01-007": {"name": "Jones Office", "address": "456 Oak Ave...", "city": "Vancouver"}
        }
    """
    if not project_ids:
        return {}
    
    # Check if Supabase is configured
    if not SUPABASE_URL or not SUPABASE_KEY:
        log_db.error("Supabase not configured, skipping project metadata lookup")
        return {}
    
    try:
        log_db.info(f"Fetching metadata for {len(project_ids)} projects from Supabase")
        
        # Create Supabase client
        _supa = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Query project_info table for all project IDs
        # Use .in_() filter for efficient batch lookup
        print(f"🔍 FETCHING METADATA for projects: {project_ids[:10]}{'...' if len(project_ids) > 10 else ''}")  # Diagnostic
        result = _supa.table("project_info").select(
            "project_key, project_name, project_address, project_city, project_postal_code"
        ).in_("project_key", project_ids).execute()
        
        print(f"📊 METADATA QUERY returned {len(result.data)} rows")  # Diagnostic
        
        # Build result dictionary for ALL found projects
        metadata = {}
        for row in result.data:
            project_key = row.get("project_key")
            if project_key:
                metadata[project_key] = {
                    "name": row.get("project_name") or "",
                    "address": row.get("project_address") or "",
                    "city": row.get("project_city") or "",
                    "postal_code": row.get("project_postal_code") or ""
                }
        
        print(f"📋 METADATA FOUND for: {list(metadata.keys())[:10]}{'...' if len(metadata) > 10 else ''}")  # Diagnostic
        
        log_db.info(f"Retrieved metadata for {len(metadata)}/{len(project_ids)} projects from Supabase")
        
        # Log warnings for missing projects
        for proj_id in project_ids:
            if proj_id not in metadata and PROJECT_RE.match(proj_id):
                log_db.warning(f"Project {proj_id} not found in Supabase project_info table")
            elif proj_id not in metadata:
                # Log non-standard project IDs that weren't found
                log_db.debug(f"Non-standard project ID '{proj_id}' not found in Supabase (may be malformed)")
        
        # Ensure we return a dict (safety check)
        if not isinstance(metadata, dict):
            log_db.error(f"❌ Metadata is not a dict (type: {type(metadata)}), returning empty dict")
            return {}
        
        return metadata
        
    except Exception as e:
        import traceback
        log_db.error(f"Supabase project metadata lookup failed: {e}")
        log_db.error(f"Traceback: {traceback.format_exc()}")
        return {}


def test_database_connection() -> Dict:
    """
    Lightweight healthcheck for Supabase project_info table.
    Returns:
        {
          "connected": bool,
          "project_count": int,     # number of projects in table
          "error": "..."            # present only when connected=False
        }
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        return {"connected": False, "error": "Missing SUPABASE_URL or SUPABASE_KEY env vars"}
    
    try:
        _supa = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Try to count projects in project_info table
        result = _supa.table("project_info").select("*", count="exact").limit(1).execute()
        
        return {
            "connected": True,
            "project_count": result.count
        }
    except Exception as e:
        return {"connected": False, "error": f"Supabase connection failed: {e}"}

