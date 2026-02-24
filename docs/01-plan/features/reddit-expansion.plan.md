# Plan: Reddit 데이터 수집 확장

> Reddit 다중 서브레딧 + 공통 서브레딧 + 기존 데이터 확장을 통한 대규모 데이터 수집

## 1. Overview

| Item | Value |
|------|-------|
| Feature ID | reddit-expansion |
| Priority | High |
| Status | Plan |
| Created | 2026-02-24 |

### 1.1 Background

이전 PDCA 사이클(remaining-games-data)에서 **32,003 chunks**를 수집했으나:
- Reddit 데이터는 **322개** posts만 수집 (Wiki 중심 수집이었음)
- 게임당 평균 **46개** Reddit posts로 커뮤니티 팁/토론 데이터 부족
- 새로 구현한 다중 서브레딧 지원 + 공통 서브레딧 기능 미적용 상태

### 1.2 Goals

| 목표 | 현재 | 목표 | 예상 증가 |
|------|:----:|:----:|:---------:|
| Reddit Posts | 322 | **1,800+** | **5.6배** |
| Reddit Chunks | ~1,000 | **6,000+** | **6배** |
| 총 Chunks | 32,003 | **37,000+** | **+15%** |

---

## 2. Current State

### 2.1 기존 데이터 (remaining-games-data 완료 기준)

| Game | Reddit Posts | Wiki Pages | Total Chunks |
|------|:------------:|:----------:|:------------:|
| Elden Ring | 41 | 349 | 12,046 |
| Dark Souls 3 | 23 | 229 | 7,752 |
| Sekiro | 28 | 208 | 3,610 |
| Dark Souls 2 | 41 | 249 | 4,764 |
| Lies of P | 37 | 247 | 2,045 |
| Hollow Knight | 76 | 502 | 1,753 |
| Silksong | 76 | 0 | 33 |
| **Total** | **322** | **1,784** | **32,003** |

### 2.2 새로 구현된 기능 (dda7852)

1. **다중 서브레딧 지원** - `subreddits: list[str]`
2. **공통 서브레딧 자동 분류** - `crawl_common_subreddit()`
3. **제목 기반 게임 감지** - `detect_game_from_title()`
4. **수집량 증가** - 200 → 500 posts/game

---

## 3. Collection Strategy

### 3.1 게임별 서브레딧 (기존 + 신규)

| Game | 서브레딧 | Limit | 예상 Posts |
|------|----------|:-----:|:----------:|
| **Elden Ring** | r/Eldenring, r/eldenringdiscussion, r/EldenRingLoreTalk | 500 | ~400 |
| **Dark Souls 3** | r/darksouls3 | 500 | ~150 |
| **Dark Souls 2** | r/DarkSouls2 | 500 | ~100 |
| **Dark Souls** | r/darksouls, r/darksoulsremastered | 500 | ~150 |
| **Sekiro** | r/Sekiro | 500 | ~100 |
| **Lies of P** | r/LiesOfP | 500 | ~80 |
| **Hollow Knight** | r/HollowKnight, r/HollowKnightdaily, r/HollowKnightArt, r/ASilksong | 500 | ~350 |

### 3.2 공통 서브레딧 (NEW)

| 서브레딧 | Limit | 예상 Posts | 특징 |
|----------|:-----:|:----------:|------|
| r/fromsoftware | 300 | ~200 | FromSoftware 공식 커뮤니티 |
| r/soulslike | 300 | ~150 | 장르 전체 토론 |
| r/shittydarksouls | 300 | ~150 | 밈/유머 (의외로 팁 많음) |

### 3.3 수집 필터

| 필터 | 값 | 목적 |
|------|:--:|------|
| min_upvotes | 10 | 품질 보장 |
| min_content_length | 50자 | 너무 짧은 글 제외 |
| quality_score | ≥0.3 | 스팸/저품질 필터 |
| flair 보너스 | Guide, Tips, Help | 가이드 콘텐츠 우선 |

---

## 4. Implementation Plan

### Phase 1: 게임별 서브레딧 크롤링 (기존 데이터 확장)

```bash
# 모든 게임 Reddit 수집 (Wiki 스킵)
python crawl_remaining_games.py --games all --skip-wiki
```

**예상 결과:**
- 7개 게임 × 500 posts = 최대 3,500 posts
- 필터 후 예상: ~1,300 posts
- Chunks: ~4,500 (post당 ~3.5 chunks)

