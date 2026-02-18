# BossHelp Phase 2 Plan Document

## Overview

| Item | Description |
|------|-------------|
| Feature | BossHelp Phase 2 - 미구현 항목 및 확장 기능 |
| Predecessor | `bosshelp-mvp` (96% 완료, Report 완료) |
| Version | 1.1 |
| Created | 2026-02-19 |
| Status | Planning |

---

## 1. Background

### 1.1 MVP 완료 상태

BossHelp MVP는 96% Match Rate로 프로덕션 배포 준비가 완료되었습니다.

**완료된 핵심 기능:**
- RAG 기반 AI Q&A 시스템 (Claude Sonnet 4)
- 5개 게임 지원 (Elden Ring, Sekiro, Hollow Knight, HK:Silksong, Lies of P)
- Wiki 크롤러 + 데이터 파이프라인
- Frontend (Next.js 14) + Backend (FastAPI)
- 스포일러 컨트롤, 출처 표시, 피드백 시스템

### 1.2 Phase 2 필요성

MVP에서 범위 축소 또는 시간 제약으로 구현되지 않은 항목들을 완성하고,
사용자 피드백 기반 기능을 확장하기 위해 Phase 2를 진행합니다.

---

## 2. Unimplemented Items (미구현 항목)

### 2.1 Minor Components (낮은 우선순위)

| ID | 항목 | 설계 위치 | 현재 상태 | 영향도 |
|:--:|------|----------|----------|:------:|
| U-01 | Sidebar 컴포넌트 | design.md:111 | ChatContainer에 인라인 | Low |
| U-02 | MobileNav 컴포넌트 | design.md:114 | Header에 통합 | Low |
| U-03 | GameSelector 컴포넌트 | design.md:107 | Header에 인라인 | Low |
| U-04 | Steam Crawler | design.md:65 | 미구현 | Medium |

### 2.2 Partial Implementation (부분 구현)

| ID | 항목 | 현재 상태 | 필요 작업 |
|:--:|------|----------|----------|
| P-01 | `expandAnswer()` | 스텁 구현 | Claude API 호출 연동 |
| P-02 | Reddit 데이터 수집 | 크롤러 완성, 데이터 미수집 | 5게임 Reddit 크롤링 실행 |
| P-03 | Rate Limiting | 기본 구현 | IP 기반 제한 강화 |

---

## 3. Phase 2 Goals

### 3.1 Primary Goals (P0)

| Goal | Description | Success Criteria |
|------|-------------|------------------|
| 데이터 보강 | Reddit 크롤링 데이터 추가 | 총 15K+ chunks |
| Steam Crawler | Steam 가이드 크롤러 구현 | 게임당 500+ chunks 추가 |
| expandAnswer 완성 | "더 자세히" 기능 완전 구현 | 800자 확장 답변 |

### 3.2 Secondary Goals (P1)

| Goal | Description | Success Criteria |
|------|-------------|------------------|
| User Authentication | 로그인/회원가입 | Supabase Auth 연동 |
| Chat History | 대화 기록 저장 | 세션별 히스토리 조회 |
| Rate Limiting 강화 | IP 기반 제한 | 20회/일 제한 정확 적용 |

### 3.3 Tertiary Goals (P2)

| Goal | Description | Success Criteria |
|------|-------------|------------------|
| Analytics Dashboard | 사용 통계 대시보드 | 일일 질문 수, 인기 질문 |
| Component 분리 | Sidebar, MobileNav 추출 | 독립 컴포넌트 파일 |
| Multi-language | 다국어 지원 (영어) | i18n 적용 |

---

## 4. Implementation Plan

### Phase 2-A: 데이터 보강 (3-5일)

