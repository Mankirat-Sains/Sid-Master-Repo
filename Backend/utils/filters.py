"""
Filter Extraction Utilities
Extract date, project, and other filters from queries
"""
import re
from typing import Dict, Any, Optional
from datetime import datetime
from config.settings import PROJECT_RE
from config.logging_config import log_query
from .project_utils import detect_project_filter


def extract_date_filters_from_query(
    query: str,
    project_filter: Optional[str] = None,
    follow_up_context: Optional[str] = None
) -> Dict[str, Any]:
    """
    Extract date/time filters AND project-specific filters from query.
    Now handles: dates, specific project IDs, and follow-up context.
    """
    log_query.info(f"🗓️ SMART FILTER EXTRACTION: Analyzing query: '{query}'")
    
    q_lower = query.lower()
    filters = {}
    
    # 1. Month extraction
    month_patterns = {
        r'\bjanuary\b': '01', r'\bjan\b': '01',
        r'\bfebruary\b': '02', r'\bfeb\b': '02',
        r'\bmarch\b': '03', r'\bmar\b': '03',
        r'\bapril\b': '04', r'\bapr\b': '04',
        r'\bmay\b': '05',
        r'\bjune\b': '06', r'\bjun\b': '06',
        r'\bjuly\b': '07', r'\bjul\b': '07',
        r'\baugust\b': '08', r'\baug\b': '08',
        r'\bseptember\b': '09', r'\bsep\b': '09', r'\bsept\b': '09',
        r'\boctober\b': '10', r'\boct\b': '10',
        r'\bnovember\b': '11', r'\bnov\b': '11',
        r'\bdecember\b': '12', r'\bdec\b': '12'
    }
    
    for pattern, month_num in month_patterns.items():
        if re.search(pattern, q_lower):
            filters['month'] = month_num
            log_query.info(f"🗓️ DATE EXTRACTION: Found month pattern '{pattern}' → {month_num}")
            break
    
    # Year extraction
    year_match = re.search(r'\b(20\d{2})\b', query)
    if year_match:
        year = year_match.group(1)[2:]  # Convert 2025 to 25
        filters['year'] = year
        log_query.info(f"🗓️ DATE EXTRACTION: Found year pattern '{year_match.group(1)}' → {year}")
    
    # Relative time patterns
    current_year = datetime.now().year % 100
    
    if re.search(r'\bthis year\b', q_lower):
        filters['year'] = str(current_year)
        log_query.info(f"🗓️ DATE EXTRACTION: Found 'this year' → {current_year}")
    elif re.search(r'\blast year\b', q_lower):
        filters['year'] = str(current_year - 1)
        log_query.info(f"🗓️ DATE EXTRACTION: Found 'last year' → {current_year - 1}")
    elif re.search(r'\bcurrent year\b', q_lower):
        filters['year'] = str(current_year)
        log_query.info(f"🗓️ DATE EXTRACTION: Found 'current year' → {current_year}")
    
    # 2. Specific project ID detection
    project_id = detect_project_filter(query)
    if project_id:
        filters['project_id'] = project_id
        log_query.info(f"🎯 SMART FILTER: Detected specific project: {project_id}")
    
    # 3. Follow-up context project detection
    if follow_up_context:
        context_project = detect_project_filter(follow_up_context)
        if context_project:
            filters['project_id'] = context_project
            log_query.info(f"🔄 SMART FILTER: Detected follow-up project: {context_project}")
    
    # 4. Explicit project filter from state
    if project_filter:
        filters['project_id'] = project_filter
        log_query.info(f"🎯 SMART FILTER: Using state project filter: {project_filter}")
    
    # 5. Revit file detection
    revit_patterns = [
        r'\brevit\b', r'\brevit file\b', r'\brevit model\b',
        r'\brevit definition\b', r'\brevit project\b',
        r'\bhas revit\b', r'\bwith revit\b',
        r'\brevit available\b', r'\brevit drawing\b', r'\brevit design\b'
    ]
    
    for pattern in revit_patterns:
        match = re.search(pattern, q_lower)
        if match:
            filters['has_revit'] = True
            log_query.info(f"🏗️ REVIT DETECTION: ✅ Revit query identified!")
            break
    
    log_query.info(f"🗓️ SMART FILTER EXTRACTION: Final extracted filters: {filters}")
    return filters


def create_sql_project_filter(filters: Dict[str, Any]) -> Optional[Dict]:
    """
    Create SQL filter for Supabase based on date filters AND project-specific filters.
    Now handles: dates, specific projects, and follow-up context.
    """
    if not filters:
        return None
    
    conditions = []
    
    # Date-based filtering
    if 'year' in filters:
        year = filters['year']
        conditions.append(f"project_key.like.{year}-%")
    
    if 'month' in filters:
        month = filters['month']
        if 'year' in filters:
            conditions.append(f"project_key.like.{year}-{month}-%")
        else:
            conditions.append(f"project_key.like.%-{month}-%")
    
    # Project-specific filtering
    if 'project_id' in filters:
        project_id = filters['project_id']
        conditions.append(f"project_key.like.{project_id}")
        log_query.info(f"🎯 SQL FILTER: Adding exact project match: {project_id}")
    
    # Revit file filtering
    if 'has_revit' in filters and filters['has_revit']:
        conditions.append("has_revit.eq.true")
        log_query.info(f"🏗️ SQL FILTER CREATION: ✅ Revit filter condition added")
    
    if conditions:
        return {"and": conditions}
    
    return None

