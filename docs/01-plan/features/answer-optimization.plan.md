# Answer Optimization Plan

> RAG 파이프라인 답변 품질 향상 및 응답 속도 개선

## Overview

| Item | Value |
|------|-------|
| Feature | answer-optimization |
| Phase | Plan |
| Created | 2026-02-24 |
| Status | Planning |
| Priority | High |

---

## Background

### 현재 RAG 파이프라인 구조

```
Query → Translation → Entity Detection → Embedding → Vector Search → Rerank → Prompt → Claude → Answer
        (Haiku)       (dictionary.py)    (OpenAI)     (pgvector)     (quality)  (300자)  (Sonnet)
```

### 현재 파이프라인 상태

| 컴포넌트 | 현재 상태 | 이슈 |
|----------|----------|------|
| Translation | Haiku 사용 | 번역 품질 개선 여지 |
| Retriever | top 10 → rerank 5 | 검색 정확도 개선 필요 |
| Reranker | similarity 0.7 + quality 0.3 | 단순 점수 기반 |
| Prompt | 300자 기본 / 800자 확장 | 구조화 필요 |
| LLM | Sonnet 4, 동기 호출 | 스트리밍 미활용 |

### 개선 필요 영역

1. **답변 품질**: 환각(hallucination) 감소, 더 정확한 정보 제공
2. **응답 속도**: 현재 평균 2-4초 → 목표 1-2초

---

## Goals

### Primary Goals

1. **답변 품질 향상**
   - 환각률 감소 (현재 추정 10-15% → 목표 5% 이하)
   - 정확도 향상 (관련 정보 누락 감소)
   - 답변 구조화 (핵심 → 상세 → 출처)

2. **응답 속도 개선**
   - 평균 응답 시간 단축 (목표 50% 감소)
   - 체감 속도 향상 (스트리밍 적용)

### Secondary Goals

- 프롬프트 엔지니어링 최적화
- 리랭킹 알고리즘 개선
- 캐싱 전략 도입

---

## Proposed Solutions

### 1. 답변 품질 향상

#### 1-A. 프롬프트 엔지니어링 개선

**현재 문제**:
- 시스템 프롬프트가 일반적
- 참고 자료 포맷이 단순
- 출처 표시 일관성 부족

**개선안**:

```python
# 현재
SYSTEM_PROMPT = """당신은 BossHelp의 게임 공략 전문 AI입니다..."""

# 개선
SYSTEM_PROMPT = """당신은 BossHelp의 게임 공략 전문 AI입니다.

## 핵심 규칙
1. **절대 규칙**: 참고 자료에 없는 정보는 생성하지 마세요
2. **확실하지 않으면**: "정확한 정보를 확인하지 못했습니다"라고 답변
3. **수치 정보**: 참고 자료의 수치를 그대로 인용

## 답변 구조
1. [핵심] 질문에 대한 직접적인 답변 (1-2문장)
2. [상세] 추가 맥락 및 팁 (선택적)
3. [출처] 참고한 자료 링크

## 품질 체크리스트
- [ ] 참고 자료에서 직접 확인 가능한가?
- [ ] 추측이나 일반 지식이 섞이지 않았는가?
- [ ] 게임 버전에 따른 차이가 있을 수 있는가?
"""
```

#### 1-B. Chunk 품질 기반 신뢰도 표시

**현재**: 모든 chunk를 동등하게 취급
**개선**: 신뢰도 등급 시스템 도입

```python
# 신뢰도 등급
CONFIDENCE_LEVELS = {
    "high": quality_score >= 0.8,    # Wiki 공식 정보
    "medium": quality_score >= 0.5,  # Reddit 검증된 정보
    "low": quality_score < 0.5,      # 커뮤니티 추측
}
```

#### 1-C. 환각 방지 메커니즘

1. **출처 검증 강화**
   - 답변 내 모든 수치/사실에 chunk 참조 필수
   - 참조 없는 정보는 LLM에 재확인 요청

2. **Cross-Reference**
   - 동일 정보를 다수 chunk에서 확인
   - 일치율 낮으면 불확실성 표시

### 2. 응답 속도 개선

#### 2-A. 스트리밍 응답 활성화

**현재**: 동기 호출 → 전체 응답 대기
**개선**: 스트리밍 → 점진적 응답

```python
# backend/app/api/v1/ask.py
@router.post("/stream")
async def ask_stream(request: AskRequest):
    """Streaming response endpoint."""
    async def generate():
        for chunk in pipeline.run_stream(...):
            yield f"data: {json.dumps({'text': chunk})}\n\n"
    return StreamingResponse(generate(), media_type="text/event-stream")
```

**예상 효과**:
- 첫 토큰 응답 시간: 2-4초 → 0.5-1초
- 체감 속도 대폭 개선

#### 2-B. 병렬 처리 최적화

**현재**: 순차 처리
```
Translation (300ms) → Embedding (200ms) → Search (500ms) → Rerank (50ms) → LLM (2000ms)
Total: ~3000ms
```

**개선**: 가능한 부분 병렬화
```
Translation (300ms)
    ├── Entity Detection (병렬)
    └── Cache Check (병렬)
Embedding (200ms) → Search (500ms) → Rerank (50ms) → LLM (스트리밍)
Total: ~2000ms (첫 토큰: ~1000ms)
```

#### 2-C. 캐싱 전략

1. **Query 캐싱**
   - 동일 질문 결과 캐싱 (TTL: 1시간)
   - 해시 기반 키 생성

