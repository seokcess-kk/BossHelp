# BossHelp MVP Implementation Plan

## Project Overview

| Item | Description |
|------|-------------|
| Project Name | BossHelp |
| Level | Dynamic (Fullstack with BaaS) |
| Description | 하드코어 게임 전문 AI Q&A 플랫폼 |
| Target | 25~35세 하드코어 게이머 |
| Core Value | "막히면 물어봐. 바로 알려줄게." - 3초 내 정확한 답변 |

---

## 1. MVP Scope (8주)

### 1.1 Core Features (Must-Have)

| Feature | Description | Priority |
|---------|-------------|----------|
| 게임 선택 UI | 5개 게임 (Elden Ring, Sekiro, HK, HK:Silksong, Lies of P) | P0 |
| 질문 입력 | 자연어 질문 + 스포일러 레벨 선택 | P0 |
| RAG 기반 AI 답변 | pgvector + Claude Sonnet 4 | P0 |
| 출처 표시 | 원본 URL + 신뢰도 점수 | P0 |
| 스포일러 컨트롤 | none/light/heavy 3단계 | P0 |
| 피드백 시스템 | "도움 됨/안 됨" 버튼 | P0 |
| 모바일 반응형 | PC/모바일 대응 | P0 |

### 1.2 Data Pipeline

| Component | Description |
|-----------|-------------|
| Reddit Crawler | PRAW (OAuth), 게임별 subreddit |
| Wiki Crawler | BeautifulSoup4, Fextralife Wiki |
| Steam Crawler | Steam Web API + BS4 |
| Data Processing | Clean → Classify(7 카테고리) → Quality Score → Chunk → Embedding |
| Vector DB | Supabase pgvector (1536차원) |

### 1.3 7-Category Classification

```
boss_guide      - 보스 공략, 패턴 분석
build_guide     - 캐릭터 빌드, 무기 추천
progression_route - 진행 순서, 추천 루트
npc_quest       - NPC 위치, 퀘스트 진행
item_location   - 아이템 획득 위치
mechanic_tip    - 게임 메카닉 설명
secret_hidden   - 숨겨진 요소, 이스터에그
```

---

## 2. Tech Stack

### 2.1 Frontend
```
- Next.js 14+ (App Router)
- TypeScript
- TailwindCSS
- TanStack Query (데이터 페칭)
- Zustand (상태 관리)
```

### 2.2 Backend
```
- Python FastAPI (RAG 파이프라인)
- Supabase (PostgreSQL + pgvector + Auth)
- Claude Sonnet 4 (LLM)
- OpenAI text-embedding-3-small (Embedding)
```

### 2.3 Deployment
```
- Vercel (Frontend)
- Railway (FastAPI Backend)
- Supabase Cloud (Database)
```

---

## 3. Database Schema

### 3.1 Core Tables

```sql
-- 게임 목록
games (
  id TEXT PRIMARY KEY,        -- 'elden-ring', 'sekiro'
  title TEXT NOT NULL,
  genre TEXT NOT NULL,        -- 'soulslike', 'metroidvania', 'action_rpg'
  release_date DATE,
  subreddit TEXT,
  wiki_base_url TEXT,
  is_active BOOLEAN DEFAULT true
)

-- 데이터 청크 (Vector DB)
chunks (
  id UUID PRIMARY KEY,
  game_id TEXT REFERENCES games(id),
  category TEXT NOT NULL,      -- 7개 카테고리
  source_type TEXT NOT NULL,   -- 'reddit', 'wiki', 'steam'
  source_url TEXT NOT NULL,
  title TEXT,
  content TEXT NOT NULL,
  embedding VECTOR(1536),
  quality_score FLOAT DEFAULT 0.5,
  spoiler_level TEXT DEFAULT 'none',
  entity_tags TEXT[],
  is_active BOOLEAN DEFAULT true,
  feedback_helpful INT DEFAULT 0,
  feedback_not_helpful INT DEFAULT 0
)

-- 대화 로그
conversations (
  id UUID PRIMARY KEY,
  session_id TEXT NOT NULL,
  game_id TEXT REFERENCES games(id),
  question TEXT NOT NULL,
  answer TEXT NOT NULL,
  chunk_ids UUID[],
  spoiler_level TEXT DEFAULT 'none',
  is_helpful BOOLEAN,
  latency_ms INT
)
```

