# Plan: Entity Tagging Improvement

> 청크 레벨 엔티티 태깅 정확도 개선을 통한 RAG 검색 품질 향상

## 배경 및 문제

### 현재 상황

```
47,073개 청크
├── 데이터 품질: ✅ 우수 (99% 고품질, 평균 1,513자)
├── entity_tags: ⚠️ 페이지 레벨 태깅 (정확도 낮음)
└── 검색 정확도: ⚠️ 엔티티 검색 시 오매칭 발생
```

### 핵심 문제

| 문제 | 현상 | 영향 |
|------|------|------|
| **페이지 레벨 태깅** | Malenia 페이지의 모든 청크가 `['radahn', 'ranni', 'rivers of blood', 'malenia']` 태그 보유 | 엔티티 필터링 정확도 저하 |
| **주 엔티티 미구분** | "Malenia 페이지"인지 "Radahn 페이지"인지 알 수 없음 | 출처 품질 저하 |
| **태그 다양성 부족** | 47,073개 청크 중 유니크 태그 조합 ~100개 | 세밀한 검색 불가 |

### 실제 문제 사례

```
질문: "라단 페스티벌 공략"

Before (엔티티 사전만 개선):
  번역: "Radahn Festival" → Builds 페이지 반환 ❌

After (번역 선처리 추가):
  번역: "Starscourge Radahn" → Radahn 페이지 반환 ✅

하지만 여전히:
  - entity_tags로 필터링 불가 (정확도 낮음)
  - 벡터 검색에만 의존 (속도 저하)
```

## 목표

### 주요 목표

1. **primary_entity 필드 추가**: 각 청크의 주 엔티티 식별
2. **entity_type 분류**: 보스/무기/장소/NPC 등 엔티티 유형 분류
3. **검색 파이프라인 연동**: 엔티티 기반 1차 필터링 → 벡터 검색

### 성공 지표

| 지표 | 현재 | 목표 |
|------|------|------|
| 엔티티 검색 정확도 | 70% (추정) | 95%+ |
| 1차 필터링 가능 청크 | 0% | 80%+ |
| 검색 응답 시간 | 8-15초 | 5초 이하 |

## 범위

### In Scope

- [ ] DB 스키마 확장 (primary_entity, entity_type)
- [ ] Title 기반 엔티티 추출 로직 구현
- [ ] 기존 청크 마이그레이션 (47,073개)
- [ ] Retriever에서 엔티티 필터링 로직 추가

### Out of Scope

- 청크 레벨 content 재분석 (LLM 비용 높음)
- entities 별도 테이블 분리 (스키마 대변경)
- GraphRAG 도입 (별도 프로젝트)

## 접근 방식

### Phase 1: DB 스키마 확장

```sql
-- chunks 테이블에 칼럼 추가
ALTER TABLE chunks ADD COLUMN primary_entity TEXT;
ALTER TABLE chunks ADD COLUMN entity_type TEXT;

-- 인덱스 추가 (검색 성능)
CREATE INDEX idx_chunks_primary_entity ON chunks(primary_entity);
CREATE INDEX idx_chunks_entity_type ON chunks(entity_type);
```

### Phase 2: Title 기반 엔티티 추출

```python
class TitleEntityExtractor:
    """Title에서 주 엔티티 추출."""

    WIKI_PATTERN = r"^(.+?)\s*\|\s*(?:Elden Ring|Dark Souls|Sekiro|...).*Wiki"

    def extract(self, title: str) -> tuple[str, str]:
        """
        Returns:
            (entity_name, entity_type)

        Examples:
            "Malenia Blade of Miquella | Elden Ring Wiki"
            → ("Malenia Blade of Miquella", "boss")

            "Moonveil | Elden Ring Wiki"
            → ("Moonveil", "weapon")
        """
```

### Phase 3: 엔티티 유형 분류

| entity_type | 키워드/패턴 | 예시 |
|-------------|-------------|------|
| `boss` | Demigod, Lord, King, Knight 등 | Malenia, Radahn |
| `weapon` | Sword, Katana, Staff 등 | Moonveil, Rivers of Blood |
| `armor` | Armor, Helm, Gauntlets 등 | Radahn's Set |
| `location` | Castle, Ruins, Dungeon 등 | Redmane Castle |
| `npc` | Merchant, Knight (비보스) | Patches, Alexander |
| `item` | Talisman, Seal, Ring 등 | Shard of Alexander |
| `spell` | Incantation, Sorcery 등 | Comet Azur |
| `mechanic` | Guide, Tips, Build 등 | Builds, Ashes of War |

### Phase 4: 마이그레이션 스크립트

```python
# crawler/migrate_entity_tags.py
async def migrate_all_chunks():
    """기존 47,073개 청크에 primary_entity, entity_type 추가."""

    extractor = TitleEntityExtractor()
    classifier = EntityTypeClassifier()

    for chunk in get_all_chunks():
        entity_name = extractor.extract(chunk.title)
        entity_type = classifier.classify(entity_name, chunk.category)

        await update_chunk(
            chunk.id,
            primary_entity=entity_name,
            entity_type=entity_type
        )
```

### Phase 5: Retriever 연동

```python
# backend/app/core/rag/retriever.py
def search(self, query: str, game_id: str, ...):
    # 1. 질문에서 엔티티 추출
    entities = self.entity_extractor.extract_from_query(query)

    # 2. primary_entity로 1차 필터링 (있으면)
    if entities:
        chunks = self.filter_by_entity(entities, game_id)
    else:
        chunks = self.get_all_chunks(game_id)

    # 3. 벡터 검색으로 정밀 검색
    results = self.vector_search(chunks, query_embedding)

    return results
```

## 구현 순서

| 순서 | 작업 | 예상 난이도 |
|:----:|------|:-----------:|
| 1 | DB 스키마 확장 (SQL) | 쉬움 |
| 2 | TitleEntityExtractor 구현 | 중간 |
| 3 | EntityTypeClassifier 구현 | 중간 |
| 4 | 마이그레이션 스크립트 작성/실행 | 중간 |
| 5 | Retriever 연동 | 중간 |
| 6 | 테스트 및 검증 | 쉬움 |

## 위험 요소

| 위험 | 확률 | 영향 | 대응 |
|------|:----:|:----:|------|
| Title 패턴 예외 | 중간 | 중간 | 미매칭 청크는 기존 방식 유지 |
| 마이그레이션 시간 | 낮음 | 낮음 | 배치 처리, 비동기 실행 |
| entity_type 오분류 | 중간 | 낮음 | category 필드 참조로 보완 |

## 의존성

- Supabase SQL 실행 권한
- 기존 chunks 테이블 구조
- EntityAutoExtractor (이미 구현됨)

## 예상 효과

```
Before:
  질문 → 번역 → 벡터 검색 (47,073개 전체) → 리랭킹
  응답 시간: 8-15초

After:
  질문 → 엔티티 추출 → 엔티티 필터링 (~500개) → 벡터 검색 → 리랭킹
  응답 시간: 3-5초 (예상)
```

## 참고 자료

- 현재 chunks 스키마: `supabase/migrations/001_initial_schema.sql`
- EntityAutoExtractor: `backend/app/core/entity/auto_extractor.py`
- Retriever: `backend/app/core/rag/retriever.py`

---

**작성일**: 2026-02-25
**상태**: Plan 작성 완료
