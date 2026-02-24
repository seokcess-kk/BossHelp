# Remaining Games Data Collection Plan

## Overview

| Item | Value |
|------|-------|
| Feature | remaining-games-data |
| Phase | Plan |
| Created | 2026-02-23 |
| Status | Planning |

## Background

BossHelp는 현재 다음 게임들을 지원합니다:

| Game | ID | Wiki URL | 데이터 상태 |
|------|-----|----------|------------|
| Elden Ring | `elden-ring` | eldenring.wiki.fextralife.com | 미수집 |
| Sekiro | `sekiro` | sekiroshadowsdietwice.wiki.fextralife.com | 미수집 |
| Hollow Knight | `hollow-knight` | hollowknight.wiki.fextralife.com | 미수집 |
| Silksong | `silksong` | (미출시) | N/A |
| Lies of P | `lies-of-p` | liesofp.wiki.fextralife.com | 미수집 |
| Dark Souls | `dark-souls` | darksouls.wiki.fextralife.com | 수집 완료 |
| Dark Souls 2 | `dark-souls-2` | darksouls2.wiki.fextralife.com | 미수집 |
| Dark Souls 3 | `dark-souls-3` | darksouls3.wiki.fextralife.com | 미수집 |

Dark Souls는 데이터 수집이 완료되었으나, 나머지 7개 게임은 Wiki 데이터 수집이 필요합니다.

## Goals

1. **Primary**: 6개 핵심 게임의 **Wiki + Reddit** 데이터 수집 (Elden Ring, Sekiro, Hollow Knight, Lies of P, DS2, DS3)
2. **Secondary**: Silksong 관련 정보 수집 (출시 전이므로 Reddit만)

## Data Sources

### 1. Wiki (Fextralife)
- 보스 공략, 무기/방어구, 아이템, 지역 정보
- 정적이고 체계적인 정보

### 2. Reddit JSON API (인증 불필요)
- 커뮤니티 팁, 빌드 가이드, 토론
- 동적이고 실전적인 정보
- **크롤러**: `crawler/crawlers/reddit_json.py` (구현 완료)
- **Rate Limit**: 6초 간격 (분당 10개)

### 크롤링 방식
```bash
# Dark Souls와 동일한 방식 사용
python crawl_dark_souls_json.py  # 이 스크립트를 각 게임별로 적용
```

## Target Games (Priority Order)

### Priority 1: High Traffic Games

| 순위 | Game | 예상 Pages | 이유 |
|:----:|------|:----------:|------|
| 1 | Elden Ring | 1,500+ | 가장 인기 있는 소울라이크, 트래픽 높음 |
| 2 | Dark Souls 3 | 1,200+ | 소울라이크 입문작으로 인기 |

### Priority 2: Core Soulslike

| 순위 | Game | 예상 Pages | 이유 |
|:----:|------|:----------:|------|
| 3 | Sekiro | 800+ | FromSoftware 작품, 독특한 전투 시스템 |
| 4 | Dark Souls 2 | 1,000+ | 시리즈 완성을 위해 필요 |
| 5 | Lies of P | 600+ | 최신 소울라이크, 성장 중 |

### Priority 3: Metroidvania

| 순위 | Game | 예상 Pages | 이유 |
|:----:|------|:----------:|------|
| 6 | Hollow Knight | 1,000+ | 메트로바니아 대표작 |
| 7 | Silksong | N/A | 미출시 - News/Preview만 |

---

## Implementation Phases

### Phase 1: Elden Ring (최우선)

**목표**: Elden Ring Wiki + Reddit 데이터 완전 수집

**작업 내용**:

#### 1-A. Reddit JSON 수집
```bash
# RedditJsonCrawler 사용 (인증 불필요)
# r/Eldenring top 200 posts
```
- Subreddit: `r/Eldenring`
- Flairs: Guide, Tips/Hints, Help, Strategy
- Min upvotes: 10
- 예상: 150-200 posts → 300+ chunks

#### 1-B. Wiki 수집
- Bosses (주요 보스, 필드 보스) - ~150 pages
- Weapons (무기) - ~300 pages
- Armor (방어구) - ~200 pages
- Talismans (탈리스만) - ~100 pages
- Locations (지역) - ~100 pages
- NPCs (NPC 퀘스트) - ~50 pages
- Magic (주문/기도) - ~150 pages
- Items (소모품/재료) - ~300 pages
- 예상: 1,350 pages → 3,500+ chunks

#### 1-C. 데이터 처리
- HTML → 마크다운 변환
- 청킹 (500 tokens, 100 overlap)
- 품질 점수 계산
- 임베딩 생성

**예상 결과**: 4,000+ chunks (Reddit 300 + Wiki 3,700)

### Phase 2: Dark Souls 3

**목표**: Dark Souls 3 Wiki + Reddit 데이터 수집

**작업 내용**:

