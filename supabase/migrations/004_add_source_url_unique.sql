-- Add unique constraint on source_url for upsert support
-- Version: 4
-- Date: 2026-02-23

-- chunks 테이블의 source_url에 unique 제약조건 추가
-- source_url에 chunk 인덱스가 포함되어 있어 중복이 없음
ALTER TABLE chunks
ADD CONSTRAINT chunks_source_url_unique UNIQUE (source_url);

-- 이미 중복 데이터가 있으면 먼저 정리 필요:
-- DELETE FROM chunks a USING chunks b
-- WHERE a.id > b.id AND a.source_url = b.source_url;
