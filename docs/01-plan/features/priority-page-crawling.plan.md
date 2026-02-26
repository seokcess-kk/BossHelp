# Priority Page Crawling - Plan Document

> 주요 보스/무기/NPC 페이지 우선 크롤링 시스템

## Overview

| Item | Value |
|------|-------|
| Feature | priority-page-crawling |
| Created | 2026-02-26 |
| Status | 📋 Planning |
| Priority | 🔴 Critical |

---

## 1. Problem Statement

### 1.1 현재 문제

```
User Query: "말레니아 공략"

Expected: Malenia 보스 페이지의 상세 공략 정보
Actual: "말레니아에 대한 구체적인 전략은 제공된 자료에서 확인하지 못했습니다"
```

### 1.2 근본 원인

| 원인 | 설명 | 영향도 |
|------|------|:------:|
| **페이지 미수집** | Malenia 전용 페이지 (`/Malenia+Blade+of+Miquella`) 미크롤링 | 🔴 Critical |
| 크롤링 전략 부재 | 주요 엔티티 페이지 우선순위 없음 | 🟡 High |
| 검증 부재 | 크롤링 후 필수 페이지 존재 여부 확인 없음 | 🟡 High |

### 1.3 데이터 분석

```
Elden Ring 청크 현황:
- 전체 청크: 47,073개
- Malenia 언급 청크: 861개 (다른 페이지에서 이름만 언급)
- Malenia 전용 페이지 청크: 0개 ❌

문제 범위:
- 주요 보스 40+ 중 전용 페이지 있는 보스: 미확인
- 예상 누락: 대부분의 주요 보스 상세 페이지
```

---

## 2. Goals

### 2.1 Primary Goals

| Goal | Metric | Target |
|------|--------|:------:|
| 주요 보스 페이지 수집 | 보스 전용 페이지 수 | 40+ |
| 공략 정보 품질 | 공략 키워드 포함 청크 | 80%+ |
| 검색 정확도 | 관련 답변 반환율 | 95%+ |

### 2.2 Success Criteria

1. **데이터 완성도**
   - 주요 보스 40개 이상 전용 페이지 크롤링
   - 각 보스당 평균 10+ 청크 (공략, 패턴, 드롭템 등)

2. **검색 품질**
   - "말레니아 공략" → Malenia 전용 페이지 청크 반환
   - 공략 관련 키워드 (phase, dodge, pattern, strategy) 포함

3. **시스템 개선**
   - 필수 페이지 목록 관리 체계
   - 크롤링 완료 후 검증 로직

---

## 3. Proposed Solution

### 3.1 접근 방식

```
┌─────────────────────────────────────────────────────────────┐
│                  Priority Page Crawling                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  [1] 필수 페이지 목록 정의                                   │
│      │                                                       │
│      ├── bosses.json: 40+ 주요 보스 URL                      │
│      ├── weapons.json: 30+ 인기 무기 URL                     │
│      └── npcs.json: 20+ 주요 NPC URL                         │
│                                                              │
│  [2] 우선순위 크롤링 실행                                    │
│      │                                                       │
│      └── crawl_priority_pages.py                             │
│           ├── 필수 페이지 먼저 크롤링                        │
│           ├── 청킹 → 임베딩 → 저장                           │
│           └── 엔티티 태깅 자동 적용                          │
│                                                              │
│  [3] 검증 및 모니터링                                        │
│      │                                                       │
│      └── verify_priority_pages.py                            │
│           ├── 필수 페이지 존재 여부 확인                     │
│           ├── 청크 품질 검사                                 │
│           └── 누락 페이지 리포트                             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 우선순위 페이지 목록 (예시)

**Bosses (Tier 1 - Critical)**
- Malenia Blade of Miquella
- Starscourge Radahn
- Morgott the Omen King
- Godfrey First Elden Lord
- Radagon of the Golden Order
- Elden Beast
- Mohg Lord of Blood
- Maliketh the Black Blade
- Fire Giant
- Rykard Lord of Blasphemy

**Bosses (Tier 2 - High)**
- Margit the Fell Omen
- Godrick the Grafted
- Rennala Queen of the Full Moon
- Astel Naturalborn of the Void
- Placidusax
- Fortissax
- Loretta
- Commander Niall

---

## 4. Implementation Plan

### Phase 1: 필수 페이지 목록 생성 (1단계)

| Task | Description | Output |
|------|-------------|--------|
| 보스 목록 추출 | Wiki Bosses 페이지에서 URL 추출 | `priority_pages/bosses.json` |
| 무기 목록 추출 | 인기 무기 URL 수집 | `priority_pages/weapons.json` |
| NPC 목록 추출 | 주요 NPC URL 수집 | `priority_pages/npcs.json` |

### Phase 2: 크롤링 스크립트 개선 (2단계)

| Task | Description | Output |
|------|-------------|--------|
| 우선순위 크롤러 | 필수 페이지 먼저 크롤링 | `crawl_priority_pages.py` |
| 자동 태깅 | 크롤링 시 entity tagging 자동 적용 | 통합 |
| 중복 체크 | 기존 데이터와 중복 방지 | 통합 |

### Phase 3: 검증 시스템 (3단계)

| Task | Description | Output |
|------|-------------|--------|
| 검증 스크립트 | 필수 페이지 존재 확인 | `verify_priority_pages.py` |
| 품질 리포트 | 청크 품질 분석 | 리포트 생성 |
| 자동 알림 | 누락 페이지 감지 시 알림 | 로깅 |

---

## 5. Risk Assessment

| Risk | Impact | Mitigation |
|------|:------:|------------|
| Wiki 차단 | 🔴 | Rate limiting, User-Agent 설정 |
| 페이지 구조 변경 | 🟡 | 유연한 파서, 에러 핸들링 |
| 대용량 데이터 | 🟢 | 배치 처리, 진행 상황 저장 |

---

## 6. Immediate Action

**긴급 조치**: 기존 `crawl_specific_pages.py` 실행

```bash
cd crawler && python crawl_specific_pages.py
```

이 스크립트에 이미 Malenia 포함 주요 보스 URL이 준비되어 있음.

---

## 7. Next Steps

1. **즉시**: `crawl_specific_pages.py` 실행하여 긴급 데이터 수집
2. **Design**: 상세 설계 문서 작성
3. **Do**: 우선순위 크롤링 시스템 구현
4. **Check**: 검증 및 품질 확인

---

**작성일**: 2026-02-26
**작성 도구**: bkit:pdca