---

## 4. API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/ask | 질문 → AI 답변 (핵심 API) |
| GET | /api/v1/games | 게임 목록 조회 |
| GET | /api/v1/games/{id}/popular | 인기 질문 TOP 10 |
| POST | /api/v1/feedback | 피드백 제출 |
| POST | /api/admin/crawl/{id} | 크롤링 트리거 (Admin) |

### 4.1 POST /api/v1/ask

**Request:**
```json
{
  "game_id": "elden-ring",
  "question": "말레니아 어떻게 깸?",
  "spoiler_level": "none",
  "session_id": "abc-123"
}
```

**Response:**
```json
{
  "answer": "말레니아(Malenia)는 출혈 회피가 핵심입니다...",
  "sources": [
    {"url": "...", "title": "...", "source_type": "reddit", "quality_score": 0.87}
  ],
  "conversation_id": "uuid-...",
  "has_detail": true,
  "latency_ms": 1823
}
```

---

## 5. Quality Metrics (MVP 기준)

| Metric | Target | Measurement |
|--------|--------|-------------|
| Groundedness | ≥ 90% | 답변이 chunk 근거 기반인가 |
| Hallucination | ≤ 5% | 허위 정보 비율 |
| Citation Precision | ≥ 85% | 출처 URL 정확성 |
| Response Time | ≤ 3초 | P95 기준 |

---

## 6. Development Phases

### Phase 1: Foundation (Week 1-2)
- [ ] Next.js + TailwindCSS 프로젝트 초기화
- [ ] Supabase 프로젝트 생성 + pgvector 활성화
- [ ] DB 스키마 생성 (games, chunks, conversations)
- [ ] FastAPI 프로젝트 초기화
- [ ] 기본 UI 레이아웃 (홈, 채팅)

### Phase 2: Data Pipeline (Week 3-4)
- [ ] Reddit Crawler 구현 (PRAW)
- [ ] Wiki Crawler 구현 (BeautifulSoup4)
- [ ] Data Cleaning & Classification 파이프라인
- [ ] Quality Score 계산 로직
- [ ] Embedding 생성 & pgvector 저장
- [ ] 5개 게임 초기 데이터 수집

### Phase 3: RAG Backend (Week 5-6)
- [ ] FastAPI RAG 엔드포인트 구현
- [ ] Vector Search + Re-ranking 로직
- [ ] Claude Sonnet 프롬프트 최적화
- [ ] 한/영 엔티티 사전 구축
- [ ] 품질 테스트셋 100문항 평가

### Phase 4: Frontend Integration (Week 7-8)
- [ ] 게임 선택 UI
- [ ] 채팅 인터페이스 (스트리밍 응답)
- [ ] 스포일러 컨트롤 UI
- [ ] 출처 표시 + 피드백 버튼
- [ ] 모바일 반응형 최적화
- [ ] 베타 런칭

---

## 7. Cost Estimation (Base Scenario)

| Item | Monthly Cost |
|------|--------------|
| Claude API (답변) | ~$45 |
| Embedding + 분류 | ~$4 |
| Supabase Pro | ~$25 |
| Vercel Pro | ~$20 |
| Railway | ~$10 |
| 크롤링 서버 | ~$5 |
| **Total** | **~$109/월** |

**손익분기점:** $3.99 구독 기준 ~33명

---

## 8. Risk & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| 저작권 이슈 | High | 요약/변환만 사용, 출처 표시, 삭제 요청 24h 대응 |
| Hallucination | High | RAG + 출처 필수, 품질 테스트 90%+ |
| API 비용 폭증 | Medium | Rate limit 20회/일 (Free), 캐싱 적용 |
| 데이터 부족 | Medium | 5개 게임 집중 → 검증 후 확장 |

---

## 9. Success Criteria

### MVP Launch (Week 8)
- [ ] 5개 게임 데이터 수집 완료
- [ ] Groundedness ≥ 90%
- [ ] P95 응답시간 ≤ 3초
- [ ] 모바일/PC 반응형 완료
- [ ] 베타 사용자 피드백 수집 시작

---

## Document Info

| Item | Value |
|------|-------|
| Version | 1.0 |
| Created | 2026-02-15 |
| Author | Claude (AI) |
| Status | Draft |
| Next Step | `/pdca design bosshelp-mvp` |
