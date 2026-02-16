# BossHelp Data Collection Plan

## Overview

| Item | Value |
|------|-------|
| Feature | data-collection |
| Phase | Plan |
| Created | 2026-02-15 |
| Status | Planning |

## Background

BossHelp MVP가 배포되었으나, 현재 데이터베이스에 실제 게임 공략 데이터가 없습니다.
RAG 파이프라인이 정상 작동하려면 Reddit/Wiki에서 수집한 실제 데이터가 필요합니다.

## Goals

1. Reddit API 연동하여 게임별 공략 데이터 수집
2. Wiki 크롤링으로 보스/아이템/지역 정보 수집
3. 데이터 처리 및 임베딩 생성
4. Supabase에 벡터 데이터 저장

## Implementation Phases

### Phase 1: Reddit API 설정 (우선순위: 높음)

**목표**: Reddit API 인증 및 기본 크롤링 테스트

**작업 내용**:
1. Reddit App 생성 및 API 키 발급
   - https://www.reddit.com/prefs/apps
   - "script" 타입 앱 생성
   - client_id, client_secret 획득

2. 환경변수 설정
   ```
   REDDIT_CLIENT_ID=xxx
   REDDIT_CLIENT_SECRET=xxx
   REDDIT_USER_AGENT=BossHelp/1.0
   ```

3. 연결 테스트
   - PRAW 라이브러리로 subreddit 접근 테스트
   - r/Eldenring 에서 샘플 포스트 가져오기

**예상 결과**: Reddit API 정상 연결, 샘플 데이터 출력

### Phase 2: 게임별 데이터 수집 (우선순위: 높음)

**목표**: 5개 게임의 Reddit 데이터 수집

**작업 내용**:
1. Elden Ring (r/Eldenring)
   - Guide, Tips/Hints, Help, Strategy 플레어 포스트
   - 최소 10 upvote 이상
   - 최근 1년 이내 포스트

2. Sekiro (r/Sekiro)
   - Guide, Tips, Help 플레어 포스트

3. Hollow Knight (r/HollowKnight)
   - Guide, Tips & Tricks, Help 플레어 포스트

4. Lies of P (r/LiesOfP)
   - Guide, Tips, Help, Build 플레어 포스트

5. Silksong (r/HollowKnight)
   - Silksong, News 플레어 (출시 전이므로 제한적)

**예상 결과**: 게임당 100-500개 포스트 수집

### Phase 3: Wiki 크롤링 (우선순위: 중간)

**목표**: Fextralife Wiki에서 보스/아이템 정보 수집

**작업 내용**:
1. Elden Ring Wiki
   - 보스 페이지: 전략, 약점, 드롭 아이템
   - 무기/방어구 페이지: 스탯, 획득 방법
   - 지역 페이지: 탐색 가이드

2. Sekiro Wiki
   - 보스 공략, 의수인법, 스킬 정보

3. Hollow Knight Wiki
   - 보스 공략, 부적, 지역 정보

4. Lies of P Wiki
   - 보스 공략, 무기, 레기온 암 정보

**예상 결과**: 게임당 200-1000개 페이지 수집

### Phase 4: 데이터 처리 파이프라인 (우선순위: 높음)

**목표**: 수집된 데이터 정제 및 임베딩

**작업 내용**:
1. 텍스트 정제 (cleaner.py)
   - 마크다운/HTML 태그 제거
   - 링크 정리
   - 특수문자 처리

2. 분류 (classifier.py)
   - 카테고리 자동 분류: boss, item, location, build, general

3. 품질 필터링 (quality.py)
   - 길이, 정보량, 관련성 점수 계산
   - 최소 품질 기준 미달 데이터 제외

4. 청킹 (chunker.py)
   - 500 토큰 단위로 분할
   - 100 토큰 오버랩

5. 임베딩 생성 (embedder.py)
   - OpenAI text-embedding-3-small
   - 배치 처리 (100개 단위)

**예상 결과**: 처리된 청크 5,000-20,000개

### Phase 5: 데이터 저장 및 검증 (우선순위: 높음)

**목표**: Supabase에 데이터 저장 및 검색 테스트

**작업 내용**:
1. Supabase 저장
   - knowledge_base 테이블에 upsert
   - 중복 처리 (source_url 기준)

2. 벡터 검색 테스트
   - 샘플 질문으로 검색 테스트
   - Top-K 결과 품질 확인

3. RAG 파이프라인 통합 테스트
   - 실제 질문-답변 테스트
   - 응답 품질 검증

**예상 결과**: RAG 파이프라인 정상 작동, 품질 좋은 답변 생성

## Timeline

| Phase | 작업 | 예상 기간 |
|-------|------|----------|
| 1 | Reddit API 설정 | 1일 |
| 2 | 게임별 데이터 수집 | 2-3일 |
| 3 | Wiki 크롤링 | 2-3일 |
| 4 | 데이터 처리 | 1-2일 |
| 5 | 저장 및 검증 | 1일 |
| **Total** | | **7-10일** |

## Prerequisites

1. **Reddit API 계정**
   - Reddit 계정 필요
   - https://www.reddit.com/prefs/apps 에서 앱 생성

2. **환경변수**
   ```bash
   # .env (crawler/.env)
   REDDIT_CLIENT_ID=your_client_id
   REDDIT_CLIENT_SECRET=your_client_secret
   REDDIT_USER_AGENT=BossHelp/1.0
   SUPABASE_URL=https://xxx.supabase.co
   SUPABASE_SERVICE_KEY=xxx
   OPENAI_API_KEY=sk-xxx
   ```

3. **Rate Limiting 준수**
   - Reddit: 초당 1 요청 (1초 딜레이)
   - Wiki: 초당 0.67 요청 (1.5초 딜레이)
   - OpenAI: 분당 3,000 RPM

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Reddit API 제한 | 중간 | Rate limiting 준수, 점진적 수집 |
| Wiki 구조 변경 | 낮음 | 선택자 기반 크롤링, 에러 핸들링 |
| 임베딩 비용 | 낮음 | text-embedding-3-small 사용 (저비용) |
| 데이터 품질 | 중간 | 품질 필터링 강화 |

## Success Criteria

- [ ] Reddit API 연동 완료
- [ ] 게임당 최소 100개 이상 포스트 수집
- [ ] Wiki 페이지 500개 이상 수집
- [ ] 임베딩 5,000개 이상 생성
- [ ] RAG 검색 테스트 통과
- [ ] 실제 질문에 대한 유의미한 답변 생성

## Next Steps

1. `/pdca design data-collection` - 상세 설계 문서 작성
2. Reddit App 생성 및 API 키 발급
3. 크롤러 테스트 실행
