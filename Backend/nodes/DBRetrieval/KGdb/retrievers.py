"""
Hybrid Retrievers for Supabase
Dense vector + keyword search with MMR diversification
"""
import re
from typing import List, Dict, Optional, Any
from langchain_core.documents import Document
from supabase import create_client
from config.settings import (
    SUPABASE_URL, SUPABASE_KEY, SUPA_SMART_TABLE,
    SUPA_LARGE_TABLE, SUPA_CODE_TABLE, SUPA_COOP_TABLE
)
from config.llm_instances import emb
from config.logging_config import log_query
from .supabase_client import vs_smart, vs_large, vs_code, vs_coop

# This is a large file - functions extracted from rag.py
# See the original file for full implementation details

def make_hybrid_retriever(project: Optional[str] = None, sql_filters: Optional[Dict] = None, route: str = "smart"):
    """Create hybrid retriever (dense + keyword) with project filtering and SQL pre-filtering for project database"""
    
    # Cache for pre-filtered project keys (computed once for all subqueries)
    _prefiltered_project_keys_cache = None
    _total_content_count_cache = None
    
    # Supabase hybrid: dense vector + keyword search on the selected database
    if SUPABASE_URL and SUPABASE_KEY and vs_smart is not None and vs_large is not None:
        def supabase_hybrid_search(query: str, k: int = 8, keyword_weight: float = None, 
                                  sql_filters: Optional[Dict] = None) -> List[Document]:
            """Enhanced Supabase hybrid search with SQL pre-filtering"""
            
            log_query.info(f"🔍 HYBRID SEARCH CALLED: sql_filters={sql_filters}")
            
            # Get the selected database based on route
            if route == "smart" and vs_smart is not None:
                selected_vs = vs_smart
                table_name = SUPA_SMART_TABLE
            elif route == "large" and vs_large is not None:
                selected_vs = vs_large
                table_name = SUPA_LARGE_TABLE
            elif vs_smart is not None:  # fallback to smart
                selected_vs = vs_smart
                table_name = SUPA_SMART_TABLE
            elif vs_large is not None:  # fallback to large
                selected_vs = vs_large
                table_name = SUPA_LARGE_TABLE
            else:
                log_query.error("No Supabase vector stores available")
                return []

            # Log which table is being used based on route
            log_query.info(f"🎯 ROUTE-BASED TABLE SELECTION: route='{route}' → table='{table_name}'")

            # Apply SQL pre-filtering if provided
            _supa = create_client(SUPABASE_URL, SUPABASE_KEY)
            if sql_filters:
                log_query.info(f"🗓️ SQL PRE-FILTER: Applying filters {sql_filters} to {table_name}")
                try:
                    # STEP 1: SQL Pre-filtering (done ONCE for all subqueries)
                    nonlocal _prefiltered_project_keys_cache, _total_content_count_cache
                    if _prefiltered_project_keys_cache is None:
                        log_query.info("🚀 OPTIMIZATION: Performing SQL pre-filtering ONCE for all subqueries")
                        
                        # Get filtered project keys first with pagination to bypass 1000 limit
                        all_project_keys = []
                        offset = 0
                        page_size = 1000  # Supabase's max per request
                        
                        while True:
                            query_builder = _supa.table(table_name).select("project_key")
                            
                            # Apply filters
                            has_revit_filter = False
                            for condition in sql_filters.get("and", []):
                                if "like" in condition:
                                    key, op, value = condition.split(".", 2)
                                    query_builder = query_builder.like(key, value)
                                elif "eq" in condition:
                                    key, op, value = condition.split(".", 2)
                                    if value.lower() == "true":
                                        value = True
                                    elif value.lower() == "false":
                                        value = False
                                    
                                    if key == "has_revit":
                                        has_revit_filter = True
                                    
                                    query_builder = query_builder.eq(key, value)
                            
                            result = query_builder.range(offset, offset + page_size - 1).execute()
                            
                            if not result.data:
                                break
                            
                            page_keys = [row["project_key"] for row in result.data]
                            all_project_keys.extend(page_keys)
                            
                            if len(result.data) < page_size:
                                break
                            
                            offset += page_size
                    
                        filtered_project_keys = list(set(all_project_keys))
                        
                        if not filtered_project_keys:
                            return []
                        
                        _prefiltered_project_keys_cache = filtered_project_keys
                        _total_content_count_cache = len(all_project_keys)
                    else:
                        log_query.info("🚀 OPTIMIZATION: Using cached SQL pre-filtering results")
                    
                    # Get query embedding
                    query_embedding = emb.embed_query(query)
                    
                    # Use cached project keys
                    unique_project_keys = _prefiltered_project_keys_cache
                    
                    # Use the new capped project functions for better project diversity
                    rpc_function = 'match_image_descriptions_verbatim' if table_name == SUPA_SMART_TABLE else 'match_project_descriptions'
                    
                    print(f"🔍 RPC CALL (pre-filtered): function={rpc_function}, table={table_name}, project_keys={len(unique_project_keys) if unique_project_keys else 0}")  # Diagnostic
                    
                    chunks_per_project = 5
                    projects_limit = min(30, len(unique_project_keys)) if unique_project_keys else 50
                    match_count = 300
                    
                    result = _supa.rpc(rpc_function, {
                        'query_embedding': query_embedding,
                        'match_count': match_count,
                        'projects_limit': projects_limit,
                        'chunks_per_project': chunks_per_project,
                        'project_keys': unique_project_keys
                    }).execute()
                    
                    # Convert HNSW result to rows
                    dense_rows = result.data or []
                    print(f"📊 RPC RETURNED (pre-filtered): {len(dense_rows)} rows")  # Diagnostic
                    if dense_rows:
                        first_projects = []
                        for row in dense_rows[:5]:
                            meta = row.get('metadata', {})
                            proj = meta.get('project_key') or meta.get('project_id') or 'UNKNOWN'
                            first_projects.append(proj)
                        print(f"📋 First projects: {first_projects}")  # Diagnostic
                    
                    # Ensure even distribution across projects
                    if dense_rows:
                        project_chunks = {}
                        for row in dense_rows:
                            project_key = row.get('metadata', {}).get('project_key', 'unknown')
                            if project_key not in project_chunks:
                                project_chunks[project_key] = []
                            project_chunks[project_key].append(row)
                        
                        balanced_rows = []
                        for project_key, chunks in project_chunks.items():
                            limited_chunks = chunks[:chunks_per_project]
                            balanced_rows.extend(limited_chunks)
                        
                        dense_rows = balanced_rows
                    
                    # Pure HNSW only - just take top k results
                    fused_rows = dense_rows[:k]
                    
                    # Convert fused rows to Document objects
                    dense_docs = []
                    for row in fused_rows:
                        metadata = row.get('metadata', {}).copy() if isinstance(row.get('metadata'), dict) else {}
                        metadata['similarity_score'] = row.get('similarity', row.get('score', 0.0))
                        
                        doc = Document(
                            page_content=row.get('content', ''),
                            metadata=metadata
                        )
                        dense_docs.append(doc)
                    
                    return dense_docs
                    
                except Exception as e:
                    log_query.error(f"SQL pre-filtering failed: {e}")
                    # Fall back to regular search
            else:
                log_query.info(f"🗓️ SQL PRE-FILTER: No sql_filters provided, skipping pre-filtering")

            # Regular dense vector search (fallback or when no filters)
            query_embedding = emb.embed_query(query)
            
            rpc_function = 'match_image_descriptions_verbatim' if table_name == SUPA_SMART_TABLE else 'match_project_descriptions'
            
            print(f"🔍 RPC CALL: function={rpc_function}, table={table_name}, route={route}")  # Diagnostic
            
            if route == "large" or table_name == SUPA_LARGE_TABLE:
                chunks_per_project = 3
            elif route == "smart" or table_name == SUPA_SMART_TABLE:
                chunks_per_project = 1
            else:
                chunks_per_project = 1
            
            projects_limit = 30
            match_count = 300
            
            result = _supa.rpc(rpc_function, {
                'query_embedding': query_embedding,
                'match_count': match_count,
                'projects_limit': projects_limit,
                'chunks_per_project': chunks_per_project,
                'project_keys': None
            }).execute()
            
            dense_rows = result.data or []
            print(f"📊 RPC RETURNED: {len(dense_rows)} rows from {rpc_function}")  # Diagnostic
            
            # Show first few project keys returned
            if dense_rows:
                first_projects = []
                for row in dense_rows[:5]:
                    meta = row.get('metadata', {})
                    proj = meta.get('project_key') or meta.get('project_id') or 'UNKNOWN'
                    first_projects.append(proj)
                print(f"📋 First projects returned: {first_projects}")  # Diagnostic
            
            fused_rows = dense_rows[:k]
            
            dense_docs = []
            for row in fused_rows:
                metadata = row.get('metadata', {}).copy() if isinstance(row.get('metadata'), dict) else {}
                metadata['similarity_score'] = row.get('similarity', row.get('score', 0.0))
                
                doc = Document(
                    page_content=row.get('content', ''),
                    metadata=metadata
                )
                dense_docs.append(doc)
            
            return dense_docs

        class SupabaseHybrid:
            def hybrid_search(self, query: str, k: int = 8, keyword_weight: float = None, sql_filters: Optional[Dict] = None) -> List[Document]:
                return supabase_hybrid_search(query, k, keyword_weight, sql_filters)

        hybrid_retriever = SupabaseHybrid()
    else:
        raise ValueError("No hybrid retriever available. Supabase tables not initialized.")
    
    def hybrid_search_with_filter(query: str, k: int = 8) -> List[Document]:
        """Enhanced hybrid search with smart SQL pre-filtering and project filtering"""
        
        if sql_filters:
            log_query.info(f"🗓️ DATE FILTERING: Using pre-extracted SQL filters: {sql_filters}")
        
        fetch_count = k * 3 if project else k * 2
        results = hybrid_retriever.hybrid_search(query, fetch_count, sql_filters=sql_filters)

        # Apply project filter if specified
        if project:
            normalized_filter = re.sub(r'\D', '', project)
            filtered_results = []
            for doc in results:
                md = doc.metadata or {}
                doc_project = (md.get('drawing_number') or
                             md.get('project_key') or
                             md.get('project_id') or '')
                normalized_doc = re.sub(r'\D', '', doc_project)
                
                if (project in doc_project or
                    normalized_filter == normalized_doc or
                    project == doc_project):
                    filtered_results.append(doc)
            
            results = filtered_results

        final = results[:k]
        return final

    return hybrid_search_with_filter


