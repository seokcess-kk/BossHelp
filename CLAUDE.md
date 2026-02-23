# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
BossHelp는 소울라이크/메트로바니아 게임 가이드를 위한 AI Q&A 플랫폼입니다. Reddit/Wiki에서 크롤링한 데이터를 RAG 파이프라인으로 처리하여 게임 관련 질문에 답변합니다.

## Architecture

### 3-Tier Architecture
```
[Frontend]          [Backend]           [Database]
Next.js 16    →    FastAPI RAG    →    Supabase
React 19           Claude + OpenAI     PostgreSQL + pgvector
```

### RAG Pipeline Flow
```
Query → Entity Detection → Embedding → Vector Search → Rerank → Prompt → Claude → Answer
       (dictionary.py)    (embeddings.py)  (retriever.py)  (reranker.py)  (claude.py)
```

### Data Pipeline Flow (Crawler)
```
Crawl → Clean → Classify → Quality Score → Chunk → Embed → Store
(reddit/wiki)  (cleaner.py)  (classifier.py)  (quality.py)  (chunker.py)  (embedder.py)
```

## Commands

```bash
# Frontend (port 3000)
cd frontend && npm run dev
cd frontend && npm run build
cd frontend && npm run lint

# Backend (port 8000)
cd backend && uvicorn app.main:app --reload
cd backend && python -m pytest

# Crawler
cd crawler && python pipeline.py --mode initial --games elden-ring
cd crawler && python pipeline.py --mode update

# Database
# Supabase SQL Editor에서 실행: supabase/migrations/*.sql
```

## Environment Variables

### Backend (.env)
- `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` - Supabase 연결
- `ANTHROPIC_API_KEY` - Claude API (답변 생성)
- `OPENAI_API_KEY` - OpenAI Embeddings (text-embedding-3-small, 1536차원)
- `ADMIN_API_KEY` - 관리자 API 인증

### Crawler (.env)
- `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET` - Reddit API
- Supabase + OpenAI 동일

### Frontend
- `NEXT_PUBLIC_API_URL` - Backend API URL

## Key Modules

### Backend
- `app/core/rag/pipeline.py` - RAG 파이프라인 오케스트레이터
- `app/core/rag/retriever.py` - pgvector 벡터 검색
- `app/core/entity/dictionary.py` - 게임별 엔티티 사전 (용어 정규화)
- `app/api/v1/ask.py` - Q&A 엔드포인트

### Frontend
- `src/hooks/useChat.ts` - 채팅 상태 관리 (React Query)
- `src/stores/chat-store.ts` - Zustand 전역 상태
- `src/lib/api.ts` - API 클라이언트

### Database (Supabase)
- `chunks` - 벡터 DB (embedding VECTOR(1536))
- `games` - 지원 게임 목록
- `conversations` - 대화 로그

## Conventions
- API endpoints: `/api/v1/...` (public), `/api/admin/...` (internal)
- Frontend components: PascalCase
- Backend modules: snake_case
- 비즈니스 로직 주석: 한국어
- Spoiler levels: `none`, `light`, `heavy`
- Categories: `boss_guide`, `build_guide`, `progression_route`, `npc_quest`, `item_location`, `mechanic_tip`, `secret_hidden`

## Work Logging (필수)

**모든 작업은 반드시 기록해야 합니다.**

### 작업 시작 시
1. `docs/WORKLOG.md`에 새 항목 추가 (WL-XXX 형식)
2. 요청 내용, 예상 수정 파일 기록

### 작업 완료 시
1. `docs/WORKLOG.md` 상태를 ✅ 완료로 변경
2. 실제 수정된 파일, 커밋 해시 기록
3. 중요 변경 시 `docs/04-report/changelog.md`도 업데이트

### 버그/이슈 발견 시
1. `docs/WORKLOG.md`의 미해결 이슈 섹션에 TODO-XXX로 추가

### 참고 파일
- `docs/WORKLOG.md` - 작업 요청/완료 로그 (중복 방지용)
- `docs/04-report/changelog.md` - 버전별 변경 이력
- `docs/.pdca-status.json` - PDCA 자동 추적 (bkit)
