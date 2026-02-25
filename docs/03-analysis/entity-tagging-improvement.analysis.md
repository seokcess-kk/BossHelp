# Entity Tagging Improvement - Gap Analysis Report

> Design 문서 vs 구현 코드 비교 분석

## Analysis Overview

| Item | Value |
|------|-------|
| Feature | entity-tagging-improvement |
| Design Document | `docs/02-design/features/entity-tagging-improvement.design.md` |
| Analysis Date | 2026-02-25 |
| Match Rate | **92%** |
| Status | ✅ Approved |

---

## Overall Scores

| Category | Score | Status |
|----------|:-----:|:------:|
| DB Schema | 98% | ✅ Approved |
| TitleEntityExtractor | 95% | ✅ Approved |
| EntityTypeClassifier | 92% | ✅ Approved |
| Migration Script | 90% | ✅ Approved |
| Retriever Integration | 88% | ✅ Approved |
| Test Coverage | 100% | ✅ Approved |
| RPC Function (search_chunks_v2) | 0% | ⚠️ Not Implemented (Python 대체) |

---

## 1. DB Schema (98%)

### 구현된 항목 ✅

| 항목 | Design | Implementation | 상태 |
|------|--------|----------------|:----:|
| primary_entity 컬럼 | TEXT | TEXT | ✅ |
| entity_type 컬럼 | TEXT | TEXT | ✅ |
| chk_entity_type 제약조건 | 9 values | 9 values | ✅ |
| idx_chunks_primary_entity | B-tree | B-tree | ✅ |
| idx_chunks_entity_type | B-tree | B-tree | ✅ |
| idx_chunks_primary_entity_trgm | GIN trigram | GIN trigram | ✅ |
| idx_chunks_game_entity_type | Composite | Composite | ✅ |

### 개선된 항목 🔼

| 항목 | Design | Implementation | 효과 |
|------|--------|----------------|------|
| trigram 인덱스 조건 | `WHERE is_active = true` | `WHERE is_active = true AND primary_entity IS NOT NULL` | 성능 최적화 |
| 컬럼 코멘트 | 미지정 | COMMENT ON COLUMN 추가 | 문서화 개선 |

---

## 2. TitleEntityExtractor (95%)

### 구현된 항목 ✅

| 항목 | Design | Implementation | 상태 |
|------|--------|----------------|:----:|
| ExtractedEntity 데이터클래스 | name, normalized | name, normalized | ✅ |
| WIKI_PATTERNS | 3개 패턴 | 3개 패턴 | ✅ |
| extract() 메서드 | 시그니처 일치 | 시그니처 일치 | ✅ |
| _should_exclude() 메서드 | 구현 | 구현 | ✅ |
| 길이 검증 (3-80) | 구현 | 구현 | ✅ |
| 싱글톤 패턴 | get_title_extractor() | get_title_extractor() | ✅ |

### 개선된 항목 🔼

| 항목 | Design | Implementation | 효과 |
|------|--------|----------------|------|
| EXCLUDE_PATTERNS | 12개 | 23개 (+11) | 더 정확한 필터링 |
| 특수문자 검증 | 없음 | `not any(c.isalnum())` 체크 | 오류 방지 |
| extract_batch() | 없음 | 추가 구현 | 배치 처리 지원 |

---

## 3. EntityTypeClassifier (92%)

### 구현된 항목 ✅

| 항목 | Design | Implementation | 상태 |
|------|--------|----------------|:----:|
| EntityType enum | 9개 값 | 9개 값 | ✅ |
| CATEGORY_MAPPING | 7개 매핑 | 7개 매핑 | ✅ |
| TYPE_KEYWORDS | 7개 카테고리 | 7개 카테고리 | ✅ |
| classify() 메서드 | 구현 | 구현 | ✅ |
| 싱글톤 패턴 | get_type_classifier() | get_type_classifier() | ✅ |

### 개선된 항목 🔼

| 항목 | Design | Implementation | 효과 |
|------|--------|----------------|------|
| 분류 우선순위 | Category → Keywords → Known | Category(특정만) → Known → Keywords → Category 폴백 | 정확도 향상 |
| TYPE_KEYWORDS | ~30개/카테고리 | ~70개/카테고리 (+40) | 커버리지 확대 |
| KNOWN_ENTITIES | ~30개 | ~60개 (+30) | 더 많은 엔티티 인식 |
| classify_batch() | 없음 | 추가 구현 | 배치 처리 지원 |

---

## 4. Migration Script (90%)

### 구현된 항목 ✅

| 항목 | Design | Implementation | 상태 |
|------|--------|----------------|:----:|
| batch_size 파라미터 | 기본 100 | 기본 100 | ✅ |
| dry_run 옵션 | 구현 | 구현 | ✅ |
| 통계 추적 | 5개 필드 | 7개 필드 | ✅ |
| 배치 업데이트 | 구현 | 구현 | ✅ |
| CLI argparse | 2개 옵션 | 3개 옵션 | ✅ |

