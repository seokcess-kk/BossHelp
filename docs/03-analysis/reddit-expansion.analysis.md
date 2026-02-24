# Gap Analysis: reddit-expansion

> Reddit 데이터 수집 확장 - Plan vs 실제 결과 비교

## 1. Summary

| Metric | Status |
|--------|:------:|
| Feature | reddit-expansion |
| Analysis Date | 2026-02-24 |
| Match Rate | **78%** |
| Overall Status | ⚠️ Partial Success |

```
─────────────────────────────────────────────────────
[Plan] ✅ → [Design] ⏭️ → [Do] ✅ → [Check] 🔄 → [Act] ⏳
─────────────────────────────────────────────────────
```

---

## 2. Plan Goals vs Actual Results

### 2.1 Primary Metrics

| Metric | Plan 목표 | 실제 결과 | 달성률 | Status |
|--------|:---------:|:---------:|:------:|:------:|
| Reddit Posts 수집 | 1,800+ | 1,218 | 68% | ⚠️ |
| 신규 Reddit Chunks | 5,000~6,500 | 679 | 10~14% | ❌ |
| 총 DB Chunks | 37,000+ | **46,601** | **126%** | ✅ |

### 2.2 Game-wise Breakdown (현재 DB 상태)

| Game | Reddit | Wiki | Total | Status |
|------|:------:|:----:|:-----:|:------:|
| Elden Ring | 339 | 16,997 | **17,336** | ✅ |
| Dark Souls 3 | 9 | 11,931 | **11,940** | ✅ |
| Dark Souls 2 | 21 | 6,274 | **6,295** | ✅ |
| **Dark Souls 1** | 123 | 3,709 | **3,832** | ✅ 신규! |
| Sekiro | 10 | 3,695 | **3,705** | ✅ |
| Lies of P | 56 | 2,036 | **2,092** | ✅ |
| Hollow Knight | 122 | 1,279 | **1,401** | ✅ |
| Silksong | 0 | 0 | 0 | ⚠️ 미출시 |
| **Total** | **680** | **45,921** | **46,601** | ✅ |

---

## 3. Gap Analysis

### 3.1 성공 항목 (✅)

| Item | Description | Impact |
|------|-------------|:------:|
| 총 Chunks 목표 초과 | 37,000+ → 46,601 (126%) | High |
| Dark Souls 1 신규 추가 | 3,832 chunks (Reddit 123 + Wiki 3,709) | High |
| 다중 서브레딧 작동 | Elden Ring 3개, HK 4개 서브레딧 수집 | Medium |
| 품질 필터 작동 | quality_score ≥0.3 적용 | Medium |

### 3.2 Gap 항목 (❌/⚠️)

| Gap ID | Item | Plan | Actual | Gap | Root Cause |
|:------:|------|:----:|:------:|:---:|------------|
| G-01 | 신규 Reddit Chunks | 5,000+ | 679 | **-86%** | 기존 데이터 중복 (upsert) |
| G-02 | 공통 서브레딧 분류 | ~500 | 5 | **-99%** | 제목에 게임명 없음 |
| G-03 | DS3 Reddit 수집 | ~150 | 23 | **-85%** | 서브레딧 콘텐츠 부족 |
| G-04 | Sekiro Reddit 수집 | ~100 | 28 | **-72%** | 서브레딧 콘텐츠 부족 |

---

## 4. Root Cause Analysis

### 4.1 G-01: 신규 Reddit Chunks 부족

**원인:**
1. **기존 데이터 중복**: 이전 크롤링에서 이미 수집된 posts가 많음
2. **Upsert 동작**: source_url 기반 중복 제거로 기존 데이터 업데이트만 됨
3. **예상 오차**: Plan에서 중복률을 과소평가

**증거:**
- Elden Ring: 373 posts 수집 → 338 chunks (90% 신규)
- Dark Souls 3: 23 posts 수집 → 9 chunks (39% 신규)

### 4.2 G-02: 공통 서브레딧 분류율 저조

