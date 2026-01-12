--
-- PostgreSQL database dump
--

\restrict cYsoom1bUa4RKkeewLygIbBjPIsyYScgD2SlYSC1YA1LyooZbIAOgCCRjN6UObJ

-- Dumped from database version 17.6
-- Dumped by pg_dump version 18.1

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA public;


--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON SCHEMA public IS 'standard public schema';


--
-- Name: compute_correct_file_path(text); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.compute_correct_file_path(_file_path text) RETURNS text
    LANGUAGE sql
    AS $$
  SELECT
    CASE
      WHEN _file_path IS NULL THEN NULL

      -- Case 1: base/<pdf_name>/md/<pdf_name>_page-###.md
      WHEN split_part(replace(_file_path, E'\\', '/'), '/', 1) = 'base' THEN
        -- \\WADDELLNAS\Resources\References & Codes\<pdf_name>.pdf
        '\\\\WADDELLNAS\\Resources\\References & Codes\\'
        || split_part(
             split_part(replace(_file_path, E'\\', '/'), '/md/', 1),
             '/',
             2
           )
        || '.pdf'

      -- Case 2: <subfolder>/<pdf_name>/md/<pdf_name>_page-###.md
      ELSE
        -- \\WADDELLNAS\Resources\References & Codes\<subfolder>\<pdf_name>.pdf
        '\\\\WADDELLNAS\\Resources\\References & Codes\\'
        || split_part(
             split_part(replace(_file_path, E'\\', '/'), '/md/', 1),
             '/',
             1
           )
        || '\\'
        || split_part(
             split_part(replace(_file_path, E'\\', '/'), '/md/', 1),
             '/',
             2
           )
        || '.pdf'
    END;
$$;


--
-- Name: find_connected_by_type(text, text, text[]); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.find_connected_by_type(node_global_id text, target_label text, relationship_types text[] DEFAULT ARRAY['SUPPORTED_BY_INFERRED'::text, 'CONNECTS_TO'::text, 'CONNECTS_TO_INFERRED'::text]) RETURNS TABLE(connected_node_global_id text, connected_node_name text, relationship_type text, direction text)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT
        n.global_id,
        n.name,
        e.relationship_type,
        'outgoing'::TEXT
    FROM edges e
    JOIN nodes n ON n.global_id = e.target_global_id
    WHERE e.source_global_id = node_global_id
        AND n.label = target_label
        AND e.relationship_type = ANY(relationship_types)
    
    UNION
    
    SELECT DISTINCT
        n.global_id,
        n.name,
        e.relationship_type,
        'incoming'::TEXT
    FROM edges e
    JOIN nodes n ON n.global_id = e.source_global_id
    WHERE e.target_global_id = node_global_id
        AND n.label = target_label
        AND e.relationship_type = ANY(relationship_types);
END;
$$;


--
-- Name: find_load_path(text, text, integer); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.find_load_path(start_global_id text, end_global_id text, max_depth integer DEFAULT 10) RETURNS TABLE(path_nodes text[], path_relationships text[], path_length integer, total_confidence double precision)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE load_path AS (
        -- Base case: start with source node
        SELECT 
            ARRAY[start_global_id]::TEXT[] as nodes,
            ARRAY[]::TEXT[] as relationships,
            0 as depth,
            1.0::FLOAT as confidence_product
        WHERE start_global_id = start_global_id
        
        UNION ALL
        
        -- Recursive case: follow structural relationships
        SELECT 
            lp.nodes || e.target_global_id,
            lp.relationships || e.relationship_type,
            lp.depth + 1,
            lp.confidence_product * COALESCE(e.confidence, 1.0)
        FROM load_path lp
        JOIN edges e ON e.source_global_id = lp.nodes[array_length(lp.nodes, 1)]
        WHERE e.relationship_type IN (
            'SUPPORTED_BY_INFERRED', 
            'CONNECTS_TO', 
            'CONNECTS_TO_INFERRED',
            'CONTAINS',
            'AGGREGATES'
        )
            AND e.target_global_id != ALL(lp.nodes)  -- Avoid cycles
            AND lp.depth < max_depth  -- Limit depth
    )
    SELECT 
        path_nodes,
        path_relationships,
        array_length(path_nodes, 1) - 1 as path_length,
        total_confidence
    FROM load_path
    WHERE path_nodes[array_length(path_nodes, 1)] = end_global_id
    ORDER BY path_length ASC, total_confidence DESC
    LIMIT 1;
END;
$$;


--
-- Name: find_supporting_elements(text, integer); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.find_supporting_elements(element_global_id text, max_depth integer DEFAULT 5) RETURNS TABLE(supporting_element_global_id text, supporting_element_label text, supporting_element_name text, relationship_type text, depth integer, confidence double precision)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE support_chain AS (
        -- Base case: start with the element
        SELECT 
            element_global_id as element_id,
            0 as depth
        
        UNION ALL
        
        -- Find what supports this element
        SELECT 
            e.source_global_id,
            sc.depth + 1
        FROM support_chain sc
        JOIN edges e ON e.target_global_id = sc.element_id
        WHERE e.relationship_type IN ('SUPPORTED_BY_INFERRED', 'CONNECTS_TO', 'CONNECTS_TO_INFERRED')
            AND sc.depth < max_depth
    )
    SELECT DISTINCT
        n.global_id,
        n.label,
        n.name,
        e.relationship_type,
        sc.depth,
        e.confidence
    FROM support_chain sc
    JOIN edges e ON e.target_global_id = sc.element_id
    JOIN nodes n ON n.global_id = e.source_global_id
    WHERE sc.depth > 0  -- Exclude the starting element
    ORDER BY sc.depth, n.label;
END;
$$;


--
-- Name: get_neighbors(text, text); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.get_neighbors(node_global_id text, relationship_filter text DEFAULT NULL::text) RETURNS TABLE(neighbor_global_id text, relationship_type text, direction text, confidence double precision)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    -- Outgoing edges (node -> neighbors)
    SELECT 
        e.target_global_id,
        e.relationship_type,
        'outgoing'::TEXT,
        e.confidence
    FROM edges e
    WHERE e.source_global_id = node_global_id
        AND (relationship_filter IS NULL OR e.relationship_type = relationship_filter)
    
    UNION
    
    -- Incoming edges (neighbors -> node)
    SELECT 
        e.source_global_id,
        e.relationship_type,
        'incoming'::TEXT,
        e.confidence
    FROM edges e
    WHERE e.target_global_id = node_global_id
        AND (relationship_filter IS NULL OR e.relationship_type = relationship_filter);
