# BossHelp - AI Game Guide Q&A Platform

## Project Level
**Dynamic** - Fullstack with BaaS (Supabase)

## Tech Stack
- **Frontend**: Next.js 14 (App Router) + TypeScript + TailwindCSS
- **Backend**: Python FastAPI (RAG Pipeline)
- **Database**: Supabase (PostgreSQL + pgvector)
- **LLM**: Claude Sonnet 4 + OpenAI Embeddings

## Project Structure
```
bosshelp/
├── frontend/          # Next.js 14 App
├── backend/           # FastAPI Backend
├── crawler/           # Data Pipeline (Phase 2)
├── supabase/          # DB Migrations
└── docs/              # PDCA Documents
```

## Key Commands
```bash
# Frontend
cd frontend && npm run dev

# Backend
cd backend && uvicorn app.main:app --reload

# Database Migration
# Run in Supabase SQL Editor: supabase/migrations/001_initial_schema.sql
```

## Current Phase
- Phase 1: Foundation (완료)
- Phase 2: Data Pipeline (다음)
- Phase 3: RAG Backend
- Phase 4: Frontend Integration

## Conventions
- TypeScript strict mode
- Korean comments for business logic
- API endpoints: `/api/v1/...`
- Components: PascalCase
- Files: kebab-case or camelCase

## Important Files
- `docs/01-plan/bosshelp-mvp.md` - Plan document
- `docs/02-design/features/bosshelp-mvp.design.md` - Design document
- `supabase/migrations/001_initial_schema.sql` - DB schema
