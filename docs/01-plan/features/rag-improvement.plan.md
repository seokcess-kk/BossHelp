# RAG 파이프라인 개선 계획

## 개요

| 항목 | 내용 |
|------|------|
| 기능명 | rag-improvement |
| 목표 | 기존 Vector RAG 파이프라인 품질 향상 (+10% 정확도) |
| 우선순위 | 높음 |
| 예상 작업 시간 | 4-6시간 |
| 담당 | AI Agent |

## 현재 문제점

### 1. 검색 키워드 추출 단순함
- **위치**: `retriever.py:53-61`
- **문제**: 대문자 단어 중 가장 긴 단어만 선택
- **예시**: "How to beat Malenia phase 2?" → "Malenia"만 추출, "phase 2" 무시

### 2. 엔티티 사전 수동 관리
- **위치**: `dictionary.py`
- **문제**: 게임별 엔티티가 하드코딩, 신규 보스/아이템 누락
- **예시**: Silksong 보스 44개 중 5개만 등록

### 3. 출처 다양성 부족
- **위치**: `reranker.py`
- **문제**: 같은 URL에서 5개 청크 모두 선택 가능
- **결과**: 편향된 정보 제공

### 4. 번역 실패 시 폴백 없음
- **위치**: `translator.py:76-79`
- **문제**: Haiku API 실패 시 한글 그대로 반환 → 영어 DB 매칭 불가

### 5. 카테고리 패턴 하드코딩
- **위치**: `reranker.py:156-177`
- **문제**: 유연성 부족, 새로운 질문 유형 대응 어려움

## 개선 계획

### Phase 1: 엔티티 사전 자동 확장 (1.5시간)

#### 목표
크롤링된 청크 제목에서 엔티티 자동 추출하여 사전 확장

#### 구현 방안
```python
# 새 파일: backend/app/core/entity/auto_extractor.py

def extract_entities_from_chunks(game_id: str) -> dict[str, str]:
    """청크 제목에서 엔티티 자동 추출."""
    # 1. 해당 게임의 모든 청크 제목 조회
    # 2. Wiki 페이지 제목 패턴 파싱: "Malenia Blade of Miquella | Elden Ring Wiki"
    # 3. 보스명, 무기명, 위치명 추출
    # 4. 기존 사전과 병합
```

#### 수정 파일
- `backend/app/core/entity/auto_extractor.py` (신규)
- `backend/app/core/entity/dictionary.py` (자동 확장 연동)

### Phase 2: 다중 키워드 검색 (1시간)

#### 목표
단일 키워드 대신 복수 키워드로 검색하여 정확도 향상

#### 구현 방안
```python
# retriever.py 수정

def extract_search_keywords(query: str) -> list[str]:
    """쿼리에서 복수 검색 키워드 추출."""
    # 1. 엔티티명 (대문자 시작)
    # 2. 숫자 포함 단어 (phase 2, 1st floor 등)
    # 3. 게임 특화 용어 (build, dodge, parry 등)
    return keywords  # ["Malenia", "phase 2"]
```

#### 수정 파일
- `backend/app/core/rag/retriever.py`

### Phase 3: 출처 다양성 보장 (1시간)

#### 목표
같은 URL에서 최대 2개 청크만 선택하여 다양한 관점 제공

#### 구현 방안
```python
# reranker.py 수정

def ensure_source_diversity(chunks: list[dict], max_per_source: int = 2) -> list[dict]:
    """출처별 청크 수 제한."""
    source_counts = {}
    diverse_chunks = []

    for chunk in chunks:
        source = chunk.get("source_url", "")
        if source_counts.get(source, 0) < max_per_source:
            diverse_chunks.append(chunk)
            source_counts[source] = source_counts.get(source, 0) + 1

    return diverse_chunks
```

#### 수정 파일
- `backend/app/core/rag/reranker.py`

### Phase 4: 번역 폴백 강화 (0.5시간)

