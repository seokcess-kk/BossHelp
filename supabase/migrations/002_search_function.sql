-- BossHelp Vector Search Function
-- Version: 1.0
-- Date: 2026-02-15

-- Create vector search function for RAG pipeline
CREATE OR REPLACE FUNCTION search_chunks(
    query_embedding VECTOR(1536),
    match_threshold FLOAT DEFAULT 0.5,
    match_count INT DEFAULT 10,
    filter_game_id TEXT DEFAULT NULL,
    filter_spoiler_levels TEXT[] DEFAULT ARRAY['none'],
    filter_category TEXT DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    game_id TEXT,
    category TEXT,
    source_type TEXT,
    source_url TEXT,
    title TEXT,
    content TEXT,
    quality_score FLOAT,
    spoiler_level TEXT,
    entity_tags TEXT[],
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id,
        c.game_id,
        c.category,
        c.source_type,
        c.source_url,
        c.title,
        c.content,
        c.quality_score,
        c.spoiler_level,
        c.entity_tags,
        1 - (c.embedding <=> query_embedding) AS similarity
    FROM chunks c
    WHERE
        c.is_active = true
        AND (filter_game_id IS NULL OR c.game_id = filter_game_id)
        AND c.spoiler_level = ANY(filter_spoiler_levels)
        AND (filter_category IS NULL OR c.category = filter_category)
        AND 1 - (c.embedding <=> query_embedding) >= match_threshold
    ORDER BY c.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Grant execute permission
GRANT EXECUTE ON FUNCTION search_chunks TO authenticated;
GRANT EXECUTE ON FUNCTION search_chunks TO anon;
GRANT EXECUTE ON FUNCTION search_chunks TO service_role;

-- Create index hint comment
COMMENT ON FUNCTION search_chunks IS 'Vector similarity search for RAG pipeline. Uses idx_chunks_embedding (ivfflat) for efficient search.';
