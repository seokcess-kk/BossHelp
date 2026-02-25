# RAG 파이프라인 개선 설계 문서

## 개요

| 항목 | 내용 |
|------|------|
| 기능명 | rag-improvement |
| Plan 문서 | `docs/01-plan/features/rag-improvement.plan.md` |
| 설계 버전 | v1.0 |
| 작성일 | 2026-02-25 |

## 아키텍처

### 현재 흐름
```
질문 → 번역(Haiku) → 엔티티 추출 → 임베딩 → 벡터검색 → 리랭킹 → 프롬프트 → Claude → 답변
```

### 개선 후 흐름
```
질문 → 번역(Haiku + 폴백) → 엔티티 추출(자동 확장) → 다중 키워드 추출
     → 임베딩 → 벡터검색(다중 키워드) → 리랭킹(다양성 보장)
     → 의도 분류 → 프롬프트 → Claude → 답변
```

## 컴포넌트 상세 설계

### 1. EntityAutoExtractor (신규)

**파일**: `backend/app/core/entity/auto_extractor.py`

```python
"""Entity Auto Extractor for BossHelp.

크롤링된 청크 제목에서 엔티티를 자동 추출하여 사전 확장.
"""

import re
from functools import lru_cache
from supabase import Client
from app.db.supabase import get_supabase_client


class EntityAutoExtractor:
    """청크 제목에서 엔티티 자동 추출."""

    # Wiki 제목 패턴
    WIKI_TITLE_PATTERNS = [
        # "Malenia Blade of Miquella | Elden Ring Wiki"
        r"^(.+?)\s*\|\s*(?:Elden Ring|Dark Souls|Sekiro|Hollow Knight|Lies of P)\s*Wiki",
        # "Malenia Blade of Miquella"
        r"^([A-Z][^|]+)$",
    ]

    # 제외 패턴 (일반 페이지)
    EXCLUDE_PATTERNS = [
        r"^Builds?\b",
        r"^Weapons?\b",
        r"^Armor\b",
        r"^Items?\b",
        r"^Walkthrough\b",
        r"^Guide\b",
        r"^Tips\b",
    ]

    def __init__(self, client: Client | None = None):
        self.client = client or get_supabase_client()

    def extract_from_game(self, game_id: str) -> dict[str, str]:
        """게임의 모든 청크에서 엔티티 추출."""

        # 고유 제목 조회
        result = self.client.table("chunks").select(
            "title"
        ).eq("game_id", game_id).eq("is_active", True).execute()

        if not result.data:
            return {}

        # 제목에서 엔티티 추출
        entities = {}
        seen_titles = set()

        for chunk in result.data:
            title = chunk.get("title", "")
            if not title or title in seen_titles:
                continue
            seen_titles.add(title)

            # 패턴 매칭으로 엔티티명 추출
            entity_name = self._extract_entity_name(title)
            if entity_name and not self._should_exclude(entity_name):
                # 정규화된 키 생성 (소문자, 공백 제거)
                key = entity_name.lower().strip()
                if key not in entities:
                    entities[key] = entity_name

        return entities

    def _extract_entity_name(self, title: str) -> str | None:
        """제목에서 엔티티명 추출."""
        for pattern in self.WIKI_TITLE_PATTERNS:
            match = re.match(pattern, title.strip())
            if match:
                return match.group(1).strip()
        return None

    def _should_exclude(self, name: str) -> bool:
        """제외 대상인지 확인."""
        for pattern in self.EXCLUDE_PATTERNS:
            if re.match(pattern, name, re.IGNORECASE):
                return True
        return False

    def merge_with_manual_dict(
        self,
        auto_entities: dict[str, str],
        manual_dict: dict[str, str]
    ) -> dict[str, str]:
        """자동 추출 엔티티와 수동 사전 병합.

        수동 사전이 우선순위를 가짐 (한글 → 영어 매핑 유지).
        """
        merged = dict(manual_dict)  # 수동 사전 복사

        # 자동 추출된 엔티티 중 수동 사전에 없는 것만 추가
        manual_values = set(v.lower() for v in manual_dict.values())

        for key, value in auto_entities.items():
            if value.lower() not in manual_values:
                # 영어 엔티티는 그대로 추가 (영어 → 영어)
                merged[value] = value

        return merged


@lru_cache()
def get_entity_extractor() -> EntityAutoExtractor:
    """EntityAutoExtractor 싱글톤."""
    return EntityAutoExtractor()
```

### 2. EntityDictionary 수정

**파일**: `backend/app/core/entity/dictionary.py`