```
순서:
1. Reddit 크롤링 실행
   - Elden Ring: r/Eldenring top 1000
   - Sekiro: r/Sekiro top 500
   - Hollow Knight: r/HollowKnight top 500
   - Lies of P: r/LiesOfP top 500
   - 예상: 3000+ chunks 추가

2. Steam Crawler 구현
   - Steam API 연동
   - Guide 카테고리 크롤링
   - BeautifulSoup 파싱
   - 예상: 2000+ chunks 추가

3. 데이터 품질 검증
   - 중복 제거
   - 품질 점수 재계산
   - 임베딩 생성
```

### Phase 2-B: 핵심 기능 완성 (3-5일)

```
순서:
1. expandAnswer 완성 (1일)
   - Claude API expand 모드 구현
   - 프론트엔드 연동
   - 800자 확장 답변 테스트

2. Rate Limiting 강화 (1일)
   - IP + Session 기반 제한
   - Redis 또는 메모리 캐시 적용
   - 20회/일 정확 카운팅

3. 데이터 품질 개선 (1-2일)
   - 중복 청크 제거
   - 품질 점수 재계산
   - 검색 결과 정확도 향상
```

### Phase 2-C: 기능 확장 (1-2주)

```
순서:
1. User Authentication (3일)
   - Supabase Auth 연동
   - Login/Signup 페이지
   - Protected routes

2. Chat History (2일)
   - conversations 테이블 활용
   - 히스토리 조회 API
   - UI 컴포넌트

3. Analytics Dashboard (5일)
   - 일일 통계 API
   - 차트 컴포넌트
   - 관리자 페이지
```

### Phase 2-D: UI 개선 (선택적)

```
순서:
1. Component 분리 (1일)
   - Sidebar 컴포넌트 추출
   - MobileNav 컴포넌트 추출
   - GameSelector 컴포넌트 추출

2. 반응형 개선 (1일)
   - 모바일 UX 개선
   - 태블릿 레이아웃 최적화
```

---

## 5. Technical Specifications

### 5.1 Steam Crawler

```python
# crawler/crawlers/steam.py
class SteamCrawler:
    """
    Steam Guide 수집기
    - Library: Steam Web API + BeautifulSoup
    - Rate: 10 QPM (conservative)
    - Categories: Guide, FAQ, Walkthrough
    """

    CONFIG = {
        "elden-ring": {
            "app_id": "1245620",
            "guide_url": "https://steamcommunity.com/app/1245620/guides/",
        },
        "sekiro": {
            "app_id": "814380",
            "guide_url": "https://steamcommunity.com/app/814380/guides/",
        },
        # ... other games
    }

    def crawl_guides(self, game_id: str, limit: int = 100):
        """Steam Guide 크롤링"""
        pass
```

### 5.2 expandAnswer 구현

```python
# backend/app/core/rag/pipeline.py
def run(self, ..., expanded: bool = False) -> RAGResult:
    """
    expanded=True일 때:
    - max_tokens: 1500 (기본 500)
    - 답변 길이: ~800자 (기본 ~300자)
    - 추가 컨텍스트 포함
    """

    max_tokens = 1500 if expanded else 500

    answer = self.claude_client.generate_answer(
        system_prompt=system_prompt,
        user_message=user_message,
        max_tokens=max_tokens,
        expanded=expanded,
    )
```

### 5.3 User Authentication

```typescript
// Supabase Auth 연동
// frontend/src/lib/auth.ts
import { createClientComponentClient } from '@supabase/auth-helpers-nextjs'

export const supabase = createClientComponentClient()

export async function signIn(email: string, password: string) {
  return supabase.auth.signInWithPassword({ email, password })
}

export async function signUp(email: string, password: string) {
  return supabase.auth.signUp({ email, password })
}

export async function signOut() {
  return supabase.auth.signOut()
}
```

### 5.4 Chat History API

```python
# backend/app/api/v1/history.py
@router.get("/history/{session_id}")
async def get_chat_history(
    session_id: str,
    limit: int = 50,
) -> list[ConversationResponse]:
    """세션별 대화 기록 조회"""
    pass

@router.delete("/history/{session_id}")
async def clear_chat_history(session_id: str):
    """대화 기록 삭제"""
    pass
```

### 5.5 Rate Limiting 강화

