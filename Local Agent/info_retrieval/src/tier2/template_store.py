"""
Template Store: Database access for templates and style rules.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from supabase import Client


class TemplateStore:
    """
    Fetch document templates, section templates, and style rules.
    """

    def __init__(self, supabase_client: Client):
        self.db = supabase_client

    def get_document_template(self, company_id: str, doc_type: str) -> Optional[Dict]:
        result = (
            self.db.table("document_templates")
            .select("*")
            .eq("company_id", company_id)
            .eq("doc_type", doc_type)
            .limit(1)
            .execute()
        )
        if result.data:
            return result.data[0]
        return None

    def get_section_template(self, company_id: str, doc_type: str, section_type: str) -> Optional[Dict]:
        result = (
            self.db.table("section_templates")
            .select("*")
            .eq("company_id", company_id)
            .eq("doc_type", doc_type)
            .eq("section_type", section_type)
            .limit(1)
            .execute()
        )
        if result.data:
            return result.data[0]
        return None

    def get_style_rules(self, company_id: str, rule_types: Optional[List[str]] = None) -> List[Dict]:
        query = self.db.table("style_rules").select("*").eq("company_id", company_id)
        if rule_types:
            query = query.in_("rule_type", rule_types)
        query = query.order("priority", desc=True)
        result = query.execute()
        return result.data if result.data else []