#### 목표
Haiku 번역 실패 시 엔티티 사전 기반 폴백

#### 구현 방안
```python
# translator.py 수정

def translate_with_fallback(self, question: str, game_id: str) -> str:
    """번역 실패 시 엔티티 사전으로 폴백."""
    try:
        return self._translate_with_haiku(question, game_id)
    except Exception:
        # 폴백: 엔티티 사전으로 한글 → 영어 치환
        entity_dict = get_entity_dictionary(game_id)
        return entity_dict.translate_to_english(question)
```

#### 수정 파일
- `backend/app/core/rag/translator.py`

### Phase 5: 의도 분류 강화 (1시간)

#### 목표
질문 의도를 더 정확하게 분류하여 카테고리 부스팅 개선

#### 구현 방안
```python
# 새 파일: backend/app/core/rag/intent_classifier.py

class IntentClassifier:
    """LLM 기반 질문 의도 분류."""

    INTENTS = [
        "boss_strategy",   # 보스 공략
        "item_location",   # 아이템 위치
        "build_guide",     # 빌드 추천
        "quest_guide",     # 퀘스트 가이드
        "mechanic_tip",    # 메카닉 설명
        "lore",            # 스토리/로어
    ]

    def classify(self, question: str, game_id: str) -> str:
        """Haiku로 빠른 의도 분류."""
        # 캐시 확인 후 LLM 호출
```

#### 수정 파일
- `backend/app/core/rag/intent_classifier.py` (신규)
- `backend/app/core/rag/pipeline.py` (연동)

## 예상 결과

| 질문 유형 | 현재 | 개선 후 | 개선폭 |
|----------|------|---------|--------|
| "말레니아 공략" | 90% | 92% | +2% |
| "라단 2페이즈 회피법" | 70% | 82% | +12% |
| "그랜드 마더 실크 패턴" | 50% | 75% | +25% |
| "출혈빌드 추천무기" | 60% | 72% | +12% |
| **평균** | **68%** | **80%** | **+12%** |

## 테스트 계획

### 단위 테스트
- `test_auto_extractor.py`: 엔티티 자동 추출 검증
- `test_retriever.py`: 다중 키워드 검색 검증
- `test_reranker.py`: 출처 다양성 검증

### 통합 테스트
```python
# test_rag_improvement.py
test_cases = [
    ("elden-ring", "말레니아 2페이즈 공략"),
    ("silksong", "Grand Mother Silk 패턴"),
    ("dark-souls-3", "무명왕 번개 회피법"),
    ("lies-of-p", "Laxasia 산 데미지"),
]
```

### 성능 측정
- 개선 전/후 동일 질문 100개 테스트
- 답변 관련성 스코어 비교

## 구현 순서

| 순서 | 작업 | 예상 시간 | 의존성 |
|------|------|----------|--------|
| 1 | Phase 1: 엔티티 자동 확장 | 1.5h | 없음 |
| 2 | Phase 2: 다중 키워드 검색 | 1h | Phase 1 |
| 3 | Phase 3: 출처 다양성 | 1h | 없음 |
| 4 | Phase 4: 번역 폴백 | 0.5h | Phase 1 |
| 5 | Phase 5: 의도 분류 | 1h | 없음 |
| 6 | 통합 테스트 | 1h | 전체 |

**총 예상 시간: 6시간**

## 후속 작업 (향후 고려)

개선 완료 후 효과 검증 결과에 따라:
- **효과 충분 (+10% 이상)**: 현 상태 유지, 모니터링
- **효과 부족 (+5% 미만)**: 경량 GraphRAG 도입 검토 (보스-공격 관계만)

## 참고 자료

- 현재 RAG 파이프라인: `backend/app/core/rag/pipeline.py`
- 엔티티 사전: `backend/app/core/entity/dictionary.py`
- 리랭커: `backend/app/core/rag/reranker.py`
- 번역기: `backend/app/core/rag/translator.py`
