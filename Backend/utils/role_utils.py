"""
Role-Based Database Preference Utilities
Functions for retrieving and formatting role-based database preferences
"""
from typing import Dict, Optional
from config.settings import ROLE_DATABASE_PREFERENCES, VALID_ROLES
from config.logging_config import log_query


def get_role_preferences(user_role: Optional[str] = None) -> Dict:
    """
    Get database preferences for a user role.
    
    Args:
        user_role: User role (e.g., "structural_engineer", "trainer")
                  If None or invalid, returns "default" role preferences
    
    Returns:
        Dictionary with database priorities and description:
        {
            "project_db": 1.0,
            "code_db": 0.8,
            "coop_manual": 0.3,
            "speckle_db": 0.9,
            "description": "Role description..."
        }
    """
    # Normalize role (handle None, empty string, case-insensitive)
    if not user_role or not isinstance(user_role, str):
        role_key = "default"
    else:
        role_key = user_role.lower().strip()
    
    # Validate role - fallback to default if invalid
    if role_key not in VALID_ROLES:
        log_query.warning(f"⚠️ Invalid role '{user_role}' - using 'default' preferences")
        role_key = "default"
    
    preferences = ROLE_DATABASE_PREFERENCES.get(role_key, ROLE_DATABASE_PREFERENCES["default"])
    
    log_query.info(f"👤 Role preferences for '{role_key}': project_db={preferences.get('project_db', 0.8)}, code_db={preferences.get('code_db', 0.8)}, coop_manual={preferences.get('coop_manual', 0.8)}, speckle_db={preferences.get('speckle_db', 0.8)}")
    
    return preferences


def format_role_preferences_for_router(user_role: Optional[str] = None) -> str:
    """
    Format role-based database preferences as a string for inclusion in router prompt.
    
    Args:
        user_role: User role (e.g., "structural_engineer")
    
    Returns:
        Formatted string describing the role and database priorities for the router
    """
    prefs = get_role_preferences(user_role)
    
    # Build priority description
    priority_lines = []
    if prefs.get("project_db", 0.8) >= 0.8:
        priority_lines.append(f"- **Project Database**: HIGH priority (score: {prefs.get('project_db', 0.8)})")
    elif prefs.get("project_db", 0.8) >= 0.5:
        priority_lines.append(f"- **Project Database**: MEDIUM priority (score: {prefs.get('project_db', 0.8)})")
    else:
        priority_lines.append(f"- **Project Database**: LOW priority (score: {prefs.get('project_db', 0.8)})")
    
    if prefs.get("code_db", 0.8) >= 0.8:
        priority_lines.append(f"- **Code Database**: HIGH priority (score: {prefs.get('code_db', 0.8)})")
    elif prefs.get("code_db", 0.8) >= 0.5:
        priority_lines.append(f"- **Code Database**: MEDIUM priority (score: {prefs.get('code_db', 0.8)})")
    else:
        priority_lines.append(f"- **Code Database**: LOW priority (score: {prefs.get('code_db', 0.8)})")
    
    if prefs.get("coop_manual", 0.8) >= 0.8:
        priority_lines.append(f"- **Internal Docs Database**: HIGH priority (score: {prefs.get('coop_manual', 0.8)})")
    elif prefs.get("coop_manual", 0.8) >= 0.5:
        priority_lines.append(f"- **Internal Docs Database**: MEDIUM priority (score: {prefs.get('coop_manual', 0.8)})")
    else:
        priority_lines.append(f"- **Internal Docs Database**: LOW priority (score: {prefs.get('coop_manual', 0.8)})")
    
    if prefs.get("speckle_db", 0.8) >= 0.8:
        priority_lines.append(f"- **Speckle/BIM Models Database**: HIGH priority (score: {prefs.get('speckle_db', 0.8)})")
    elif prefs.get("speckle_db", 0.8) >= 0.5:
        priority_lines.append(f"- **Speckle/BIM Models Database**: MEDIUM priority (score: {prefs.get('speckle_db', 0.8)})")
    else:
        priority_lines.append(f"- **Speckle/BIM Models Database**: LOW priority (score: {prefs.get('speckle_db', 0.8)})")
    
    formatted = f"""USER ROLE: {user_role or 'default'}

{prefs.get('description', 'Default role with balanced access to all databases.')}

ROLE-BASED DATABASE PRIORITIES:
{chr(10).join(priority_lines)}

NOTE: These priorities guide which databases to prefer based on the user's role. Consider these priorities along with the query content when selecting databases. You can select multiple databases when the query requires information from multiple sources."""
    
    return formatted