#### 2-A. Reddit JSON 수집
- Subreddit: `r/darksouls3`
- Flairs: Help, Co-op, Build, PVP, Lore
- 예상: 150-200 posts → 300+ chunks

#### 2-B. Wiki 수집
- Bosses - ~100 pages
- Weapons - ~250 pages
- Armor - ~150 pages
- Rings - ~100 pages
- Locations - ~50 pages
- NPCs - ~50 pages
- Spells - ~150 pages
- Items - ~200 pages
- 예상: 1,050 pages → 2,700+ chunks

**예상 결과**: 3,000+ chunks (Reddit 300 + Wiki 2,700)

### Phase 3: Sekiro

**목표**: Sekiro Wiki + Reddit 데이터 수집

#### 3-A. Reddit JSON 수집
- Subreddit: `r/Sekiro`
- Flairs: Guide, Tips, Help
- 예상: 100-150 posts → 200+ chunks

#### 3-B. Wiki 수집
- Bosses - ~40 pages
- Prosthetic Tools - ~20 pages
- Combat Arts - ~30 pages
- Items - ~100 pages
- Locations - ~40 pages
- Skills - ~50 pages
- NPCs - ~30 pages
- 예상: 310 pages → 1,300+ chunks

**예상 결과**: 1,500+ chunks (Reddit 200 + Wiki 1,300)

### Phase 4: Dark Souls 2

**목표**: Dark Souls 2 Wiki + Reddit 데이터 수집

#### 4-A. Reddit JSON 수집
- Subreddit: `r/DarkSouls2`
- Flairs: Help, Co-op, Build, Lore
- 예상: 150-200 posts → 300+ chunks

#### 4-B. Wiki 수집
- Bosses - ~80 pages
- Weapons - ~250 pages
- Armor - ~150 pages
- Rings - ~100 pages
- Spells - ~150 pages
- Items - ~200 pages
- 예상: 930 pages → 2,200+ chunks

**예상 결과**: 2,500+ chunks (Reddit 300 + Wiki 2,200)

### Phase 5: Lies of P

**목표**: Lies of P Wiki + Reddit 데이터 수집

#### 5-A. Reddit JSON 수집
- Subreddit: `r/LiesOfP`
- Flairs: Guide, Tips, Help, Build
- 예상: 100-150 posts → 200+ chunks

#### 5-B. Wiki 수집
- Bosses - ~30 pages
- Weapons - ~100 pages
- Legion Arms - ~15 pages
- Amulets - ~30 pages
- Items - ~100 pages
- Locations - ~30 pages
- 예상: 305 pages → 1,300+ chunks

**예상 결과**: 1,500+ chunks (Reddit 200 + Wiki 1,300)

### Phase 6: Hollow Knight

**목표**: Hollow Knight Wiki + Reddit 데이터 수집

#### 6-A. Reddit JSON 수집
- Subreddit: `r/HollowKnight`
- Flairs: Guide, Tips & Tricks, Help
- 예상: 150-200 posts → 300+ chunks

#### 6-B. Wiki 수집
- Bosses - ~50 pages
- Charms - ~50 pages
- Items/Relics - ~50 pages
- Areas - ~30 pages
- NPCs - ~60 pages
- Enemies - ~150 pages
- 예상: 390 pages → 1,700+ chunks

**예상 결과**: 2,000+ chunks (Reddit 300 + Wiki 1,700)

### Phase 7: Silksong (Optional)

**목표**: Silksong 관련 정보 수집 (미출시 게임)

#### 7-A. Reddit JSON 수집만
- Subreddit: `r/HollowKnight` (Silksong flair)
- Flairs: Silksong, News
- Min upvotes: 5 (낮춤)
- Wiki: 미출시로 불가

**예상 결과**: 100-200 chunks (Reddit News/Preview 위주)

---

## Technical Specifications

### Wiki Crawler Configuration

각 게임별 Wiki 구조가 다르므로 설정 조정 필요:

```python
# crawler/crawlers/wiki.py

WIKI_CONFIGS = {
    "elden-ring": {
        "base_url": "https://eldenring.wiki.fextralife.com",
        "categories": {
            "bosses": "/Bosses",
            "weapons": "/Weapons",
            "armor": "/Armor",
            "talismans": "/Talismans",
            "locations": "/Locations",
            "npcs": "/NPCs",
            "spells": "/Sorceries",
            "incantations": "/Incantations",
        },
        "selectors": {
            "content": ".wiki-content-block",
            "title": "h1.page-title",
            "links": ".wiki-content a[href]",
        }
    },
    "dark-souls-3": {
        "base_url": "https://darksouls3.wiki.fextralife.com",
        "categories": {
            "bosses": "/Bosses",
            "weapons": "/Weapons",
            "armor": "/Armor",
            "rings": "/Rings",
            "spells": "/Magic",
        },
        # ... similar structure
    },
    # ... other games
}
```

### Entity Dictionary Updates