END;
$$;


--
-- Name: get_structural_hierarchy(text, integer); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.get_structural_hierarchy(start_global_id text, max_depth integer DEFAULT 5) RETURNS TABLE(level integer, node_global_id text, node_label text, node_name text, relationship_type text)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE hierarchy AS (
        -- Base case
        SELECT 
            0 as level,
            n.global_id,
            n.label,
            n.name,
            NULL::TEXT as relationship_type
        FROM nodes n
        WHERE n.global_id = start_global_id
        
        UNION ALL
        
        -- Follow CONTAINS relationships (parent -> child)
        SELECT 
            h.level + 1,
            n.global_id,
            n.label,
            n.name,
            e.relationship_type
        FROM hierarchy h
        JOIN edges e ON e.source_global_id = h.node_global_id
        JOIN nodes n ON n.global_id = e.target_global_id
        WHERE e.relationship_type = 'CONTAINS'
            AND h.level < max_depth
    )
    SELECT * FROM hierarchy ORDER BY level, node_label;
END;
$$;


--
-- Name: keyword_search_chunks(text, integer, text[], boolean); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.keyword_search_chunks(q text, match_count integer DEFAULT 200, project_keys text[] DEFAULT NULL::text[], use_large boolean DEFAULT false) RETURNS TABLE(id text, content text, metadata jsonb, score double precision)
    LANGUAGE sql STABLE
    AS $$
  with base as (
    -- flip between tables via the flag
    select * from page_chunks where use_large
    union all
    select * from smart_chunks where not use_large
  ),
  src as (
    select
      b.id::text,
      b.content,
      -- CONTENT-ONLY tsvector (matches the indexes above)
      to_tsvector('english_unaccent', coalesce(b.content,'')) as tsv_expr,
      jsonb_build_object(
        'project_key',  b.project_key,
        'page_id',      b.page_id,
        'page_number',  b.page_number,
        'chunk_index',  b.chunk_index,
        'section_type', b.section_type,
        'title',        b.title,
        'summary',      b.summary,
        'bundle_file',  b.bundle_file,
        'created_at',   b.created_at
      ) as metadata
    from base b
    where (project_keys is null or b.project_key = any(project_keys))
  ),
  qts as (
    -- Build the standard AND-words query + the strict phrase query
    select
      websearch_to_tsquery('english_unaccent', q) as tsq_words_and,
      phraseto_tsquery('english_unaccent', q)     as tsq_phrase
  ),
  words_or as (
    -- Turn "a & b & c" into "a | b | c" (any-word matching)
    select
      case
        when tsq_words_and is null then null::tsquery
        else nullif(
               regexp_replace(tsq_words_and::text, '\s&\s', ' | ', 'g'),
               ''
             )::tsquery
      end as tsq_words_or,
      tsq_phrase
    from qts
  ),
  qfinal as (
    -- Robust OR: build as TEXT (skips nulls) then cast back to tsquery
    select
      case
        when concat_ws(' | ', tsq_words_or::text, tsq_phrase::text) <> ''
          then concat_ws(' | ', tsq_words_or::text, tsq_phrase::text)::tsquery
        else null::tsquery
      end as tsq
    from words_or
  )
  select
    s.id,
    s.content,
    s.metadata,
    ts_rank_cd(s.tsv_expr, qf.tsq) as score
  from src s
  cross join qfinal qf
  where qf.tsq is not null
    and s.tsv_expr @@ qf.tsq
  order by score desc
  limit match_count;
$$;


--
-- Name: match_code_documents(public.vector, integer); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.match_code_documents(query_embedding public.vector, match_count integer DEFAULT 1000) RETURNS TABLE(id text, content text, metadata jsonb, similarity double precision)
    LANGUAGE plpgsql
    AS $$
DECLARE
  effective_ef int;
BEGIN
  -- Set HNSW search efficiency parameter
  effective_ef := LEAST(GREATEST(match_count, 100), 1000);
  PERFORM set_config('hnsw.ef_search', effective_ef::text, true);

  RETURN QUERY
  SELECT
    c.id,
    c.content,
    jsonb_build_object(
      'content', c.content,
      'filename', c.filename,
      'page_number', c.page_number,
      'file_path', c.file_path,
      'created_at', c.created_at
    ) AS metadata,
    1 - (c.embedding <=> query_embedding) AS similarity
  FROM public.code_chunks c
  WHERE c.embedding IS NOT NULL
  ORDER BY c.embedding <=> query_embedding
  LIMIT match_count;
END; $$;


--
-- Name: match_code_documents_filtered(public.vector, integer, text[]); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.match_code_documents_filtered(query_embedding public.vector, match_count integer DEFAULT 1000, filename_filter text[] DEFAULT NULL::text[]) RETURNS TABLE(id text, content text, metadata jsonb, similarity double precision)
    LANGUAGE plpgsql
    AS $$
DECLARE
  effective_ef int;
BEGIN
  -- Set HNSW search efficiency parameter
  effective_ef := LEAST(GREATEST(match_count, 100), 1000);
  PERFORM set_config('hnsw.ef_search', effective_ef::text, true);

  RETURN QUERY
  SELECT
    c.id,
    c.content,
    jsonb_build_object(
      'content', c.content,
      'filename', c.filename,
      'page_number', c.page_number,
      'file_path', c.file_path,
      'created_at', c.created_at
    ) AS metadata,
    1 - (c.embedding <=> query_embedding) AS similarity
  FROM public.code_chunks c
  WHERE c.embedding IS NOT NULL
    AND (filename_filter IS NULL OR c.filename = ANY(filename_filter))
  ORDER BY c.embedding <=> query_embedding
  LIMIT match_count;
END; $$;


--
-- Name: match_coop_documents(public.vector, integer); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.match_coop_documents(query_embedding public.vector, match_count integer DEFAULT 1000) RETURNS TABLE(id text, content text, metadata jsonb, similarity double precision)
    LANGUAGE plpgsql
    AS $$