**변경 사항**:
```python
# 기존 __init__ 수정
def __init__(self, game_id: str, auto_expand: bool = True):
    self.game_id = game_id
    self.ko_to_en = dict(ENTITY_DICTS.get(game_id, {}))  # 복사본 생성

    # 자동 확장
    if auto_expand:
        self._expand_with_auto_entities()

    self.en_to_ko = {v: k for k, v in self.ko_to_en.items()}

def _expand_with_auto_entities(self):
    """자동 추출 엔티티로 사전 확장."""
    from app.core.entity.auto_extractor import get_entity_extractor

    extractor = get_entity_extractor()
    auto_entities = extractor.extract_from_game(self.game_id)

    # 병합 (수동 사전 우선)
    self.ko_to_en = extractor.merge_with_manual_dict(
        auto_entities,
        self.ko_to_en
    )
```

### 3. MultiKeywordRetriever (Retriever 수정)

**파일**: `backend/app/core/rag/retriever.py`

**변경 사항**:
```python
def extract_search_keywords(self, query: str, max_keywords: int = 3) -> list[str]:
    """쿼리에서 복수 검색 키워드 추출.

    우선순위:
    1. 대문자로 시작하는 단어 (엔티티명)
    2. 숫자 포함 단어 (phase 2, floor 1)
    3. 게임 특화 용어
    """
    import re

    # 구두점 제거
    clean_query = re.sub(r'[^\w\s]', ' ', query)
    words = clean_query.split()

    keywords = []
    stop_words = {
        "how", "what", "where", "when", "why", "can", "does", "the",
        "this", "are", "could", "would", "should", "to", "do", "i", "a"
    }

    # 1. 대문자 시작 단어 (엔티티명 가능성 높음)
    for word in words:
        if len(word) >= 3 and word[0].isupper() and word.lower() not in stop_words:
            keywords.append(word)

    # 2. 숫자 포함 단어 조합 (phase 2, floor 1 등)
    for i, word in enumerate(words):
        if word.isdigit() and i > 0:
            prev_word = words[i-1]
            if prev_word.lower() in {"phase", "floor", "stage", "part", "act"}:
                keywords.append(f"{prev_word} {word}")

    # 3. 게임 특화 용어
    game_terms = {"build", "dodge", "parry", "roll", "attack", "weapon", "armor"}
    for word in words:
        if word.lower() in game_terms and word not in keywords:
            keywords.append(word)

    return keywords[:max_keywords]

def search(self, ..., query: str = "") -> list[dict]:
    """벡터 검색 (다중 키워드 지원)."""

    # 다중 키워드 추출
    keywords = self.extract_search_keywords(query)

    # 첫 번째 키워드로 주 검색
    primary_keyword = keywords[0] if keywords else None

    print(f"[Retriever] Keywords: {keywords}, Primary: {primary_keyword}")

    # RPC 호출 (기존 로직 유지, primary_keyword 사용)
    # ...

    # 보조 키워드로 결과 필터링/부스팅
    if len(keywords) > 1 and response.data:
        response.data = self._boost_by_secondary_keywords(
            response.data,
            keywords[1:]
        )

    return response.data

def _boost_by_secondary_keywords(
    self,
    chunks: list[dict],
    secondary_keywords: list[str]
) -> list[dict]:
    """보조 키워드 매칭으로 점수 부스팅."""
    for chunk in chunks:
        content = (chunk.get("content", "") + chunk.get("title", "")).lower()

        match_count = sum(
            1 for kw in secondary_keywords
            if kw.lower() in content
        )

        if match_count > 0:
            chunk["similarity"] = min(1.0, chunk.get("similarity", 0.5) + match_count * 0.05)

    chunks.sort(key=lambda x: x.get("similarity", 0), reverse=True)
    return chunks
```

### 4. SourceDiversityReranker (Reranker 수정)

**파일**: `backend/app/core/rag/reranker.py`

**추가 메서드**:
```python
def ensure_source_diversity(
    self,
    chunks: list[dict],
    max_per_source: int = 2
) -> list[dict]:
    """출처별 청크 수 제한으로 다양성 보장.

    Args:
        chunks: 정렬된 청크 리스트
        max_per_source: 출처당 최대 청크 수

    Returns:
        다양한 출처의 청크 리스트
    """
    source_counts: dict[str, int] = {}
    diverse_chunks = []

    for chunk in chunks:
        source_url = chunk.get("source_url", "")

        # URL에서 기본 페이지 추출 (쿼리 파라미터, 앵커 제거)
        base_url = source_url.split("#")[0].split("?")[0]

        current_count = source_counts.get(base_url, 0)

        if current_count < max_per_source:
            diverse_chunks.append(chunk)
            source_counts[base_url] = current_count + 1

    return diverse_chunks

def rerank_multi_stage(self, ...) -> list[dict]:
    """다단계 리랭킹 파이프라인 (수정)."""

    # ... 기존 Stage 1-5 ...

    # Stage 6: 출처 다양성 보장 (NEW)
    chunks = self.ensure_source_diversity(chunks, max_per_source=2)

    # Stage 7: Deduplication
    chunks = self.deduplicate(chunks)

    # Stage 8: Final ranking
    return chunks[:top_k]
```

