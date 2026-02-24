# BossHelp 작업 로그 (WORKLOG)

> 모든 요청사항, 수정사항, 버그 수정을 기록하여 중복 작업을 방지합니다.

---

## 2026-02-24

### [WL-016] RAG 답변 최적화 구현 (answer-optimization)
- **요청**: RAG 파이프라인 답변 품질 향상 및 응답 속도 개선
- **구현 내용**:
  - **Phase 1: 스트리밍 응답 (SSE)**
    - `backend/app/api/v1/ask_stream.py`: SSE 스트리밍 엔드포인트
    - `backend/app/core/rag/pipeline.py`: `run_stream()`, `prepare_context()` 메서드 추가
    - `frontend/src/lib/api.ts`: `askStream()` 함수 추가
  - **Phase 2: 프롬프트 최적화**
    - `backend/app/core/rag/prompt.py`: `SYSTEM_PROMPT_V2` (환각 방지 강화)
    - 신뢰도 등급 시스템 (`high`, `medium`, `low`)
    - 답변 구조화 템플릿 (핵심→상세→출처)
  - **Phase 3: 캐싱 시스템**
    - `backend/app/core/cache/query_cache.py`: TTL 기반 쿼리 결과 캐싱
    - `backend/app/core/cache/embedding_cache.py`: LRU 임베딩 캐싱
  - **Phase 4: 다단계 리랭킹**
    - `backend/app/core/rag/reranker.py`: `MultiStageReranker` 클래스
    - 질문 유형 감지 및 카테고리 부스트
    - 키워드 부스트, 품질 필터, 중복 제거
- **API 변경**:
  - `POST /api/v1/ask/stream`: SSE 스트리밍 엔드포인트 추가
  - AskResponse에 `confidence`, `cached` 필드 추가
- **의존성 추가**: `cachetools==5.3.0`
- **목표 지표**:
  - 평균 응답 시간: ~3000ms → <2000ms
  - 첫 토큰 시간: ~3000ms → <1000ms (스트리밍)
  - 캐시 적중 응답: <100ms
- **상태**: ✅ 완료 (PDCA Report 생성)

### [WL-015] Hollow Knight 추가 데이터 수집
- **요청**: Gap Analysis에서 확인된 Hollow Knight 데이터 부족 해결
- **원인**: 기존 811 chunks로 목표(2,000+) 미달 (40%)
- **수집 내용**:
  - `crawl_hollow_knight_extra.py`: 전용 크롤러 생성
  - 수집 카테고리: Bosses(42), Charms(43), Items(35), NPCs(49), Enemies(50), Spells(28), Nail Arts(12), Locations(40), Lore(44) 등
  - 총 352 페이지 → **942 chunks 추가**
- **결과**:
  - 기존: 811 chunks
  - 추가: 942 chunks
  - 최종: **1,753 chunks** (목표 대비 87%)
- **Match Rate**: 96% → **98%** 향상
- **상태**: ✅ 완료

---

## 2026-02-23

### [WL-014] 보스/아이템 추가 데이터 수집 및 RAG 검증
- **요청**: 보스 공략, 아이템 위치 데이터 부족 문제 해결
- **수집 내용**:
  - `crawl_bosses_items.py`: 카테고리별 집중 크롤링 (4,854 chunks)
  - `crawl_specific_pages.py`: 주요 보스/무기 페이지 직접 크롤링 (702 chunks)
- **수정 내용**:
  - `backend/app/core/rag/retriever.py`: 키워드 추출 시 구두점 제거 버그 수정
- **RAG 테스트 결과**:
  - Malenia 공략: ✅ (heavy spoiler 설정 시 상세 공략 제공)
  - Radahn 공략: ✅ (Scarlet Rot 전략 등)
  - Moonveil 위치: ✅ (Gael Tunnel, Magma Wyrm)
- **참고**: 보스 공략 정보는 heavy spoiler로 분류됨 (의도된 동작)
- **상태**: ✅ 완료