DECLARE
  effective_ef int;
BEGIN
  -- Set HNSW search efficiency parameter
  effective_ef := LEAST(GREATEST(match_count, 10), 100);
  PERFORM set_config('hnsw.ef_search', effective_ef::text, true);

  RETURN QUERY
  SELECT
    c.id,
    c.content,
    jsonb_build_object(
      'filename', c.filename,
      'page_number', c.page_number,
      'file_path', c.file_path,
      'created_at', c.created_at
    ) AS metadata,
    1 - (c.embedding <=> query_embedding) AS similarity
  FROM public.coop_chunks c
  WHERE c.embedding IS NOT NULL
  ORDER BY c.embedding <=> query_embedding
  LIMIT match_count;
END; $$;


--
-- Name: match_documents(public.vector, integer, text[]); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.match_documents(query_embedding public.vector, match_count integer DEFAULT 400, project_keys text[] DEFAULT NULL::text[]) RETURNS TABLE(id text, content text, metadata jsonb, similarity double precision)
    LANGUAGE plpgsql
    AS $$
DECLARE
  effective_ef integer;
BEGIN
  effective_ef := LEAST(GREATEST(match_count, 400), 1000);
  PERFORM set_config('hnsw.ef_search', effective_ef::text, true);
  
  RETURN QUERY
  SELECT
    chunks.id,
    chunks.content,
    -- Create metadata object from individual columns
    jsonb_build_object(
      'project_key', chunks.project_key,
      'page_id', chunks.page_id,
      'page_number', chunks.page_number,
      'chunk_index', chunks.chunk_index,
      'section_type', chunks.section_type,
      'title', chunks.title,
      'summary', chunks.summary,
      'bundle_file', chunks.bundle_file,
      'created_at', chunks.created_at
    ) as metadata,
    1 - (chunks.embedding <=> query_embedding) as similarity
  FROM smart_chunks chunks
  WHERE chunks.embedding IS NOT NULL
    AND (project_keys IS NULL OR chunks.project_key = ANY(project_keys))
  ORDER BY chunks.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;


--
-- Name: match_documents_cap_projects(public.vector, integer, integer, integer, text[]); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.match_documents_cap_projects(query_embedding public.vector, match_count integer DEFAULT 1000, projects_limit integer DEFAULT 100, chunks_per_project integer DEFAULT 1, project_keys text[] DEFAULT NULL::text[]) RETURNS TABLE(id text, content text, metadata jsonb, similarity double precision)
    LANGUAGE plpgsql
    AS $$
DECLARE
  effective_ef int;
BEGIN
  effective_ef := LEAST(GREATEST(match_count, 100), 1000);
  PERFORM set_config('hnsw.ef_search', effective_ef::text, true);

  RETURN QUERY
  WITH candidates AS (
    SELECT
      s.id, 
      s.content, 
      s.project_key, 
      s.page_id, 
      s.page_number,
      s.chunk_index, 
      s.section_type, 
      s.title, 
      s.summary,
      s.bundle_file, 
      s.created_at,
      s.has_revit,
      (s.embedding <=> query_embedding) AS dist
    FROM public.smart_chunks s
    WHERE s.embedding IS NOT NULL
      AND (project_keys IS NULL OR s.project_key = ANY(project_keys))
    ORDER BY s.embedding <=> query_embedding
    LIMIT match_count
  ),
  ranked AS (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY project_key ORDER BY dist ASC) AS rn
    FROM candidates
  )
  SELECT
    ranked.id,
    ranked.content,
    jsonb_build_object(
      'project_key', ranked.project_key,
      'page_id', ranked.page_id,
      'page_number', ranked.page_number,
      'chunk_index', ranked.chunk_index,
      'section_type', ranked.section_type,
      'title', ranked.title,
      'summary', ranked.summary,
      'bundle_file', ranked.bundle_file,
      'created_at', ranked.created_at,
      'has_revit', ranked.has_revit
    ) AS metadata,
    1 - ranked.dist AS similarity
  FROM ranked
  WHERE ranked.rn <= chunks_per_project
  ORDER BY ranked.dist ASC
  LIMIT projects_limit * chunks_per_project;
END; $$;


--
-- Name: match_documents_cap_projects_large(public.vector, integer, integer, integer, text[]); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.match_documents_cap_projects_large(query_embedding public.vector, match_count integer DEFAULT 1000, projects_limit integer DEFAULT 100, chunks_per_project integer DEFAULT 1, project_keys text[] DEFAULT NULL::text[]) RETURNS TABLE(id text, content text, metadata jsonb, similarity double precision)
    LANGUAGE plpgsql
    AS $$
DECLARE
  effective_ef int;
BEGIN
  effective_ef := LEAST(GREATEST(match_count, 100), 1000);
  PERFORM set_config('hnsw.ef_search', effective_ef::text, true);

  RETURN QUERY
  WITH candidates AS (
    SELECT
      s.id, 
      s.content, 
      s.project_key, 
      s.page_id, 
      s.page_number,
      s.chunk_index, 
      s.section_type, 
      s.title, 
      s.summary,
      s.bundle_file, 
      s.created_at,
      s.has_revit,
      (s.embedding <=> query_embedding) AS dist
    FROM public.page_chunks s
    WHERE s.embedding IS NOT NULL
      AND (project_keys IS NULL OR s.project_key = ANY(project_keys))
    ORDER BY s.embedding <=> query_embedding
    LIMIT match_count
  ),
  ranked AS (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY project_key ORDER BY dist ASC) AS rn
    FROM candidates
  )
  SELECT
    ranked.id,
    ranked.content,
    jsonb_build_object(
      'project_key', ranked.project_key,
      'page_id', ranked.page_id,
      'page_number', ranked.page_number,
      'chunk_index', ranked.chunk_index,
      'section_type', ranked.section_type,
      'title', ranked.title,
      'summary', ranked.summary,
      'bundle_file', ranked.bundle_file,
      'created_at', ranked.created_at,
      'has_revit', ranked.has_revit
    ) AS metadata,
    1 - ranked.dist AS similarity
  FROM ranked
  WHERE ranked.rn <= chunks_per_project
  ORDER BY ranked.dist ASC
  LIMIT projects_limit * chunks_per_project;