### 5. TranslatorFallback (Translator 수정)

**파일**: `backend/app/core/rag/translator.py`

**변경 사항**:
```python
def translate(self, question: str, game_id: str) -> str:
    """한글 질문을 영어로 번역 (폴백 포함)."""

    if not self._contains_korean(question):
        return question

    # 캐시 확인
    cache_key = self._make_cache_key(question, game_id)
    if cache_key in self._cache:
        return self._cache[cache_key]

    # 1차 시도: Haiku 번역
    try:
        translated = self._translate_with_haiku(question, game_id)
        self._cache[cache_key] = translated
        return translated
    except Exception as e:
        logger.warning(f"Haiku translation failed: {e}, using fallback")

    # 2차 시도: 엔티티 사전 기반 번역
    translated = self._translate_with_entity_dict(question, game_id)
    self._cache[cache_key] = translated
    return translated

def _translate_with_entity_dict(self, question: str, game_id: str) -> str:
    """엔티티 사전으로 한글 → 영어 치환."""
    from app.core.entity.dictionary import get_entity_dictionary

    entity_dict = get_entity_dictionary(game_id)
    translated = entity_dict.translate_to_english(question)

    logger.info(f"Fallback translation: '{question}' -> '{translated}'")
    return translated
```

### 6. IntentClassifier (신규 - Optional)

**파일**: `backend/app/core/rag/intent_classifier.py`

```python
"""Intent Classifier for BossHelp.

질문 의도를 분류하여 카테고리 부스팅 개선.
"""

import hashlib
from anthropic import Anthropic
from app.config import get_settings


class IntentClassifier:
    """LLM 기반 질문 의도 분류."""

    INTENTS = [
        "boss_strategy",   # 보스 공략
        "item_location",   # 아이템 위치
        "build_guide",     # 빌드 추천
        "quest_guide",     # 퀘스트 가이드
        "mechanic_tip",    # 메카닉 설명
        "lore",            # 스토리/로어
        "general",         # 일반 질문
    ]

    # 패턴 기반 빠른 분류 (LLM 호출 전)
    PATTERN_INTENTS = {
        "boss_strategy": [
            "공략", "패턴", "이기", "잡", "처치", "물리치", "회피",
            "beat", "defeat", "kill", "strategy", "dodge", "phase"
        ],
        "item_location": [
            "위치", "어디", "획득", "얻", "찾",
            "where", "find", "get", "location"
        ],
        "build_guide": [
            "빌드", "스탯", "무기", "추천",
            "build", "stat", "weapon", "recommend"
        ],
        "quest_guide": [
            "퀘스트", "NPC", "엔딩",
            "quest", "ending", "route"
        ],
    }

    def __init__(self):
        self._cache: dict[str, str] = {}

    def classify(self, question: str, game_id: str) -> str:
        """질문 의도 분류.

        1. 패턴 매칭으로 빠른 분류 시도
        2. 실패 시 LLM 분류 (캐시 확인)
        """
        # 1. 패턴 기반 분류
        intent = self._classify_by_pattern(question)
        if intent:
            return intent

        # 2. 캐시 확인
        cache_key = self._make_cache_key(question, game_id)
        if cache_key in self._cache:
            return self._cache[cache_key]

        # 3. LLM 분류 (선택적 - 비용 고려)
        # intent = self._classify_with_llm(question, game_id)
        # self._cache[cache_key] = intent

        return "general"

    def _classify_by_pattern(self, question: str) -> str | None:
        """패턴 매칭으로 빠른 분류."""
        question_lower = question.lower()

        for intent, patterns in self.PATTERN_INTENTS.items():
            if any(p in question_lower for p in patterns):
                return intent

        return None

    def _make_cache_key(self, question: str, game_id: str) -> str:
        content = f"{game_id}:{question}"
        return hashlib.md5(content.encode()).hexdigest()


_classifier: IntentClassifier | None = None

def get_intent_classifier() -> IntentClassifier:
    global _classifier
    if _classifier is None:
        _classifier = IntentClassifier()
    return _classifier
```