### Phase 2: 공통 서브레딧 크롤링 (NEW)

```bash
# 공통 서브레딧만 크롤링
python crawl_remaining_games.py --common-only
```

**예상 결과:**
- 3개 서브레딧 × 300 posts = 900 posts
- 게임 분류 후: ~500 posts (분류 실패 제외)
- Chunks: ~1,750

### Phase 3: 데이터 검증

1. 게임별 chunk 수 확인
2. RAG 검색 품질 테스트
3. 중복 제거 검증 (source_url 기준 upsert)

---

## 5. Expected Results

### 5.1 수집량 예상

| Source | Posts | Chunks |
|--------|:-----:|:------:|
| 게임별 서브레딧 (신규) | ~1,300 | ~4,500 |
| 공통 서브레딧 (신규) | ~500 | ~1,750 |
| **신규 총합** | **~1,800** | **~6,250** |
| 기존 Wiki + Reddit | - | 32,003 |
| **최종 총합** | - | **~38,250** |

### 5.2 게임별 예상 분포

| Game | 기존 Chunks | 추가 예상 | 최종 예상 |
|------|:-----------:|:---------:|:---------:|
| Elden Ring | 12,046 | +1,400 | ~13,450 |
| Dark Souls 3 | 7,752 | +700 | ~8,450 |
| Dark Souls 2 | 4,764 | +400 | ~5,160 |
| Dark Souls | 0 | +600 | ~600 |
| Sekiro | 3,610 | +400 | ~4,010 |
| Lies of P | 2,045 | +300 | ~2,345 |
| Hollow Knight | 1,786 | +1,200 | ~2,990 |
| **Total** | 32,003 | +5,000~6,500 | **~37,000~38,500** |

---

## 6. Execution Commands

### 6.1 전체 실행 (권장)

```bash
cd crawler

# Step 1: 게임별 Reddit 수집 (Wiki 스킵)
python crawl_remaining_games.py --games all --skip-wiki

# Step 2: 공통 서브레딧 수집
python crawl_remaining_games.py --common-only
```

### 6.2 개별 게임 실행 (선택)

```bash
# 특정 게임만
python crawl_remaining_games.py --games elden-ring dark-souls-3 --skip-wiki

# Dark Souls 1 (신규 게임)
python crawl_remaining_games.py --games dark-souls --skip-wiki
```

### 6.3 전체 한 번에 (게임별 + 공통)

```bash
python crawl_remaining_games.py --games all --skip-wiki --include-common
```

---

## 7. Risk & Mitigation

| Risk | Impact | Mitigation |
|------|:------:|------------|
| Rate Limit (429) | High | 6초 딜레이 적용 완료 |
| 중복 데이터 | Low | source_url 기반 upsert |
| 품질 저하 | Medium | quality_score ≥0.3 필터 |
| 분류 실패 (공통) | Medium | 미분류 데이터는 제외 |

---

## 8. Success Criteria

| Metric | Target | Measurement |
|--------|:------:|-------------|
| 신규 Reddit Posts | ≥1,500 | DB 쿼리 |
| 신규 Chunks | ≥5,000 | DB 쿼리 |
| 총 Chunks | ≥37,000 | DB 쿼리 |
| RAG 품질 유지 | Pass | 검색 테스트 |
| 오류율 | <5% | 크롤링 로그 |

---

## 9. Timeline

| Phase | Duration | Task |
|-------|:--------:|------|
| Phase 1 | ~3시간 | 게임별 Reddit 크롤링 |
| Phase 2 | ~1시간 | 공통 서브레딧 크롤링 |
| Phase 3 | ~30분 | 데이터 검증 |
| **Total** | **~4.5시간** | |

> Note: Rate limit (6초/요청) 으로 인해 시간이 필요합니다.

---

## 10. Dependencies

| Dependency | Status | Notes |
|------------|:------:|-------|
| config.py 수정 | ✅ | 다중 서브레딧 지원 |
| reddit_json.py 수정 | ✅ | 공통 서브레딧 크롤러 |
| crawl_remaining_games.py 수정 | ✅ | CLI 옵션 추가 |
| Supabase 연결 | ✅ | .env 설정 완료 |
| OpenAI API | ✅ | embedding 생성 |

---

## Document Info

| Item | Value |
|------|-------|
| Version | 1.0 |
| Author | Claude (AI) |
| Created | 2026-02-24 |
| PDCA Phase | Plan |
| Next Step | Do (크롤링 실행) |
