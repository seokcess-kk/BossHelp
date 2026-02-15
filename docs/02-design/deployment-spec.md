# BossHelp Deployment Specification

## Overview

| Item | Value |
|------|-------|
| Project | BossHelp MVP |
| Level | Dynamic |
| Created | 2026-02-15 |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Internet                             │
└─────────────────────────┬───────────────────────────────────┘
                          │
          ┌───────────────┴───────────────┐
          │                               │
          ▼                               ▼
┌─────────────────────┐      ┌─────────────────────┐
│   Vercel (Frontend) │      │  Railway (Backend)  │
│   Next.js 14        │──────│  FastAPI            │
│   icn1 (Seoul)      │      │  uvicorn            │
└─────────────────────┘      └──────────┬──────────┘
                                        │
                                        ▼
                             ┌─────────────────────┐
                             │ Supabase (Database) │
                             │ PostgreSQL+pgvector │
                             └─────────────────────┘
```

## Services

### Frontend (Vercel)

| Setting | Value |
|---------|-------|
| Framework | Next.js 14 |
| Region | icn1 (Seoul) |
| Build Command | `npm run build` |
| Output Directory | `.next` |
| Node.js Version | 20.x |

### Backend (Railway)

| Setting | Value |
|---------|-------|
| Runtime | Python 3.12 |
| Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Health Check | `/health` |
| Timeout | 30s |

### Database (Supabase)

| Setting | Value |
|---------|-------|
| Provider | Supabase |
| Database | PostgreSQL 15 |
| Extensions | pgvector, pg_trgm |
| Region | ap-northeast-2 (Seoul) |

## Environment Variables

### Frontend (Vercel)

| Variable | Environment | Description |
|----------|-------------|-------------|
| `NEXT_PUBLIC_API_URL` | All | Backend API URL |
| `NEXT_PUBLIC_SUPABASE_URL` | All | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | All | Supabase anon key |

### Backend (Railway)

| Variable | Environment | Description |
|----------|-------------|-------------|
| `SUPABASE_URL` | All | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | All | Supabase service role key |
| `ANTHROPIC_API_KEY` | All | Claude API key |
| `OPENAI_API_KEY` | All | OpenAI API key |
| `CORS_ORIGINS` | All | Allowed CORS origins |
| `ADMIN_API_KEY` | All | Admin API authentication |
| `ENV` | All | Environment (development/production) |

## Deployment Steps

### 1. Database Setup

```bash
# 1. Create Supabase project
# 2. Run migrations in SQL Editor
# 3. Copy API keys
```

### 2. Backend Deployment

```bash
cd backend
railway login
railway init
railway variables set [ENV_VARS]
railway up
```

### 3. Frontend Deployment

```bash
cd frontend
vercel login
vercel --prod
```

### 4. Verification

```bash
# Run verification script
BACKEND_URL=https://xxx.railway.app \
FRONTEND_URL=https://xxx.vercel.app \
bash scripts/verify-deployment.sh
```

## Security

### Headers (Frontend)

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`

### CORS (Backend)

- Only allow configured origins
- Credentials enabled
- All methods allowed

### API Authentication

- Admin endpoints require `X-Admin-Key` header
- Rate limiting: 20 requests/day (anonymous)

## Monitoring

### Health Checks

| Service | Endpoint | Interval |
|---------|----------|----------|
| Backend | `/health` | 30s |
| Frontend | `/` | 60s |

### Logs

```bash
# Backend logs
railway logs -f

# Frontend logs
vercel logs --follow
```

## Rollback

### Backend

```bash
# List deployments
railway deployments

# Rollback to previous
railway rollback
```

### Frontend

```bash
# Vercel dashboard → Deployments → Promote previous
```

## Cost Estimate

| Service | Plan | Monthly Cost |
|---------|------|--------------|
| Vercel | Hobby | Free |
| Railway | Starter | ~$5 |
| Supabase | Free | Free |
| **Total** | | **~$5/month** |
