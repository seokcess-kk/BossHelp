-- BossHelp Initial Schema
-- Version: 1.0
-- Date: 2026-02-15

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ============================================
-- Games Table
-- ============================================
CREATE TABLE games (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    genre TEXT NOT NULL CHECK (genre IN ('soulslike', 'metroidvania', 'action_rpg')),
    release_date DATE,
    subreddit TEXT,
    wiki_base_url TEXT,
    latest_patch TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE games IS '지원하는 게임 목록';
COMMENT ON COLUMN games.id IS '게임 식별자 (slug 형식: elden-ring, sekiro)';
COMMENT ON COLUMN games.genre IS '게임 장르: soulslike, metroidvania, action_rpg';

-- ============================================
-- Chunks Table (Vector DB)
-- ============================================
CREATE TABLE chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    game_id TEXT REFERENCES games(id) NOT NULL,
    category TEXT NOT NULL CHECK (category IN (
        'boss_guide', 'build_guide', 'progression_route',
        'npc_quest', 'item_location', 'mechanic_tip', 'secret_hidden'
    )),
    source_type TEXT NOT NULL CHECK (source_type IN ('reddit', 'wiki', 'steam')),
    source_url TEXT NOT NULL,
    title TEXT,
    content TEXT NOT NULL,
    embedding VECTOR(1536),
    quality_score FLOAT DEFAULT 0.5 CHECK (quality_score >= 0 AND quality_score <= 1),
    spoiler_level TEXT DEFAULT 'none' CHECK (spoiler_level IN ('none', 'light', 'heavy')),
    entity_tags TEXT[] DEFAULT '{}',
    patch_version TEXT,
    is_active BOOLEAN DEFAULT true,
    feedback_helpful INT DEFAULT 0,
    feedback_not_helpful INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE chunks IS '크롤링된 콘텐츠 청크 (RAG용 Vector DB)';
COMMENT ON COLUMN chunks.category IS '콘텐츠 분류: boss_guide, build_guide, progression_route, npc_quest, item_location, mechanic_tip, secret_hidden';
COMMENT ON COLUMN chunks.quality_score IS '품질 점수 (0~1), RAG 리랭킹에 사용';
COMMENT ON COLUMN chunks.embedding IS 'OpenAI text-embedding-3-small 1536차원 벡터';

-- ============================================
-- Conversations Table
-- ============================================
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id TEXT NOT NULL,
    game_id TEXT REFERENCES games(id),
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    chunk_ids UUID[] DEFAULT '{}',
    spoiler_level TEXT DEFAULT 'none' CHECK (spoiler_level IN ('none', 'light', 'heavy')),
    is_helpful BOOLEAN,
    latency_ms INT,
    created_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE conversations IS '대화 로그';
COMMENT ON COLUMN conversations.session_id IS '클라이언트 세션 식별자';
COMMENT ON COLUMN conversations.chunk_ids IS '답변 생성에 사용된 chunk ID 배열';

-- ============================================
-- Crawl Logs Table
-- ============================================
CREATE TABLE crawl_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    game_id TEXT REFERENCES games(id),
    source_type TEXT NOT NULL CHECK (source_type IN ('reddit', 'wiki', 'steam')),
    status TEXT NOT NULL CHECK (status IN ('success', 'failed', 'partial')),
    pages_crawled INT DEFAULT 0,
    chunks_created INT DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMPTZ DEFAULT now(),
    completed_at TIMESTAMPTZ
);

COMMENT ON TABLE crawl_logs IS '크롤링 작업 로그';

-- ============================================
-- Takedown Log Table
-- ============================================
CREATE TABLE takedown_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_url TEXT NOT NULL,
    requester TEXT NOT NULL,
    reason TEXT,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'hidden', 'removed', 'rejected')),
    affected_chunk_ids UUID[],
    created_at TIMESTAMPTZ DEFAULT now(),
    resolved_at TIMESTAMPTZ
);

COMMENT ON TABLE takedown_log IS '콘텐츠 삭제 요청 로그';

-- ============================================
-- Indexes
-- ============================================

-- Vector search index (IVFFlat)
CREATE INDEX idx_chunks_embedding ON chunks
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Game + Category filter (for active chunks)
CREATE INDEX idx_chunks_game_cat ON chunks(game_id, category)
    WHERE is_active = true;

-- Quality score for ranking
CREATE INDEX idx_chunks_quality ON chunks(quality_score DESC)
    WHERE is_active = true;

-- Conversation session lookup
CREATE INDEX idx_conv_session ON conversations(session_id);

-- Conversation game + time lookup
CREATE INDEX idx_conv_game ON conversations(game_id, created_at DESC);

-- Full-text search on chunk content
CREATE INDEX idx_chunks_content_trgm ON chunks
    USING gin (content gin_trgm_ops);

-- ============================================
-- Initial Game Data
-- ============================================
INSERT INTO games (id, title, genre, subreddit, wiki_base_url) VALUES
    ('elden-ring', 'Elden Ring', 'soulslike', 'r/Eldenring', 'https://eldenring.wiki.fextralife.com'),
    ('sekiro', 'Sekiro: Shadows Die Twice', 'soulslike', 'r/Sekiro', 'https://sekiroshadowsdietwice.wiki.fextralife.com'),
    ('hollow-knight', 'Hollow Knight', 'metroidvania', 'r/HollowKnight', 'https://hollowknight.wiki.fextralife.com'),
    ('silksong', 'Hollow Knight: Silksong', 'metroidvania', 'r/HollowKnight', null),
    ('lies-of-p', 'Lies of P', 'soulslike', 'r/LiesOfP', 'https://liesofp.wiki.fextralife.com');

-- ============================================
-- Updated_at Trigger
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_games_updated_at
    BEFORE UPDATE ON games
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_chunks_updated_at
    BEFORE UPDATE ON chunks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- RLS Policies (Optional - for public access)
-- ============================================
-- ALTER TABLE games ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE chunks ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;

-- CREATE POLICY "Games are viewable by everyone" ON games
--     FOR SELECT USING (true);

-- CREATE POLICY "Chunks are viewable by everyone" ON chunks
--     FOR SELECT USING (is_active = true);