```python
# backend/app/middleware/rate_limit.py
from collections import defaultdict
from datetime import datetime, timedelta

class RateLimiter:
    """IP + Session 기반 Rate Limiting"""

    def __init__(self, limit: int = 20, window: timedelta = timedelta(days=1)):
        self.limit = limit
        self.window = window
        self.requests = defaultdict(list)

    def is_allowed(self, identifier: str) -> bool:
        """요청 허용 여부 확인"""
        now = datetime.now()
        cutoff = now - self.window

        # 오래된 요청 제거
        self.requests[identifier] = [
            t for t in self.requests[identifier] if t > cutoff
        ]

        if len(self.requests[identifier]) >= self.limit:
            return False

        self.requests[identifier].append(now)
        return True
```

---

## 6. Timeline

| Week | Phase | Tasks | Deliverables |
|:----:|-------|-------|--------------|
| 1 | 2-A | Reddit 크롤링, Steam Crawler | 5K+ 추가 chunks |
| 1-2 | 2-B | expandAnswer, Rate Limiting | 핵심 기능 완성 |
| 2-3 | 2-C | User Auth, Chat History | 인증 시스템 |
| 3-4 | 2-C/D | Analytics, Component 분리 | 대시보드, UI 개선 |

**Total Duration**: 3-4 weeks

---

## 7. Success Metrics

### 7.1 Data

| Metric | Current | Target |
|--------|:-------:|:------:|
| Total Chunks | ~10K | 20K+ |
| Reddit Chunks | 0 | 3K+ |
| Steam Chunks | 0 | 2K+ |

### 7.2 Features

| Metric | Target |
|--------|--------|
| expandAnswer | 100% 구현 |
| Rate Limiting | 정확 동작 |
| Auth 구현 | 100% |
| Chat History | 100% |

### 7.3 Quality

| Metric | Target |
|--------|--------|
| Match Rate | 98%+ |
| 검색 정확도 | 향상 |
| 응답 품질 | 향상 |

---

## 8. Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Reddit API 제한 | High | Rate limiting 준수, 점진적 수집 |
| Steam 크롤링 차단 | Medium | User-Agent 설정, 딜레이 증가 |
| LLM API 비용 | Medium | 캐싱, 답변 길이 제한 |
| 중복 데이터 | Low | 해시 기반 중복 체크 |

---

## 9. Dependencies

### 9.1 External Services

| Service | Purpose | Status |
|---------|---------|--------|
| Supabase | Database + Auth | Active |
| Anthropic API | Claude LLM | Active |
| OpenAI API | Embeddings | Active |
| Reddit API | Data Source | Pending |
| Steam API | Data Source | Pending |

### 9.2 Prerequisites

- [x] MVP 96% 완료
- [x] Design Document 완료
- [ ] Reddit API Credentials 확인
- [ ] Steam API Key (optional)

---

## 10. Priority Order

### Immediate (This Week)

| 순위 | 작업 | 예상 기간 |
|:----:|------|:--------:|
| 1 | Reddit 크롤링 실행 | 2일 |
| 2 | expandAnswer 완성 | 1일 |
| 3 | Rate Limiting 강화 | 1일 |

### Next Week

| 순위 | 작업 | 예상 기간 |
|:----:|------|:--------:|
| 4 | Steam Crawler 구현 | 3일 |
| 5 | User Authentication | 3일 |
| 6 | Chat History | 2일 |

### Later

| 순위 | 작업 | 예상 기간 |
|:----:|------|:--------:|
| 7 | Analytics Dashboard | 5일 |
| 8 | Component 분리 | 1일 |
| 9 | Multi-language | 3일 |

---

## Document Info

| Item | Value |
|------|-------|
| Version | 1.1 |
| Created | 2026-02-19 |
| Updated | 2026-02-19 |
| Author | Claude (AI) |
| Status | Planning |
| Predecessor | `bosshelp-mvp` |
| Next Step | `/pdca design bosshelp-phase2` |