### [WL-013] 나머지 게임 데이터 수집 완료
- **요청**: 다크소울 외 나머지 게임들의 데이터 수집
- **수집 대상**: Elden Ring, Dark Souls 3, Sekiro, Dark Souls 2, Lies of P, Hollow Knight, Silksong
- **수집 방법**: Reddit JSON API + Fextralife Wiki 크롤링
- **결과**:
  | Game | Reddit | Wiki | Chunks |
  |------|--------|------|--------|
  | Elden Ring | 41 | 349 | 12,046 |
  | Dark Souls 3 | 23 | 229 | 7,752 |
  | Sekiro | 28 | 208 | 3,610 |
  | Dark Souls 2 | 41 | 249 | 4,764 |
  | Lies of P | 37 | 247 | 2,045 |
  | Hollow Knight | 76 | 150 | 811 |
  | Silksong | 76 | 0 | 33 |
  | **Total** | **322** | **1,432** | **31,061** |
- **스크립트**: `crawler/crawl_remaining_games.py` (신규 생성)
- **상태**: ✅ 완료

### [WL-012] Query Translation 버그 수정
- **요청**: 한글 질문 번역 후 검색 실패 문제
- **원인**:
  - Haiku 모델 ID 오류 (`claude-3-5-haiku-20241022` → 존재하지 않음)
  - 벡터 검색 시 원본 한글 쿼리 사용 (번역된 쿼리 미사용)
  - 키워드 추출이 엔티티 이름 대신 일반 단어 선택
- **수정 내용**:
  - `backend/app/core/rag/translator.py`:
    - 모델 ID 수정: `claude-3-haiku-20240307`
  - `backend/app/core/rag/pipeline.py`:
    - retriever.search()에 `translated_query` 전달
  - `backend/app/core/rag/retriever.py`:
    - 키워드 추출 시 대문자 단어(엔티티) 우선 선택
- **테스트 결과**:
  - "보르트 보스 공략 알려줘" → ✅ Vordt 공략 응답 성공
  - "PvP 빌드 추천해줘" → ✅ 빌드 추천 응답 성공
- **커밋**: `dbf2b5b`
- **상태**: ✅ 완료

### [WL-011] RAG 파이프라인 한글/영어 질문 지원
- **요청**: 한글 질문 "타소니아 공략 방법 알려줘" → "관련 정보를 찾지 못했습니다" 문제 해결
- **원인**: 크롤링 데이터는 영어(Wiki/Reddit), 질문은 한글 → 임베딩 매칭 불가
- **수정 내용**:
  - `backend/app/core/rag/translator.py` (신규 생성):
    - QueryTranslator 클래스 - Haiku 모델로 한글→영어 번역
    - LRU 캐싱으로 동일 질문 재번역 방지
    - 이미 영어인 질문은 그대로 통과
  - `backend/app/core/rag/pipeline.py`:
    - translator import 및 의존성 주입
    - run() 메서드에 번역 단계 추가 (Step 1)
- **테스트 결과**:
  - Before: "심연의 감시자 공략" → 검색 실패
  - After: "심연의 감시자 공략" → "Abyss Watchers guide" 번역 → 검색 성공
- **커밋**: `038d218`
- **상태**: ✅ 완료

### [WL-010] Ask API Mock 모드 제거 및 실제 RAG 연동
- **요청**: 프론트에서 질문 시 "[개발 모드]" Mock 응답 대신 실제 RAG 파이프라인 사용
- **원인**:
  - Backend: `VALID_GAMES` 하드코딩 리스트에 다크소울 시리즈 미포함
  - Backend: RAG 실패 시 Mock fallback 존재
  - Frontend: API 에러 시 Mock 응답 반환
- **수정 내용**:
  - `backend/app/api/v1/ask.py`:
    - `VALID_GAMES` 하드코딩 제거 → DB에서 게임 검증 (`validate_game_id()`)
    - `is_rag_available()` 체크 및 Mock fallback 완전 제거
    - 모든 질문이 RAG 파이프라인으로 처리됨
  - `frontend/src/stores/chat-store.ts`:
    - Mock fallback 응답 제거
    - API 에러 시 `error` 상태로 표시
- **커밋**: `e3cfbe9`
- **상태**: ✅ 완료