각 게임별 entity_dictionary.py 업데이트 필요:

```python
# backend/app/core/entity/dictionary.py

GAME_ENTITIES = {
    "elden-ring": {
        "bosses": ["Malenia", "Radahn", "Morgott", "Godfrey", ...],
        "locations": ["Limgrave", "Liurnia", "Caelid", "Altus Plateau", ...],
        "npcs": ["Melina", "Ranni", "Blaidd", "Iji", ...],
    },
    "sekiro": {
        "bosses": ["Genichiro", "Isshin", "Lady Butterfly", "Guardian Ape", ...],
        "prosthetics": ["Shuriken", "Loaded Spear", "Flame Vent", ...],
    },
    # ... other games
}
```

---

## Resource Estimation

### API Calls

| Resource | Estimate | Cost |
|----------|:--------:|:----:|
| Reddit JSON | ~1,000 posts | Free (인증 불필요) |
| Wiki Pages | ~4,300 pages | Free |
| OpenAI Embeddings | ~16,000 chunks | ~$1.5-2 |

### Rate Limits

| Source | Delay | 분당 요청 |
|--------|:-----:|:--------:|
| Reddit JSON | 6초 | ~10 |
| Wiki | 1.5초 | ~40 |

### Storage

| Item | Estimate |
|------|:--------:|
| Raw HTML | ~500 MB |
| Processed Text | ~100 MB |
| Vectors (pgvector) | ~200 MB |
| Total DB Growth | ~300 MB |

### Time Estimate

| Phase | Game | 예상 소요 |
|:-----:|------|:--------:|
| 1 | Elden Ring | 3-4시간 |
| 2 | Dark Souls 3 | 2-3시간 |
| 3 | Sekiro | 1-2시간 |
| 4 | Dark Souls 2 | 2-3시간 |
| 5 | Lies of P | 1-2시간 |
| 6 | Hollow Knight | 2-3시간 |
| 7 | Silksong | 30분 |
| **Total** | | **12-18시간** |

---

## Success Criteria

| Game | Reddit | Wiki | Total Chunks |
|------|:------:|:----:|:------------:|
| Elden Ring | 300+ | 3,700+ | 4,000+ |
| Dark Souls 3 | 300+ | 2,700+ | 3,000+ |
| Sekiro | 200+ | 1,300+ | 1,500+ |
| Dark Souls 2 | 300+ | 2,200+ | 2,500+ |
| Lies of P | 200+ | 1,300+ | 1,500+ |
| Hollow Knight | 300+ | 1,700+ | 2,000+ |
| Silksong | 100+ | N/A | 100+ |
| **Total** | **1,700+** | **12,900+** | **14,600+** |

**검증 기준**:
- [x] 각 게임별 Reddit + Wiki 데이터 수집 완료 (2026-02-23)
- [ ] 각 게임별 RAG 검색 테스트 통과
- [x] 총 chunks: 31,061개 (목표 15,000+ 달성)

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Wiki 구조 변경 | Medium | 게임별 selector 분리, fallback 로직 |
| Rate Limiting | Low | 1.5초 딜레이 준수 |
| 크롤링 차단 | Medium | User-Agent 설정, 딜레이 증가 |
| 임베딩 비용 | Low | 배치 처리, 중복 체크 |
| 데이터 품질 | Medium | 품질 필터링 강화 |

---

## Execution Order

```
Day 1:
├── Phase 1: Elden Ring Wiki 크롤링
└── 데이터 검증 & 테스트

Day 2:
├── Phase 2: Dark Souls 3 Wiki 크롤링
├── Phase 3: Sekiro Wiki 크롤링
└── 데이터 검증

Day 3:
├── Phase 4: Dark Souls 2 Wiki 크롤링
├── Phase 5: Lies of P Wiki 크롤링
└── 데이터 검증

Day 4:
├── Phase 6: Hollow Knight Wiki 크롤링
├── Phase 7: Silksong (Optional)
├── 전체 데이터 검증
└── RAG 통합 테스트
```

---

## Prerequisites

1. **Wiki Crawler 검증**
   - Dark Souls 크롤링으로 검증 완료
   - 각 게임별 selector 테스트 필요

2. **환경변수 확인**
   ```bash
   SUPABASE_URL=xxx
   SUPABASE_SERVICE_KEY=xxx
   OPENAI_API_KEY=xxx
   ```

3. **Storage 여유 공간**
   - 최소 1GB 여유 공간 필요

---

## Next Steps

1. `/pdca design remaining-games-data` - 상세 설계 문서 작성
2. Elden Ring Wiki 구조 분석 및 테스트 크롤링
3. 크롤러 설정 파일 업데이트

---

## Document Info

| Item | Value |
|------|-------|
| Version | 1.0 |
| Created | 2026-02-23 |
| Author | Claude (AI) |
| Status | Planning |
| Next Step | `/pdca design remaining-games-data` |