def make_code_hybrid_retriever():
    """Create hybrid retriever (dense + keyword) for code database"""
    
    if SUPABASE_URL and SUPABASE_KEY and vs_code is not None:
        def supabase_code_hybrid_search(query: str, k: int = 8, keyword_weight: float = None) -> List[Document]:
            """Enhanced Supabase hybrid search for code database"""
            
            try:
                _supa = create_client(SUPABASE_URL, SUPABASE_KEY)
                query_embedding = emb.embed_query(query)
                match_count = min(1000, k * 5)
                
                result = _supa.rpc("match_code_documents", {
                    'query_embedding': query_embedding,
                    'match_count': match_count
                }).execute()
                
                dense_rows = result.data or []
                fused_rows = dense_rows[:k]
                
                code_docs = []
                for i, row in enumerate(fused_rows):
                    metadata = row.get('metadata', {}).copy() if isinstance(row.get('metadata'), dict) else {}
                    
                    if 'filename' in row:
                        metadata['filename'] = row['filename']
                    if 'page_number' in row:
                        metadata['page_number'] = row['page_number']
                        metadata['page'] = row['page_number']
                    
                    for field in ['source', 'section', 'title', 'file_path', 'id']:
                        if field in row and field not in metadata:
                            metadata[field] = row[field]
                    
                    metadata['similarity_score'] = row.get('similarity', row.get('score', 0.0))
                    
                    doc = Document(
                        page_content=row['content'],
                        metadata=metadata
                    )
                    code_docs.append(doc)
                
                return code_docs
                
            except Exception as e:
                log_query.error(f"Code hybrid search failed: {e}")
                try:
                    return vs_code.similarity_search(query, k=k)
                except Exception as e2:
                    log_query.error(f"Fallback also failed: {e2}")
                    return []

        class SupabaseCodeHybrid:
            def hybrid_search(self, query: str, k: int = 8, keyword_weight: float = None) -> List[Document]:
                return supabase_code_hybrid_search(query, k, keyword_weight)

        code_hybrid_retriever = SupabaseCodeHybrid()
    else:
        raise ValueError("No code hybrid retriever available. Code vector store not initialized.")
    
    def code_search(query: str, k: int = 8) -> List[Document]:
        """Code hybrid search function"""
        fetch_count = k * 2
        results = code_hybrid_retriever.hybrid_search(query, fetch_count)
        final = results[:k]
        return final

    return code_search