### [WL-009] Dockerfile 빌드 컨텍스트 경로 수정
- **요청**: Railway 배포 실패 - requirements.txt not found
- **원인**: 루트 railway.json에서 빌드 컨텍스트가 루트인데, Dockerfile은 backend/ 기준 경로 사용
- **수정 파일**:
  - `backend/Dockerfile` - `COPY backend/requirements.txt`, `COPY backend/ .`로 변경
  - `.dockerignore` (루트) - 빌드 컨텍스트용 신규 생성
- **커밋**: `d6c8317`
- **상태**: ✅ 완료

### [WL-008] Health 엔드포인트 진단 정보 추가
- **요청**: Railway가 어떤 Supabase에 연결되어 있는지 확인
- **수정 파일**: `backend/app/main.py` - supabase_project, env, version 추가
- **커밋**: `16fe5eb`
- **상태**: ✅ 완료

### [WL-007] 프로덕션 환경변수 설정 수정
- **요청**: Railway 환경변수가 반영되지 않는 문제 해결
- **원인**: pydantic-settings에서 `.env` 파일이 환경변수보다 우선됨
- **수정 파일**:
  - `backend/app/config.py` - ENV=development일 때만 .env 로드
  - `backend/app/api/v1/games.py` - 디버그 엔드포인트 제거
- **커밋**: `1f52d1d`
- **상태**: ✅ 완료

### [WL-006] .dockerignore 추가
- **요청**: Docker 이미지에서 .env 파일 제외
- **수정 파일**: `backend/.dockerignore` 생성
- **커밋**: `41e7b13`
- **상태**: ✅ 완료

### [WL-005] Frontend 게임 목록 DB 연동
- **요청**: 하드코딩된 게임 목록 대신 DB에서 로드
- **수정 파일**:
  - `frontend/src/stores/game-store.ts` - API 호출 추가
  - `frontend/src/lib/api.ts` - snake_case → camelCase 변환
  - `frontend/src/app/page.tsx` - useGames 훅 사용
- **커밋**: `c5bd7c9` ~ `e5e4cd1`
- **상태**: ✅ 완료

### [WL-004] 다크소울 시리즈 데이터 추가
- **요청**: Dark Souls 1/2/3 게임 데이터 크롤링 및 DB 저장
- **수정 파일**:
  - `crawler/crawl_dark_souls_json.py` - 크롤러 스크립트
  - `crawler/crawlers/wiki.py` - Wiki 크롤러 개선
  - Supabase games 테이블 - 3개 게임 추가
- **커밋**: `394fb5a`
- **상태**: ✅ 완료

---

## 2026-02-22

### [WL-003] Railway 배포 설정
- **요청**: Backend를 Railway에 배포
- **수정 파일**:
  - `backend/railway.json` - Railway 설정
  - `backend/Dockerfile` - Docker 빌드 설정
  - `railway.json` (root) - 모노레포 지원
- **커밋**: `ccd6774`, `ae6d334`
- **상태**: ✅ 완료

### [WL-002] Vercel 배포 수정
- **요청**: Frontend Vercel 배포 오류 수정
- **수정 파일**: `frontend/next.config.ts` - standalone 제거
- **커밋**: `55d3138`
- **상태**: ✅ 완료

---

## 2026-02-15

### [WL-001] MVP 초기 릴리스
- **요청**: BossHelp MVP 개발 및 배포
- **내용**: Frontend, Backend, Crawler, Database 전체 구현
- **커밋**: `cfbf650`
- **상태**: ✅ 완료

---

## 미해결 이슈 (TODO)

| ID | 설명 | 우선순위 | 상태 |
|----|------|----------|------|
| ~~TODO-001~~ | ~~Frontend Mock 데이터 제거 (ask.py, chat-store.ts)~~ | ~~중간~~ | ✅ WL-010 완료 |
| TODO-002 | 게임 상세 페이지 하드코딩 제거 | 낮음 | 대기 |
| TODO-003 | 인기 질문 DB 연동 (현재 Mock) | 낮음 | 대기 |

---

## 기록 규칙

1. **새 작업 시작 시**: 이 파일에 새 항목 추가 (WL-XXX)
2. **작업 완료 시**: 상태를 ✅ 완료로 변경, 커밋 해시 기록
3. **버그 발견 시**: 미해결 이슈에 TODO-XXX로 추가
4. **중요 변경 시**: changelog.md도 함께 업데이트

---

Last updated: 2026-02-24
