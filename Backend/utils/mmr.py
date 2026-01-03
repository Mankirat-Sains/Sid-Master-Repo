"""
MMR (Maximal Marginal Relevance) Reranking
Diversify search results while maintaining relevance
"""
from typing import List
from langchain_core.documents import Document
from database.retrievers import mmr_rerank_supabase, mmr_rerank_code, mmr_rerank_coop

# Re-export from retrievers module
__all__ = ['mmr_rerank_supabase', 'mmr_rerank_code', 'mmr_rerank_coop']