def make_coop_hybrid_retriever():
    """Create hybrid retriever (dense + keyword) for coop manual database"""
    
    if SUPABASE_URL and SUPABASE_KEY and vs_coop is not None:
        def supabase_coop_hybrid_search(query: str, k: int = 8, keyword_weight: float = None) -> List[Document]:
            """Enhanced Supabase hybrid search for coop manual database"""
            
            try:
                _supa = create_client(SUPABASE_URL, SUPABASE_KEY)
                query_embedding = emb.embed_query(query)
                match_count = min(1000, k * 5)
                
                try:
                    result = _supa.rpc("match_coop_documents", {
                        'query_embedding': query_embedding,
                        'match_count': match_count
                    }).execute()
                    
                    dense_rows = result.data or []
                    fused_rows = dense_rows[:k]
                except Exception as rpc_error:
                    log_query.info(f"RPC function not available, using similarity search: {rpc_error}")
                    return vs_coop.similarity_search(query, k=k)
                
                coop_docs = []
                for i, row in enumerate(fused_rows):
                    metadata = row.get('metadata', {}).copy() if isinstance(row.get('metadata'), dict) else {}
                    
                    if 'filename' in row:
                        metadata['filename'] = row['filename']
                    elif 'filename' in metadata:
                        pass  # Already in metadata
                    else:
                        log_query.error(f"filename NOT found in row")
                    
                    if 'page_number' in row:
                        metadata['page_number'] = row['page_number']
                        metadata['page'] = row['page_number']
                    elif 'page_number' in metadata:
                        if 'page' not in metadata:
                            metadata['page'] = metadata['page_number']
                    elif 'page' in metadata:
                        metadata['page_number'] = metadata['page']
                    else:
                        log_query.error(f"page_number NOT found in row")
                    
                    if 'id' in row and 'id' not in metadata:
                        metadata['id'] = row['id']
                    
                    if 'file_path' in metadata:
                        pass
                    elif 'file_path' in row:
                        metadata['file_path'] = row['file_path']
                    
                    metadata['similarity_score'] = row.get('similarity', row.get('score', 0.0))
                    
                    doc = Document(
                        page_content=row['content'],
                        metadata=metadata
                    )
                    coop_docs.append(doc)
                
                return coop_docs
                
            except Exception as e:
                log_query.error(f"Coop hybrid search failed: {e}")
                try:
                    return vs_coop.similarity_search(query, k=k)
                except Exception as e2:
                    log_query.error(f"Fallback also failed: {e2}")
                    return []

        class SupabaseCoopHybrid:
            def hybrid_search(self, query: str, k: int = 8, keyword_weight: float = None) -> List[Document]:
                return supabase_coop_hybrid_search(query, k, keyword_weight)

        coop_hybrid_retriever = SupabaseCoopHybrid()
    else:
        raise ValueError("No coop hybrid retriever available. Coop vector store not initialized.")
    
    def coop_search(query: str, k: int = 8) -> List[Document]:
        """Coop hybrid search function"""
        fetch_count = k * 2
        results = coop_hybrid_retriever.hybrid_search(query, fetch_count)
        final = results[:k]
        return final

    return coop_search


