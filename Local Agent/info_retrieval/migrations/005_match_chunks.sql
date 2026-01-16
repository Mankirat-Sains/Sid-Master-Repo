-- Recreate match_chunks RPC with filters matching SupabaseVectorStore expectations.
DROP FUNCTION IF EXISTS public.match_chunks(
  vector(1536), int, text, text, text, text, text, text
);

CREATE OR REPLACE FUNCTION public.match_chunks(
  query_embedding     vector(1536),
  match_count         int DEFAULT 100,
  company_filter      text DEFAULT NULL,
  index_type_filter   text DEFAULT NULL,  -- 'content' | 'style'
  doc_type_filter     text DEFAULT NULL,
  section_type_filter text DEFAULT NULL,
  artifact_filter     text DEFAULT NULL,
  version_filter      text DEFAULT NULL
)
RETURNS TABLE (
  id uuid,
  content text,
  similarity float,
  metadata jsonb
)
LANGUAGE plpgsql AS $$
DECLARE
  effective_ef int;
BEGIN
  effective_ef := LEAST(GREATEST(match_count, 50), 500);
  PERFORM set_config('hnsw.ef_search', effective_ef::text, true);

  RETURN QUERY
  SELECT
    c.id,
    c.content,
    1 - (c.embedding <=> query_embedding) AS similarity,
    jsonb_build_object(
      'chunk_id', c.chunk_id,
      'artifact_id', c.artifact_id,
      'version_id', c.version_id,
      'company_id', c.company_id,
      'chunk_type', COALESCE(c.chunk_type, c.index_type),
      'index_type', c.index_type,
      'doc_type', c.doc_type,
      'section_type', c.section_type,
      'heading', c.heading,
      'page_number', c.page_number,
      'calculation_type', c.calculation_type,
      'style_frequency', c.style_frequency,
      'quality_score', c.quality_score,
      'is_pinned', c.is_pinned,
      'text_length_chars', c.text_length_chars,
      'text_length_words', c.text_length_words,
      'sentence_count', c.sentence_count,
      'paragraph_count', c.paragraph_count
    ) AS metadata
  FROM public.chunks c
  WHERE c.embedding IS NOT NULL
    AND (company_filter IS NULL OR c.company_id = company_filter)
    AND (index_type_filter IS NULL OR c.index_type = index_type_filter)
    AND (doc_type_filter IS NULL OR c.doc_type = doc_type_filter)
    AND (section_type_filter IS NULL OR c.section_type = section_type_filter)
    AND (artifact_filter IS NULL OR c.artifact_id = artifact_filter)
    AND (version_filter IS NULL OR c.version_id = version_filter)
  ORDER BY c.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

GRANT EXECUTE ON FUNCTION public.match_chunks TO anon, authenticated;