END; $$;


--
-- Name: match_documents_large(double precision[], integer, text); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.match_documents_large(q_array double precision[], k integer DEFAULT 300, p_project text DEFAULT NULL::text) RETURNS TABLE(similarity real, distance real, id text, project_key text, page_id text, page_number integer, chunk_index integer, title text, section_type text, content_preview text)
    LANGUAGE plpgsql
    AS $$
DECLARE
  q_vec vector(1536);
  effective_ef integer;
BEGIN
  -- Guardrail: ensure correct dimensionality
  IF array_length(q_array, 1) IS DISTINCT FROM 1536 THEN
    RAISE EXCEPTION 'Embedding must have 1536 dimensions, got %', array_length(q_array, 1);
  END IF;

  -- Safety cap: ef_search max value
  effective_ef := LEAST(GREATEST(k, 400), 1000);  -- default 40, cap at 1000

  -- Set hnsw.ef_search locally for this transaction only
  PERFORM set_config('hnsw.ef_search', effective_ef::text, true);

  -- Cast to pgvector
  q_vec := q_array::vector(1536);

  RETURN QUERY
  SELECT
      (1 - (sc.embedding <=> q_vec))::real AS similarity,
      (sc.embedding <=> q_vec)::real       AS distance,
      sc.id,
      sc.project_key,
      sc.page_id,
      sc.page_number,
      sc.chunk_index,
      sc.title,
      sc.section_type,
      LEFT(sc.content, 300)                AS content_preview
  FROM public.smart_chunks sc
  WHERE sc.embedding IS NOT NULL
    AND (p_project IS NULL OR sc.project_key = p_project)
  ORDER BY sc.embedding <=> q_vec
  LIMIT k;
END;
$$;


--
-- Name: match_documents_large(public.vector, integer, text[]); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.match_documents_large(query_embedding public.vector, match_count integer DEFAULT 400, project_keys text[] DEFAULT NULL::text[]) RETURNS TABLE(id text, content text, metadata jsonb, similarity double precision)
    LANGUAGE plpgsql
    AS $$
DECLARE
  effective_ef integer;
BEGIN
  effective_ef := LEAST(GREATEST(match_count, 400), 1000);
  PERFORM set_config('hnsw.ef_search', effective_ef::text, true);
  RETURN QUERY
  SELECT
    chunks.id,
    chunks.content,
    -- Create metadata object from individual columns
    jsonb_build_object(
      'project_key', chunks.project_key,
      'page_id', chunks.page_id,
      'page_number', chunks.page_number,
      'chunk_index', chunks.chunk_index,
      'section_type', chunks.section_type,
      'title', chunks.title,
      'summary', chunks.summary,
      'bundle_file', chunks.bundle_file,
      'created_at', chunks.created_at
    ) as metadata,
    1 - (chunks.embedding <=> query_embedding) as similarity
  FROM page_chunks chunks
  WHERE chunks.embedding IS NOT NULL
    AND (project_keys IS NULL OR chunks.project_key = ANY(project_keys))
  ORDER BY chunks.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;


--
-- Name: match_documents_largex(public.vector, integer, text[], integer, integer); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.match_documents_largex(query_embedding public.vector, match_count integer DEFAULT 400, project_keys text[] DEFAULT NULL::text[], projects_limit integer DEFAULT NULL::integer, chunks_per_project integer DEFAULT 1) RETURNS TABLE(id text, content text, metadata jsonb, similarity double precision)
    LANGUAGE plpgsql
    AS $$
DECLARE
  effective_ef integer;
  final_projects_limit int;
BEGIN
  effective_ef := LEAST(GREATEST(match_count, 400), 1000);
  PERFORM set_config('hnsw.ef_search', effective_ef::text, true);
  final_projects_limit := COALESCE(projects_limit, match_count);

  RETURN QUERY
  WITH candidates AS (
    SELECT
      s.id, s.content, s.project_key, s.page_id, s.page_number,
      s.chunk_index, s.section_type, s.title, s.summary, s.bundle_file,
      s.created_at,
      (s.embedding <=> query_embedding) AS dist
    FROM public.page_chunks s  -- ← Different table
    WHERE s.embedding IS NOT NULL
      AND (project_keys IS NULL OR s.project_key = ANY(project_keys))
    ORDER BY s.embedding <=> query_embedding
    LIMIT match_count
  ),
  ranked AS (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY project_key ORDER BY dist ASC) AS rn
    FROM candidates
  )
  SELECT
    id,
    content,
    jsonb_build_object(
      'project_key', project_key,
      'page_id', page_id,
      'page_number', page_number,
      'chunk_index', chunk_index,
      'section_type', section_type,
      'title', title,
      'summary', summary,
      'bundle_file', bundle_file,
      'created_at', created_at
    ) AS metadata,
    1 - dist AS similarity
  FROM ranked
  WHERE rn <= chunks_per_project
  ORDER BY dist ASC
  LIMIT final_projects_limit * chunks_per_project;
END;
$$;


--
-- Name: match_documents_x(public.vector, integer, text[], integer, integer); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.match_documents_x(query_embedding public.vector, match_count integer DEFAULT 400, project_keys text[] DEFAULT NULL::text[], projects_limit integer DEFAULT NULL::integer, chunks_per_project integer DEFAULT 1) RETURNS TABLE(id text, content text, metadata jsonb, similarity double precision)
    LANGUAGE plpgsql
    AS $$
DECLARE
  effective_ef integer;
  final_projects_limit int;