def mmr_rerank_supabase(docs: List[Document], query_embedding, lambda_=0.7, k=30) -> List[Document]:
    """Apply MMR (Maximal Marginal Relevance) to diversify Supabase results"""
    if len(docs) <= k:
        return docs
    
    selected, remaining = [], docs[:]
    
    while remaining and len(selected) < k:
        def mmr_score(doc_idx):
            doc = remaining[doc_idx]
            sim_to_q = doc.metadata.get('similarity_score', 0.0)
            
            sim_to_sel = 0.0
            if selected:
                for sel_doc in selected:
                    sel_project = sel_doc.metadata.get('project_key', '')
                    doc_project = doc.metadata.get('project_key', '')
                    if sel_project != doc_project:
                        sim_to_sel += 0.1
            
            return lambda_ * sim_to_q - (1 - lambda_) * sim_to_sel
        
        best_idx = max(range(len(remaining)), key=mmr_score)
        pick = remaining.pop(best_idx)
        selected.append(pick)
    
    return selected


def mmr_rerank_code(docs: List[Document], query_embedding, lambda_=0.9, k=30) -> List[Document]:
    """Apply MMR to diversify code results - less diversity, more relevance"""
    if len(docs) <= k:
        return docs
    
    selected, remaining = [], docs[:]
    
    while remaining and len(selected) < k:
        def mmr_score(doc_idx):
            doc = remaining[doc_idx]
            sim_to_q = doc.metadata.get('similarity_score', 0.0)
            
            sim_to_sel = 0.0
            if selected:
                for sel_doc in selected:
                    sel_source = sel_doc.metadata.get('source', '')
                    doc_source = doc.metadata.get('source', '')
                    if sel_source != doc_source:
                        sim_to_sel += 0.05
            
            return lambda_ * sim_to_q - (1 - lambda_) * sim_to_sel
        
        best_idx = max(range(len(remaining)), key=mmr_score)
        pick = remaining.pop(best_idx)
        selected.append(pick)
    
    return selected


def mmr_rerank_coop(docs: List[Document], query_embedding, lambda_=0.9, k=30) -> List[Document]:
    """Apply MMR to diversify coop results - less diversity, more relevance"""
    if len(docs) <= k:
        return docs
    
    selected, remaining = [], docs[:]
    
    while remaining and len(selected) < k:
        def mmr_score(doc_idx):
            doc = remaining[doc_idx]
            sim_to_q = doc.metadata.get('similarity_score', 0.0)
            
            sim_to_sel = 0.0
            if selected:
                for sel_doc in selected:
                    sel_filename = sel_doc.metadata.get('filename', '')
                    doc_filename = doc.metadata.get('filename', '')
                    if sel_filename != doc_filename:
                        sim_to_sel += 0.05
            
            return lambda_ * sim_to_q - (1 - lambda_) * sim_to_sel
        
        best_idx = max(range(len(remaining)), key=mmr_score)
        pick = remaining.pop(best_idx)
        selected.append(pick)
    
    return selected