## 데이터 흐름

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Query Processing                             │
├─────────────────────────────────────────────────────────────────────┤
│  User Question: "말레니아 2페이즈 워터파울 댄스 회피법"                │
│       │                                                              │
│       ▼                                                              │
│  [Translator] ──────────────────────────────────────────────────────│
│       │ Haiku 번역 시도                                              │
│       │ 성공 → "Malenia phase 2 Waterfowl Dance dodge"              │
│       │ 실패 → 엔티티 사전 폴백                                      │
│       ▼                                                              │
│  [EntityDictionary] (자동 확장)                                      │
│       │ 말레니아 → Malenia                                           │
│       │ 워터파울 댄스 → Waterfowl Dance                              │
│       ▼                                                              │
│  [KeywordExtractor]                                                  │
│       │ keywords = ["Malenia", "phase 2", "Waterfowl Dance"]        │
│       ▼                                                              │
│  [VectorRetriever]                                                   │
│       │ Primary: "Malenia"                                           │
│       │ Secondary boost: "phase 2", "Waterfowl Dance"               │
│       ▼                                                              │
│  [MultiStageReranker]                                                │
│       │ Entity boost → Keyword boost → Category boost               │
│       │ Source diversity (max 2 per URL)                            │
│       │ Deduplication                                                │
│       ▼                                                              │
│  [IntentClassifier]                                                  │
│       │ intent = "boss_strategy"                                     │
│       ▼                                                              │
│  [PromptBuilder]                                                     │
│       │ 상위 5개 청크 + 의도 기반 프롬프트                           │
│       ▼                                                              │
│  [Claude] → Answer                                                   │
└─────────────────────────────────────────────────────────────────────┘
```

## 파일 구조

```
backend/app/core/
├── entity/
│   ├── __init__.py
│   ├── dictionary.py        # 수정: auto_expand 옵션 추가
│   └── auto_extractor.py    # 신규: 엔티티 자동 추출
├── rag/
│   ├── __init__.py
│   ├── pipeline.py          # 수정: IntentClassifier 연동
│   ├── retriever.py         # 수정: 다중 키워드 검색
│   ├── reranker.py          # 수정: 출처 다양성 보장
│   ├── translator.py        # 수정: 폴백 로직 추가
│   ├── intent_classifier.py # 신규: 의도 분류
│   └── prompt.py
└── llm/
    ├── __init__.py
    ├── claude.py
    └── embeddings.py
```

## 구현 순서

| 순서 | 작업 | 파일 | 의존성 |
|------|------|------|--------|
| 1 | EntityAutoExtractor | `auto_extractor.py` (신규) | 없음 |
| 2 | EntityDictionary 수정 | `dictionary.py` | 1 |
| 3 | Retriever 다중 키워드 | `retriever.py` | 없음 |
| 4 | Reranker 출처 다양성 | `reranker.py` | 없음 |
| 5 | Translator 폴백 | `translator.py` | 2 |
| 6 | IntentClassifier (선택) | `intent_classifier.py` (신규) | 없음 |
| 7 | Pipeline 연동 | `pipeline.py` | 1-6 |
| 8 | 테스트 | `test_rag_improvement.py` | 7 |

## 테스트 케이스

```python
# backend/tests/test_rag_improvement.py

import pytest
from app.core.entity.auto_extractor import EntityAutoExtractor
from app.core.rag.retriever import VectorRetriever
from app.core.rag.reranker import MultiStageReranker

class TestEntityAutoExtractor:
    def test_extract_from_wiki_title(self):
        extractor = EntityAutoExtractor()
        title = "Malenia Blade of Miquella | Elden Ring Wiki"
        name = extractor._extract_entity_name(title)
        assert name == "Malenia Blade of Miquella"

    def test_exclude_generic_pages(self):
        extractor = EntityAutoExtractor()
        assert extractor._should_exclude("Builds") == True
        assert extractor._should_exclude("Malenia") == False

class TestMultiKeywordRetriever:
    def test_extract_keywords(self):
        retriever = VectorRetriever()
        query = "How to beat Malenia phase 2?"
        keywords = retriever.extract_search_keywords(query)
        assert "Malenia" in keywords
        assert "phase 2" in keywords

class TestSourceDiversity:
    def test_max_per_source(self):
        reranker = MultiStageReranker()
        chunks = [
            {"source_url": "http://a.com/page1", "similarity": 0.9},
            {"source_url": "http://a.com/page1", "similarity": 0.85},
            {"source_url": "http://a.com/page1", "similarity": 0.8},
            {"source_url": "http://b.com/page2", "similarity": 0.75},
        ]
        diverse = reranker.ensure_source_diversity(chunks, max_per_source=2)
        assert len(diverse) == 3  # a.com에서 2개, b.com에서 1개
```

## 성능 지표

| 지표 | 현재 | 목표 |
|------|------|------|
| 평균 답변 관련성 | 68% | 80% |
| 엔티티 인식률 | 60% | 90% |
| 출처 다양성 | 1.2 sources/query | 2.5 sources/query |
| 레이턴시 | 9,000ms | 10,000ms (10% 이내 증가) |

## 롤백 계획

문제 발생 시:
1. `dictionary.py`: `auto_expand=False` 설정
2. `retriever.py`: 기존 단일 키워드 로직 복원
3. `reranker.py`: `ensure_source_diversity` 호출 제거
4. `translator.py`: 폴백 로직 비활성화