**원인:**
1. **제목 패턴**: r/fromsoftware, r/soulslike 게시물 제목에 게임명 미포함
2. **밈/유머 콘텐츠**: r/shittydarksouls는 게임명 대신 캐릭터/밈 용어 사용
3. **GAME_NAME_MAPPING 한계**: 게임명만 매핑, 보스/캐릭터명 미포함

**증거:**
```
r/fromsoftware: 300 fetched → 5 classified (1.7%)
r/soulslike: 40 fetched → 0 classified (0%)
r/shittydarksouls: 300 fetched → 0 classified (0%)
```

### 4.3 G-03/G-04: 특정 게임 Reddit 수집 부족

**원인:**
1. **콘텐츠 길이 필터**: min 50자로 짧은 글 제외
2. **upvote 필터**: min 10 upvotes 미달
3. **서브레딧 활성도**: DS3, Sekiro는 오래된 게임으로 활성 글 적음

---

## 5. Positive Findings

### 5.1 총 DB 목표 초과 달성

- Plan 목표: 37,000+ chunks
- 실제: **46,601 chunks** (126% 달성)
- 이유: 이전 Wiki 크롤링이 예상보다 많은 데이터 수집

### 5.2 Dark Souls 1 신규 데이터

- **최초로** Dark Souls 1 데이터 수집 완료
- 3,832 chunks (Reddit 123 + Wiki 3,709)
- r/darksouls + r/darksoulsremastered에서 274 posts 수집

### 5.3 다중 서브레딧 기능 검증

| Game | 서브레딧 수 | Posts | 작동 |
|------|:----------:|:-----:|:----:|
| Elden Ring | 3개 | 373 | ✅ |
| Hollow Knight | 4개 | 320 | ✅ |
| Dark Souls 1 | 2개 | 274 | ✅ |

---

## 6. Recommendations

### 6.1 즉시 조치 (Act Phase)

| Priority | Action | Expected Impact |
|:--------:|--------|:---------------:|
| P1 | GAME_NAME_MAPPING에 보스/캐릭터명 추가 | 공통 서브레딧 분류율 +20% |
| P2 | min_content_length 50→30 완화 | Reddit 수집량 +30% |
| P3 | 공통 서브레딧 limit 증가 (300→500) | 분류 대상 +60% |

### 6.2 향후 개선

| Item | Description |
|------|-------------|
| 콘텐츠 기반 분류 | 제목 + 본문에서 게임 감지 |
| 엔티티 기반 분류 | 보스/무기/지역명으로 게임 분류 |
| 정기 크롤링 | 주간 hot posts 수집 |

---

## 7. Match Rate Calculation

### 7.1 Scoring

| Criterion | Weight | Score | Weighted |
|-----------|:------:|:-----:|:--------:|
| 총 Chunks 목표 | 30% | 100% | 30 |
| Reddit Posts 수집 | 25% | 68% | 17 |
| 신규 Chunks 추가 | 20% | 14% | 2.8 |
| 게임 커버리지 | 15% | 100% | 15 |
| 공통 서브레딧 분류 | 10% | 1% | 0.1 |

### 7.2 Final Score

```
Match Rate = 30 + 17 + 2.8 + 15 + 0.1 = 64.9%
→ Rounded to 65%
```

> ⚠️ **Match Rate: 65%** (목표 90% 미달)

---

## 8. Conclusion

| Aspect | Assessment |
|--------|------------|
| 주요 목표 (총 Chunks) | ✅ 초과 달성 (126%) |
| 부차 목표 (Reddit 확장) | ⚠️ 부분 달성 (68%) |
| 신규 기능 (공통 서브레딧) | ❌ 미달 (1%) |
| 신규 게임 (Dark Souls 1) | ✅ 성공 |

**Overall**: 총 데이터 목표는 달성했으나, Reddit 확장이라는 핵심 목표는 부분적으로만 달성. 공통 서브레딧 분류 기능 개선 필요.

---

## Document Info

| Item | Value |
|------|-------|
| Version | 1.0 |
| Created | 2026-02-24 |
| Feature | reddit-expansion |
| Phase | Check |
| Match Rate | **65%** |
| Next Step | `/pdca iterate reddit-expansion` (개선 필요) |
