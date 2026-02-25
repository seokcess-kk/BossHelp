-- Entity Tagging Enhancement
-- Version: 1.0
-- Date: 2026-02-25
-- Feature: entity-tagging-improvement

-- ============================================
-- 1. 새 컬럼 추가
-- ============================================

-- primary_entity: 해당 청크의 주 엔티티 (페이지 제목에서 추출)
ALTER TABLE chunks ADD COLUMN IF NOT EXISTS primary_entity TEXT;

-- entity_type: 엔티티 유형 분류
ALTER TABLE chunks ADD COLUMN IF NOT EXISTS entity_type TEXT;

-- ============================================
-- 2. entity_type 제약조건
-- ============================================

-- entity_type 유효 값 체크
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'chk_entity_type'
    ) THEN
        ALTER TABLE chunks ADD CONSTRAINT chk_entity_type
            CHECK (entity_type IS NULL OR entity_type IN (
                'boss', 'weapon', 'armor', 'location',
                'npc', 'item', 'spell', 'mechanic', 'unknown'
            ));
    END IF;
END $$;

-- ============================================
-- 3. 검색 성능을 위한 인덱스
-- ============================================

-- primary_entity 인덱스 (B-tree)
CREATE INDEX IF NOT EXISTS idx_chunks_primary_entity
    ON chunks(primary_entity)
    WHERE is_active = true;

-- entity_type 인덱스 (B-tree)
CREATE INDEX IF NOT EXISTS idx_chunks_entity_type
    ON chunks(entity_type)
    WHERE is_active = true;

-- primary_entity 부분 검색용 인덱스 (trigram)
-- 이미 pg_trgm 확장이 활성화되어 있음 (001_initial_schema.sql)
CREATE INDEX IF NOT EXISTS idx_chunks_primary_entity_trgm
    ON chunks USING gin (primary_entity gin_trgm_ops)
    WHERE is_active = true AND primary_entity IS NOT NULL;

-- 복합 인덱스 (game_id + entity_type)
CREATE INDEX IF NOT EXISTS idx_chunks_game_entity_type
    ON chunks(game_id, entity_type)
    WHERE is_active = true;

-- ============================================
-- 4. 코멘트 추가
-- ============================================

COMMENT ON COLUMN chunks.primary_entity IS '청크의 주 엔티티명 (페이지 제목에서 추출)';
COMMENT ON COLUMN chunks.entity_type IS '엔티티 유형: boss, weapon, armor, location, npc, item, spell, mechanic, unknown';

-- ============================================
-- 완료 메시지
-- ============================================
DO $$
BEGIN
    RAISE NOTICE 'Migration 005_entity_tagging.sql completed successfully';
    RAISE NOTICE 'Added columns: primary_entity, entity_type';
    RAISE NOTICE 'Added indexes: idx_chunks_primary_entity, idx_chunks_entity_type, idx_chunks_primary_entity_trgm, idx_chunks_game_entity_type';
END $$;