BEGIN
  -- explore deep independently of return count
  effective_ef := LEAST(GREATEST(match_count, 400), 1000);
  PERFORM set_config('hnsw.ef_search', effective_ef::text, true);

  final_projects_limit := COALESCE(projects_limit, match_count);

  RETURN QUERY
  WITH candidates AS (
    SELECT
      s.id, s.content, s.project_key, s.page_id, s.page_number,
      s.chunk_index, s.section_type, s.title, s.summary, s.bundle_file,
      s.created_at,
      (s.embedding <=> query_embedding) AS dist
    FROM public.smart_chunks s
    WHERE s.embedding IS NOT NULL
      AND (project_keys IS NULL OR s.project_key = ANY(project_keys))
    ORDER BY s.embedding <=> query_embedding
    LIMIT match_count
  ),
  ranked AS (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY project_key ORDER BY dist ASC) AS rn
    FROM candidates
  )
  SELECT
    id,
    content,
    jsonb_build_object(
      'project_key', project_key,
      'page_id', page_id,
      'page_number', page_number,
      'chunk_index', chunk_index,
      'section_type', section_type,
      'title', title,
      'summary', summary,
      'bundle_file', bundle_file,
      'created_at', created_at
    ) AS metadata,
    1 - dist AS similarity
  FROM ranked
  WHERE rn <= chunks_per_project
  ORDER BY dist ASC
  LIMIT final_projects_limit * chunks_per_project;  -- cap rows = projects × cpp
END;
$$;


--
-- Name: match_image_embeddings(public.vector, integer, double precision, text); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.match_image_embeddings(query_embedding public.vector, match_count integer DEFAULT 10, match_threshold double precision DEFAULT 0.0, project_key_filter text DEFAULT NULL::text) RETURNS TABLE(id text, project_key text, page_number integer, embedding public.vector, image_url text, similarity double precision)
    LANGUAGE plpgsql
    AS $$
BEGIN
    RETURN QUERY
    SELECT
        ie.id,
        ie.project_key,
        ie.page_number,
        ie.embedding,
        ie.image_url,
        1 - (ie.embedding <=> query_embedding) AS similarity
    FROM image_embeddings ie
    WHERE
        (project_key_filter IS NULL OR ie.project_key = project_key_filter)
        AND (1 - (ie.embedding <=> query_embedding)) >= match_threshold
    ORDER BY ie.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;


--
-- Name: nn_search_smart_chunks_from_array(double precision[], integer, text); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.nn_search_smart_chunks_from_array(q_array double precision[], k integer DEFAULT 100, p_project text DEFAULT NULL::text) RETURNS TABLE(similarity real, distance real, id text, project_key text, page_id text, page_number integer, chunk_index integer, title text, section_type text, content_preview text)
    LANGUAGE plpgsql
    AS $$
DECLARE
  q_vec vector(1536);
BEGIN
  -- Guardrail: ensure correct dimensionality
  IF array_length(q_array, 1) IS DISTINCT FROM 1536 THEN
    RAISE EXCEPTION 'Embedding must have 1536 dimensions, got %', array_length(q_array, 1);
  END IF;

  -- Cast to pgvector
  q_vec := q_array::vector(1536);

  RETURN QUERY
  SELECT
      (1 - (sc.embedding <=> q_vec))::real AS similarity,
      (sc.embedding <=> q_vec)::real       AS distance,
      sc.id,
      sc.project_key,
      sc.page_id,
      sc.page_number,
      sc.chunk_index,
      sc.title,
      sc.section_type,
      LEFT(sc.content, 300)                AS content_preview
  FROM public.smart_chunks sc
  WHERE sc.embedding IS NOT NULL
    AND (p_project IS NULL OR sc.project_key = p_project)
  ORDER BY sc.embedding <=> q_vec          -- uses your existing ANN index
  LIMIT k;
END;
$$;