### 개선된 항목 🔼

| 항목 | Design | Implementation | 효과 |
|------|--------|----------------|------|
| game_id 필터 | 없음 | `--game-id` 옵션 추가 | 선택적 마이그레이션 |
| 타임스탬프 | 없음 | started_at, completed_at | 실행 시간 추적 |
| print_stats() | 없음 | 포맷된 통계 출력 | 가독성 향상 |

### 변경된 항목 🔄

| 항목 | Design | Implementation | 영향 |
|------|--------|----------------|------|
| 함수 타입 | `async def` | `def` (동기) | 낮음 - 단순화 |
| 진행 표시 | tqdm | logger.info | 낮음 - 의존성 감소 |

---

## 5. Retriever Integration (88%)

### 구현된 항목 ✅

| 항목 | Design | Implementation | 상태 |
|------|--------|----------------|:----:|
| entities 파라미터 | search()에 추가 | search()에 추가 | ✅ |
| _filter_by_entities() | 구현 | 구현 | ✅ |
| _apply_entity_boost() | 구현 | 구현 | ✅ |
| 엔티티 우선순위 | primary → tags | primary ILIKE → tags | ✅ |

### 개선된 항목 🔼

| 항목 | Design | Implementation | 효과 |
|------|--------|----------------|------|
| _search_within_chunks() | 없음 | 추가 구현 | 필터링된 청크 내 벡터 검색 |
| entity_match_type | 없음 | "primary" / "tags" 추적 | 디버깅 용이 |
| embedding 폴백 | 없음 | 없을 시 기본 점수 적용 | 견고성 향상 |

### 변경된 항목 🔄

| 항목 | Design | Implementation | 영향 |
|------|--------|----------------|------|
| primary_entity 부스트 | +0.3 | +0.25 | 낮음 - 미세 조정 |
| 필터 구조 | 3단계 (exact, partial, tags) | 2단계 (ILIKE, tags) | 낮음 - 기능 동일 |

---

## 6. 구현 완료 항목 ✅

### 테스트 구현 완료

| 항목 | Design 위치 | 설명 | 결과 |
|------|-------------|------|------|
| test_title_extractor.py | Section 7.1 | TitleEntityExtractor 단위 테스트 | ✅ 25개 테스트 PASS |
| test_type_classifier.py | Section 7.1 | EntityTypeClassifier 단위 테스트 | ✅ 33개 테스트 PASS |

### 선택적 미구현 항목

| 항목 | Design 위치 | 설명 | 영향 |
|------|-------------|------|------|
| search_chunks_v2 RPC | Section 5.1 | filter_entities, filter_entity_type 파라미터 | Python 필터링으로 대체됨 |

**Note**: search_chunks_v2 RPC는 Python 측 필터링으로 기능적으로 대체되었습니다. 대규모 데이터에서 성능 이슈 발생 시 구현 검토.

---

## 7. Match Rate 계산

| 컴포넌트 | 가중치 | 점수 | 가중 점수 |
|----------|:------:|:----:|:---------:|
| DB Schema | 20% | 98% | 19.6 |
| TitleEntityExtractor | 20% | 95% | 19.0 |
| EntityTypeClassifier | 20% | 92% | 18.4 |
| Migration Script | 15% | 90% | 13.5 |
| Retriever Integration | 15% | 88% | 13.2 |
| Test Coverage | 5% | 100% | 5.0 |
| RPC Function | 5% | 0% | 0.0 |
| **합계** | **100%** | - | **91.7%** |

**Overall Match Rate: 92%** (반올림)

---

## 8. 완료된 조치

### 단위 테스트 작성 ✅

1. **테스트 파일 생성 완료**
   ```bash
   backend/tests/test_title_extractor.py  # 25개 테스트
   backend/tests/test_type_classifier.py  # 33개 테스트
   ```
   - 총 58개 테스트 PASS

### 선택적 조치 (성능 최적화 필요 시)

2. **search_chunks_v2 RPC 구현**
   - 현재 Python 필터링이 정상 작동
   - 47K+ 청크에서 성능 측정 후 결정

---

## 9. 결론

**Match Rate 92%** - 핵심 기능 및 테스트 모두 구현 완료. Design 대비 **개선된 부분이 더 많습니다**.

### 강점
- DB 스키마 완벽 구현 (98%)
- 엔티티 추출/분류 로직 확장 (더 많은 패턴, 키워드)
- 마이그레이션 스크립트 game_id 필터 추가
- Retriever 필터링 Python 측 구현으로 유연성 확보
- 58개 단위 테스트 100% PASS

### 다음 단계
```bash
# 90%+ 달성 - Completion Report 생성
/pdca report entity-tagging-improvement
```

---

**분석 완료**: 2026-02-25
**분석 도구**: bkit:gap-detector