2. **Embedding 캐싱**
   - 빈번한 쿼리의 임베딩 캐싱
   - LRU 캐시 (크기: 1000)

3. **Popular Answer 캐싱**
   - 인기 질문 Top 100 사전 생성
   - 실시간 업데이트 (1일 1회)

```python
# 캐싱 구현 예시
from functools import lru_cache
from cachetools import TTLCache

# Query result cache
query_cache = TTLCache(maxsize=1000, ttl=3600)

# Embedding cache
@lru_cache(maxsize=1000)
def get_cached_embedding(query_hash: str):
    return embedding_client.embed_query(...)
```

### 3. 리랭킹 개선

#### 3-A. 다단계 리랭킹

**현재**: 단일 점수 기반
**개선**: 다단계 필터링

```
Stage 1: Vector Similarity (top 20)
Stage 2: Keyword Match Boost (+entity, +exact phrase)
Stage 3: Quality Score Filter (>= 0.4)
Stage 4: Diversity Filter (중복 제거)
Stage 5: Final Rerank (top 5)
```

#### 3-B. 컨텍스트 기반 리랭킹

- 질문 유형별 가중치 조정
  - 공략 질문: boss_guide 카테고리 부스트
  - 위치 질문: item_location 카테고리 부스트
  - 빌드 질문: build_guide 카테고리 부스트

---

## Implementation Plan

### Phase 1: 스트리밍 응답 (우선순위 높음)

**목표**: 체감 응답 속도 즉시 개선

| Task | Files | Estimate |
|------|-------|:--------:|
| 스트리밍 엔드포인트 추가 | `ask.py` | 2h |
| Frontend SSE 처리 | `useChat.ts` | 2h |
| 에러 핸들링 | `pipeline.py` | 1h |

### Phase 2: 프롬프트 최적화

**목표**: 답변 품질 및 구조 개선

| Task | Files | Estimate |
|------|-------|:--------:|
| 시스템 프롬프트 개선 | `prompt.py` | 2h |
| 신뢰도 등급 시스템 | `reranker.py` | 2h |
| 답변 구조화 템플릿 | `prompt.py` | 1h |

### Phase 3: 캐싱 시스템

**목표**: 반복 쿼리 응답 속도 최적화

| Task | Files | Estimate |
|------|-------|:--------:|
| Query 캐시 구현 | `pipeline.py` | 2h |
| Embedding 캐시 | `embeddings.py` | 1h |
| 캐시 무효화 로직 | `pipeline.py` | 1h |

### Phase 4: 리랭킹 개선

**목표**: 검색 정확도 향상

| Task | Files | Estimate |
|------|-------|:--------:|
| 다단계 리랭킹 | `reranker.py` | 3h |
| 카테고리 부스트 | `reranker.py` | 2h |
| A/B 테스트 설정 | `pipeline.py` | 2h |

---

## Success Criteria

### 정량적 목표

| Metric | Current | Target |
|--------|:-------:|:------:|
| 평균 응답 시간 | ~3초 | **< 2초** |
| 첫 토큰 시간 | ~3초 | **< 1초** |
| 환각률 (추정) | 10-15% | **< 5%** |
| 사용자 만족도 | - | 측정 필요 |

### 정성적 목표

- [ ] 스트리밍 응답 구현
- [ ] 답변에 명확한 출처 표시
- [ ] 불확실한 정보 명시
- [ ] 캐싱으로 반복 쿼리 즉시 응답

---

## Technical Specifications

### 의존성

| Package | Version | Purpose |
|---------|---------|---------|
| `cachetools` | ^5.3 | TTL 캐시 |
| `sse-starlette` | ^1.6 | SSE 스트리밍 |

### API 변경

```python
# 새 엔드포인트
POST /api/v1/ask/stream  # 스트리밍 응답
GET /api/v1/ask/cached   # 캐시된 인기 질문

# 응답 형식 변경
{
    "answer": "...",
    "confidence": "high|medium|low",  # 신규
    "sources": [...],
    "cached": false,  # 신규
    "latency_ms": 1200
}
```

### 환경 설정

```bash
# .env 추가
CACHE_TTL_SECONDS=3600
CACHE_MAX_SIZE=1000
STREAMING_ENABLED=true
```

---

## Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|:------:|:-----------:|------------|
| 스트리밍 에러 핸들링 복잡 | Medium | Medium | 폴백 동기 모드 준비 |
| 캐시 무효화 누락 | Low | Low | TTL 기반 자동 만료 |
| 프롬프트 변경으로 품질 저하 | Medium | Low | A/B 테스트 후 적용 |
| 병렬 처리로 인한 버그 | Medium | Medium | 단계적 적용 |

---

## Timeline

```
Week 1:
├── Phase 1: 스트리밍 응답 구현
└── 테스트 및 프론트엔드 연동

Week 2:
├── Phase 2: 프롬프트 최적화
└── Phase 3: 캐싱 시스템

Week 3:
├── Phase 4: 리랭킹 개선
└── 전체 통합 테스트 및 배포
```

---

## Next Steps

1. `/pdca design answer-optimization` - 상세 설계 문서 작성
2. 스트리밍 프로토타입 구현
3. 성능 베이스라인 측정

---

## Document Info

| Item | Value |
|------|-------|
| Version | 1.0 |
| Created | 2026-02-24 |
| Author | Claude (AI) |
| Status | Planning |
| Next Step | `/pdca design answer-optimization` |