--
-- Name: set_updated_at(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.set_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
begin
  new.updated_at := now();
  return new;
end $$;


--
-- Name: update_updated_at_column(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.update_updated_at_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;


--
-- Name: english_unaccent; Type: TEXT SEARCH CONFIGURATION; Schema: public; Owner: -
--

CREATE TEXT SEARCH CONFIGURATION public.english_unaccent (
    PARSER = pg_catalog."default" );

ALTER TEXT SEARCH CONFIGURATION public.english_unaccent
    ADD MAPPING FOR asciiword WITH english_stem;

ALTER TEXT SEARCH CONFIGURATION public.english_unaccent
    ADD MAPPING FOR word WITH public.unaccent, english_stem;

ALTER TEXT SEARCH CONFIGURATION public.english_unaccent
    ADD MAPPING FOR numword WITH simple;

ALTER TEXT SEARCH CONFIGURATION public.english_unaccent
    ADD MAPPING FOR email WITH simple;

ALTER TEXT SEARCH CONFIGURATION public.english_unaccent
    ADD MAPPING FOR url WITH simple;

ALTER TEXT SEARCH CONFIGURATION public.english_unaccent
    ADD MAPPING FOR host WITH simple;

ALTER TEXT SEARCH CONFIGURATION public.english_unaccent
    ADD MAPPING FOR sfloat WITH simple;

ALTER TEXT SEARCH CONFIGURATION public.english_unaccent
    ADD MAPPING FOR version WITH simple;

ALTER TEXT SEARCH CONFIGURATION public.english_unaccent
    ADD MAPPING FOR hword_numpart WITH simple;

ALTER TEXT SEARCH CONFIGURATION public.english_unaccent
    ADD MAPPING FOR hword_part WITH public.unaccent, english_stem;

ALTER TEXT SEARCH CONFIGURATION public.english_unaccent
    ADD MAPPING FOR hword_asciipart WITH english_stem;

ALTER TEXT SEARCH CONFIGURATION public.english_unaccent
    ADD MAPPING FOR numhword WITH simple;

ALTER TEXT SEARCH CONFIGURATION public.english_unaccent
    ADD MAPPING FOR asciihword WITH english_stem;

ALTER TEXT SEARCH CONFIGURATION public.english_unaccent
    ADD MAPPING FOR hword WITH public.unaccent, english_stem;

ALTER TEXT SEARCH CONFIGURATION public.english_unaccent
    ADD MAPPING FOR url_path WITH simple;

ALTER TEXT SEARCH CONFIGURATION public.english_unaccent
    ADD MAPPING FOR file WITH simple;

ALTER TEXT SEARCH CONFIGURATION public.english_unaccent
    ADD MAPPING FOR "float" WITH simple;

ALTER TEXT SEARCH CONFIGURATION public.english_unaccent
    ADD MAPPING FOR "int" WITH simple;

ALTER TEXT SEARCH CONFIGURATION public.english_unaccent
    ADD MAPPING FOR uint WITH simple;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: code_chunks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.code_chunks (
    id text NOT NULL,
    filename text NOT NULL,
    page_number integer NOT NULL,
    content text,
    embedding public.vector(1536),
    created_at timestamp with time zone DEFAULT now(),
    file_path text
);


--
-- Name: coop_chunks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.coop_chunks (
    id text NOT NULL,
    filename text NOT NULL,
    page_number integer NOT NULL,
    file_path text,
    content text,
    embedding public.vector(1536),
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: image_descriptions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.image_descriptions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    project_key text NOT NULL,
    page_num integer NOT NULL,
    region_number integer,
    image_id text NOT NULL,
    relative_path text,
    classification text,
    location text,
    level text,
    orientation text,
    element_type text,
    grid_references text,
    section_callouts text,
    element_callouts text,
    key_components text,
    text_verbatim text,
    summary text,
    text_verbatim_embedding public.vector(1536),
    summary_embedding public.vector(1536),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: TABLE image_descriptions; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.image_descriptions IS 'Structured descriptions of engineering drawing regions with text embeddings';


--
-- Name: COLUMN image_descriptions.text_verbatim_embedding; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.image_descriptions.text_verbatim_embedding IS 'Embedding of text_verbatim using text-embedding-3-small (1536 dimensions)';


--
-- Name: COLUMN image_descriptions.summary_embedding; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.image_descriptions.summary_embedding IS 'Embedding of summary using text-embedding-3-small (1536 dimensions)';


--
-- Name: image_embeddings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.image_embeddings (
    id text NOT NULL,
    project_key text NOT NULL,
    page_number integer NOT NULL,
    embedding public.vector(1024),
    image_url text NOT NULL,
    created_at timestamp with time zone DEFAULT now()
);


--
-- Name: nodes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.nodes (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    global_id text NOT NULL,
    ifc_id integer,
    label text NOT NULL,
    name text,
    object_type text,
    description text,
    tag text,
    properties jsonb DEFAULT '{}'::jsonb,
    metadata jsonb DEFAULT '{}'::jsonb,
    geometry jsonb DEFAULT '{}'::jsonb,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    node_type text,
    project_key text,
    length numeric,
    width numeric,
    height numeric,
    number_of_storeys integer,
    total_volume numeric,
    volume_units text,
    used_in_elements text[],
    member_types text[],
    system_type text,
    components text[],
    element_count integer,
    ifc_type text,
    detected_in text[],
    detection_count integer,
    component_type text,
    embedding jsonb
);


--
-- Name: load_bearing_elements; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.load_bearing_elements AS
 SELECT id,
    global_id,
    ifc_id,
    label,
    name,
    object_type,
    description,
    tag,
    properties,
    metadata,
    geometry,
    created_at,
    updated_at,
    (((properties -> 'Pset_ColumnCommon'::text) ->> 'LoadBearing'::text))::boolean AS is_load_bearing_column,
    (((properties -> 'Pset_WallCommon'::text) ->> 'LoadBearing'::text))::boolean AS is_load_bearing_wall
   FROM public.nodes n
  WHERE ((label = ANY (ARRAY['IfcColumn'::text, 'IfcWall'::text, 'IfcBeam'::text, 'IfcSlab'::text, 'IfcRoof'::text])) AND ((((properties -> 'Pset_ColumnCommon'::text) ->> 'LoadBearing'::text) = 'True'::text) OR (((properties -> 'Pset_WallCommon'::text) ->> 'LoadBearing'::text) = 'True'::text)));


--
-- Name: page_chunks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.page_chunks (
    id text NOT NULL,
    project_key text NOT NULL,
    page_id text NOT NULL,
    page_number integer,
    chunk_index integer NOT NULL,
    section_type text DEFAULT 'unknown'::text,
    title text DEFAULT ''::text,
    summary text DEFAULT ''::text,
    bundle_file text,
    content text NOT NULL,
    embedding public.vector(1536),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    has_revit boolean,
    content_length integer GENERATED ALWAYS AS (char_length(COALESCE(content, ''::text))) STORED
);


--
-- Name: project_description; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.project_description (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    project_id text NOT NULL,
    project_name text,
    client text,
    location text,
    building_type text,
    number_of_levels integer,
    levels text,
    dimensions_length text,
    dimensions_width text,
    dimensions_height text,
    dimensions_area text,
    gravity_system text,
    lateral_system text,
    concrete_strengths text,
    steel_shapes text,
    rebar_sizes text,
    other_materials text,
    structural_beams text,
    structural_columns text,
    structural_trusses text,
    key_elements text,
    overall_building_description text,
    overall_building_description_embedding public.vector(1536),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


--
-- Name: TABLE project_description; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON TABLE public.project_description IS 'Building-level synthesis information from engineering drawings with text embeddings';


--
-- Name: COLUMN project_description.overall_building_description_embedding; Type: COMMENT; Schema: public; Owner: -
--

COMMENT ON COLUMN public.project_description.overall_building_description_embedding IS 'Embedding of overall_building_description using text-embedding-3-small (1536 dimensions)';


--
-- Name: project_info; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.project_info (
    id bigint NOT NULL,
    project_key text NOT NULL,
    project_name text NOT NULL,
    project_city text,
    project_postal_code text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    project_address text,
    company_name text
);


--
-- Name: project_info_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.project_info_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: project_info_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.project_info_id_seq OWNED BY public.project_info.id;


--
-- Name: smart_chunks; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.smart_chunks (
    id text NOT NULL,
    project_key text NOT NULL,
    page_id text NOT NULL,
    page_number integer,
    chunk_index integer NOT NULL,
    section_type text DEFAULT 'unknown'::text,
    title text DEFAULT ''::text,
    summary text DEFAULT ''::text,
    bundle_file text,
    content text NOT NULL,
    embedding public.vector(1536),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    has_revit boolean,
    tsv tsvector GENERATED ALWAYS AS ((setweight(to_tsvector('public.english_unaccent'::regconfig, COALESCE(title, ''::text)), 'A'::"char") || setweight(to_tsvector('public.english_unaccent'::regconfig, COALESCE(content, ''::text)), 'B'::"char"))) STORED,
    content_length integer GENERATED ALWAYS AS (char_length(COALESCE(content, ''::text))) STORED
);


--
-- Name: testingBIMdataEXPORT; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public."testingBIMdataEXPORT" (
    element_id text,
    stream_id text,
    project_id text,
    project_name text,
    model_id text,
    model_name text,
    version_id text,
    root_object_id text,
    speckle_type text,
    element_name text,
    application_id text,
    last_updated timestamp with time zone,
    is_column boolean,
    is_beam boolean,
    is_brace boolean,
    is_wall boolean,
    is_floor boolean,
    is_roof boolean,
    is_slab boolean,
    is_foundation boolean,
    is_connection boolean,
    is_beam_system boolean,
    is_door boolean,
    is_window boolean,
    is_stair boolean,
    is_railing boolean,
    element_type_summary text,
    ifc_type text,
    material text,
    revit_material text,
    structural_material text,
    level text,
    level_id text,
    building_storey text,
    base_level_elevation text,
    top_level_elevation text,
    revit_type text,
    revit_family text,
    revit_category text,
    tag text,
    section text,
    volume double precision,
    length text,
    width text,
    height text,
    area double precision,
    length_unit text,
    width_unit text,
    height_unit text,
    volume_unit text,
    area_unit text,
    geometry_points_json text,
    start_point_x text,
    start_point_y text,
    start_point_z text,
    end_point_x text,
    end_point_y text,
    end_point_z text,
    base_point_x text,
    base_point_y text,
    base_point_z text,
    top_point_x text,
    top_point_y text,
    top_point_z text,
    connected_element_ids jsonb,
    connected_element_count bigint,
    parent_id text,
    parent_name text,
    parent_type text,
    relationship_type text,
    has_display_value boolean,
    display_value_count bigint,
    geometry_type text,
    elements_array text,
    elements_count text,
    all_properties_json text,
    all_parameters_json text,
    phase_created text,
    phase_demolished text,
    is_structural boolean,
    workset text,
    comments text
);


--
-- Name: user_interactions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_interactions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    message_id character varying(255) NOT NULL,
    session_id character varying(255) NOT NULL,
    user_identifier character varying(255),
    user_query text NOT NULL,
    rag_response text NOT NULL,
    route character varying(100),
    citations_count integer DEFAULT 0,
    latency_ms numeric(10,2),
    feedback_rating character varying(20),
    feedback_comment text,
    created_at timestamp with time zone DEFAULT now(),
    feedback_updated_at timestamp with time zone,
    image_url text,
    CONSTRAINT user_interactions_feedback_rating_check CHECK (((feedback_rating)::text = ANY (ARRAY[('positive'::character varying)::text, ('negative'::character varying)::text])))
);


--
-- Name: project_info id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_info ALTER COLUMN id SET DEFAULT nextval('public.project_info_id_seq'::regclass);


--
-- Name: code_chunks code_embeddings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.code_chunks
    ADD CONSTRAINT code_embeddings_pkey PRIMARY KEY (id);


--
-- Name: coop_chunks coop_chunks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.coop_chunks
    ADD CONSTRAINT coop_chunks_pkey PRIMARY KEY (id);


--
-- Name: image_descriptions image_descriptions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.image_descriptions
    ADD CONSTRAINT image_descriptions_pkey PRIMARY KEY (id);


--
-- Name: image_embeddings image_embeddings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.image_embeddings
    ADD CONSTRAINT image_embeddings_pkey PRIMARY KEY (id);


--
-- Name: nodes nodes_global_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nodes
    ADD CONSTRAINT nodes_global_id_key UNIQUE (global_id);


--
-- Name: nodes nodes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.nodes
    ADD CONSTRAINT nodes_pkey PRIMARY KEY (id);


--
-- Name: page_chunks page_chunks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.page_chunks
    ADD CONSTRAINT page_chunks_pkey PRIMARY KEY (id);


--
-- Name: project_description project_description_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_description
    ADD CONSTRAINT project_description_pkey PRIMARY KEY (id);


--
-- Name: project_description project_description_project_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_description
    ADD CONSTRAINT project_description_project_id_key UNIQUE (project_id);


--
-- Name: project_info project_info_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_info
    ADD CONSTRAINT project_info_pkey PRIMARY KEY (id, project_key);


--
-- Name: project_info project_info_project_key_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.project_info
    ADD CONSTRAINT project_info_project_key_key UNIQUE (project_key);


--
-- Name: smart_chunks smart_chunks_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.smart_chunks
    ADD CONSTRAINT smart_chunks_pkey PRIMARY KEY (id);


--
-- Name: user_interactions user_interactions_message_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_interactions
    ADD CONSTRAINT user_interactions_message_id_key UNIQUE (message_id);


--
-- Name: user_interactions user_interactions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_interactions
    ADD CONSTRAINT user_interactions_pkey PRIMARY KEY (id);


--
-- Name: idx_code_embedding; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_code_embedding ON public.code_chunks USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='64');


--
-- Name: idx_code_filename; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_code_filename ON public.code_chunks USING btree (filename);


--
-- Name: idx_code_filename_page; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_code_filename_page ON public.code_chunks USING btree (filename, page_number);


--
-- Name: idx_code_page_number; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_code_page_number ON public.code_chunks USING btree (page_number);


--
-- Name: idx_coop_embedding; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_coop_embedding ON public.coop_chunks USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='64');


--
-- Name: idx_coop_filename; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_coop_filename ON public.coop_chunks USING btree (filename);


--
-- Name: idx_coop_filename_page; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_coop_filename_page ON public.coop_chunks USING btree (filename, page_number);


--
-- Name: idx_coop_page_number; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_coop_page_number ON public.coop_chunks USING btree (page_number);


--
-- Name: idx_image_descriptions_classification; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_image_descriptions_classification ON public.image_descriptions USING btree (classification);


--
-- Name: idx_image_descriptions_level; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_image_descriptions_level ON public.image_descriptions USING btree (level);


--
-- Name: idx_image_descriptions_page; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_image_descriptions_page ON public.image_descriptions USING btree (project_key, page_num);


--
-- Name: idx_image_descriptions_project; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_image_descriptions_project ON public.image_descriptions USING btree (project_key);


--
-- Name: idx_image_descriptions_search_text; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_image_descriptions_search_text ON public.image_descriptions USING gin (to_tsvector('english'::regconfig, ((COALESCE(summary, ''::text) || ' '::text) || COALESCE(text_verbatim, ''::text))));


--
-- Name: idx_image_descriptions_summary_embedding; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_image_descriptions_summary_embedding ON public.image_descriptions USING ivfflat (summary_embedding public.vector_cosine_ops) WITH (lists='100');


--
-- Name: idx_image_descriptions_unique; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX idx_image_descriptions_unique ON public.image_descriptions USING btree (project_key, page_num, region_number);


--
-- Name: idx_image_descriptions_verbatim_embedding; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_image_descriptions_verbatim_embedding ON public.image_descriptions USING ivfflat (text_verbatim_embedding public.vector_cosine_ops) WITH (lists='100');


--
-- Name: idx_nodes_components_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_nodes_components_gin ON public.nodes USING gin (components) WHERE (components IS NOT NULL);


--
-- Name: idx_nodes_geometry; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_nodes_geometry ON public.nodes USING gin (geometry);


--
-- Name: idx_nodes_global_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_nodes_global_id ON public.nodes USING btree (global_id);


--
-- Name: idx_nodes_label; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_nodes_label ON public.nodes USING btree (label);


--
-- Name: idx_nodes_member_types_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_nodes_member_types_gin ON public.nodes USING gin (member_types) WHERE (member_types IS NOT NULL);


--
-- Name: idx_nodes_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_nodes_name ON public.nodes USING btree (name) WHERE (name IS NOT NULL);


--
-- Name: idx_nodes_node_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_nodes_node_type ON public.nodes USING btree (node_type);


--
-- Name: idx_nodes_project_key; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_nodes_project_key ON public.nodes USING btree (project_key);


--
-- Name: idx_nodes_properties; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_nodes_properties ON public.nodes USING gin (properties);


--
-- Name: idx_nodes_properties_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_nodes_properties_gin ON public.nodes USING gin (properties);


--
-- Name: idx_nodes_tag; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_nodes_tag ON public.nodes USING btree (tag);


--
-- Name: idx_page_chunks_embedding; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_page_chunks_embedding ON public.page_chunks USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: idx_page_chunks_has_revit; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_page_chunks_has_revit ON public.page_chunks USING btree (has_revit);


--
-- Name: idx_page_chunks_order; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_page_chunks_order ON public.page_chunks USING btree (project_key, page_id, chunk_index);


--
-- Name: idx_page_chunks_project_page; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_page_chunks_project_page ON public.page_chunks USING btree (project_key, page_id);


--
-- Name: idx_page_number; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_page_number ON public.image_embeddings USING btree (page_number);


--
-- Name: idx_project_description_building_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_project_description_building_type ON public.project_description USING btree (building_type);


--
-- Name: idx_project_description_client; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_project_description_client ON public.project_description USING btree (client);


--
-- Name: idx_project_description_embedding; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_project_description_embedding ON public.project_description USING ivfflat (overall_building_description_embedding public.vector_cosine_ops) WITH (lists='100');


--
-- Name: idx_project_description_project_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_project_description_project_id ON public.project_description USING btree (project_id);


--
-- Name: idx_project_description_search_text; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_project_description_search_text ON public.project_description USING gin (to_tsvector('english'::regconfig, COALESCE(overall_building_description, ''::text)));


--
-- Name: idx_project_info_address; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_project_info_address ON public.project_info USING btree (project_address);


--
-- Name: idx_project_info_company_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_project_info_company_name ON public.project_info USING btree (company_name);


--
-- Name: idx_project_info_project_key; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_project_info_project_key ON public.project_info USING btree (project_key);


--
-- Name: idx_project_info_project_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_project_info_project_name ON public.project_info USING btree (project_name);


--
-- Name: idx_project_key; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_project_key ON public.image_embeddings USING btree (project_key);


--
-- Name: idx_smart_chunks_embedding; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_smart_chunks_embedding ON public.smart_chunks USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200');


--
-- Name: idx_smart_chunks_has_revit; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_smart_chunks_has_revit ON public.smart_chunks USING btree (has_revit);


--
-- Name: idx_smart_chunks_order; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_smart_chunks_order ON public.smart_chunks USING btree (project_key, page_id, chunk_index);


--
-- Name: idx_smart_chunks_project_page; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_smart_chunks_project_page ON public.smart_chunks USING btree (project_key, page_id);


--
-- Name: idx_user_interactions_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_interactions_created_at ON public.user_interactions USING btree (created_at);


--
-- Name: idx_user_interactions_feedback_rating; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_interactions_feedback_rating ON public.user_interactions USING btree (feedback_rating);


--
-- Name: idx_user_interactions_session_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_interactions_session_id ON public.user_interactions USING btree (session_id);


--
-- Name: idx_user_interactions_user_identifier; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_user_interactions_user_identifier ON public.user_interactions USING btree (user_identifier);


--
-- Name: image_embeddings_embedding_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX image_embeddings_embedding_idx ON public.image_embeddings USING ivfflat (embedding public.vector_cosine_ops);


--
-- Name: image_embeddings_project_key_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX image_embeddings_project_key_idx ON public.image_embeddings USING btree (project_key);


--
-- Name: image_embeddings_project_page_idx; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX image_embeddings_project_page_idx ON public.image_embeddings USING btree (project_key, page_number);


--
-- Name: smart_chunks_tsv_gin; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX smart_chunks_tsv_gin ON public.smart_chunks USING gin (tsv);


--
-- Name: project_info update_project_info_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER update_project_info_updated_at BEFORE UPDATE ON public.project_info FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: project_info Enable all access for authenticated users; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Enable all access for authenticated users" ON public.project_info TO authenticated USING (true) WITH CHECK (true);


--
-- Name: project_info Enable read access for all users; Type: POLICY; Schema: public; Owner: -
--

CREATE POLICY "Enable read access for all users" ON public.project_info FOR SELECT USING (true);


--
-- Name: testingBIMdataEXPORT; Type: ROW SECURITY; Schema: public; Owner: -
--

ALTER TABLE public."testingBIMdataEXPORT" ENABLE ROW LEVEL SECURITY;

--
-- PostgreSQL database dump complete
--

\unrestrict cYsoom1bUa4RKkeewLygIbBjPIsyYScgD2SlYSC1YA1LyooZbIAOgCCRjN6UObJ

