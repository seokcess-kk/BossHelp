"""RAG 파이프라인 개선 테스트.

이 테스트는 rag-improvement 기능의 핵심 컴포넌트를 검증합니다:
- Phase 1: EntityAutoExtractor
- Phase 3: 다중 키워드 검색
- Phase 4: 출처 다양성
"""

import pytest
from unittest.mock import MagicMock, patch


class TestEntityAutoExtractor:
    """EntityAutoExtractor 단위 테스트."""

    def test_extract_from_wiki_title(self):
        """Wiki 제목에서 엔티티명 추출 테스트."""
        from app.core.entity.auto_extractor import EntityAutoExtractor

        extractor = EntityAutoExtractor(client=MagicMock())

        # Wiki 패턴 1: "Entity | Game Wiki"
        title = "Malenia Blade of Miquella | Elden Ring Wiki"
        name = extractor._extract_entity_name(title)
        assert name == "Malenia Blade of Miquella"

        # Wiki 패턴 2: Dark Souls Wiki
        title = "Artorias the Abysswalker | Dark Souls Wiki"
        name = extractor._extract_entity_name(title)
        assert name == "Artorias the Abysswalker"

        # Wiki 패턴 3: Hollow Knight Wiki
        title = "Hornet | Hollow Knight Wiki"
        name = extractor._extract_entity_name(title)
        assert name == "Hornet"

    def test_extract_plain_title(self):
        """일반 제목에서 엔티티명 추출 테스트."""
        from app.core.entity.auto_extractor import EntityAutoExtractor

        extractor = EntityAutoExtractor(client=MagicMock())

        # 대문자로 시작하는 일반 제목
        title = "Radahn Festival"
        name = extractor._extract_entity_name(title)
        assert name == "Radahn Festival"

    def test_exclude_generic_pages(self):
        """일반 페이지 제외 테스트."""
        from app.core.entity.auto_extractor import EntityAutoExtractor

        extractor = EntityAutoExtractor(client=MagicMock())

        # 제외 대상
        assert extractor._should_exclude("Builds") is True
        assert extractor._should_exclude("Weapons") is True
        assert extractor._should_exclude("Armor") is True
        assert extractor._should_exclude("Items") is True
        assert extractor._should_exclude("Walkthrough") is True
        assert extractor._should_exclude("Guide") is True
        assert extractor._should_exclude("Locations") is True

        # 포함 대상
        assert extractor._should_exclude("Malenia") is False
        assert extractor._should_exclude("Radahn") is False
        assert extractor._should_exclude("Hornet") is False

    def test_merge_with_manual_dict(self):
        """수동 사전과 자동 추출 병합 테스트."""
        from app.core.entity.auto_extractor import EntityAutoExtractor

        extractor = EntityAutoExtractor(client=MagicMock())

        auto_entities = {
            "malenia": "Malenia",
            "radahn": "Radahn",
        }
        manual_dict = {
            "말레니아": "Malenia",  # 이미 존재
            "라단": "Radahn",  # 이미 존재
            "모르곳": "Morgott",  # 수동만 존재
        }

        merged = extractor.merge_with_manual_dict(auto_entities, manual_dict)

        # 수동 사전 항목 유지
        assert merged["말레니아"] == "Malenia"
        assert merged["라단"] == "Radahn"
        assert merged["모르곳"] == "Morgott"

        # 중복되지 않은 자동 추출 항목은 추가되지 않음 (이미 manual_values에 존재)
        # Malenia, Radahn은 manual_dict의 values에 있으므로 추가 안됨

    def test_cache_functionality(self):
        """캐시 기능 테스트."""
        from app.core.entity.auto_extractor import EntityAutoExtractor

        extractor = EntityAutoExtractor(client=MagicMock())

        # 캐시에 직접 데이터 설정
        extractor._cache["test-game"] = {"boss1": "Boss One"}

        # 캐시 히트 확인
        result = extractor.extract_from_game("test-game")
        assert result == {"boss1": "Boss One"}

        # 캐시 클리어
        extractor.clear_cache("test-game")
        assert "test-game" not in extractor._cache

        # 전체 캐시 클리어
        extractor._cache["game1"] = {}
        extractor._cache["game2"] = {}
        extractor.clear_cache()
        assert len(extractor._cache) == 0


class TestMultiKeywordRetriever:
    """다중 키워드 검색 테스트."""

    def test_extract_entity_keywords(self):
        """대문자 엔티티 키워드 추출 테스트."""
        from app.core.rag.retriever import VectorRetriever

        retriever = VectorRetriever(client=MagicMock())

        query = "How to beat Malenia phase 2?"
        keywords = retriever._extract_search_keywords(query)

        # Malenia는 대문자로 시작하는 엔티티
        assert "Malenia" in keywords

    def test_extract_phase_keywords(self):
        """숫자 포함 키워드 (phase 2 등) 추출 테스트."""
        from app.core.rag.retriever import VectorRetriever

        retriever = VectorRetriever(client=MagicMock())

        query = "How to beat Malenia phase 2?"
        keywords = retriever._extract_search_keywords(query)

        # phase 2 조합 또는 2 포함 키워드
        has_phase = any("phase" in kw.lower() for kw in keywords)
        has_number = any("2" in kw for kw in keywords)
        assert has_phase or has_number

    def test_extract_game_terms(self):
        """게임 특화 용어 추출 테스트."""
        from app.core.rag.retriever import VectorRetriever

        retriever = VectorRetriever(client=MagicMock())

        query = "best dodge timing for parry build"
        keywords = retriever._extract_search_keywords(query)

        # 게임 용어가 추출되어야 함
        keywords_lower = [kw.lower() for kw in keywords]
        assert any(term in keywords_lower for term in ["dodge", "parry", "build"])

    def test_stop_words_excluded(self):
        """Stop words 제외 테스트."""
        from app.core.rag.retriever import VectorRetriever

        retriever = VectorRetriever(client=MagicMock())

        query = "How can I beat the boss?"
        keywords = retriever._extract_search_keywords(query)

        # Stop words는 제외
        keywords_lower = [kw.lower() for kw in keywords]
        assert "how" not in keywords_lower
        assert "can" not in keywords_lower
        assert "the" not in keywords_lower

    def test_max_keywords_limit(self):
        """최대 키워드 수 제한 테스트."""
        from app.core.rag.retriever import VectorRetriever

        retriever = VectorRetriever(client=MagicMock())

        query = "Malenia Radahn Morgott Godrick Rennala strategy guide tips"
        keywords = retriever._extract_search_keywords(query)

        # 최대 5개 키워드
        assert len(keywords) <= 5


class TestSourceDiversity:
    """출처 다양성 테스트."""

    def test_max_per_source_limit(self):
        """출처당 최대 청크 수 제한 테스트."""
        from app.core.rag.reranker import MultiStageReranker

        reranker = MultiStageReranker()

        chunks = [
            {"source_url": "http://wiki.com/malenia", "similarity": 0.95},
            {"source_url": "http://wiki.com/malenia", "similarity": 0.90},
            {"source_url": "http://wiki.com/malenia", "similarity": 0.85},  # 제외됨
            {"source_url": "http://reddit.com/post1", "similarity": 0.80},
            {"source_url": "http://reddit.com/post1", "similarity": 0.75},
        ]

        diverse = reranker.ensure_source_diversity(chunks, max_per_source=2)

        # wiki.com에서 2개, reddit.com에서 2개
        assert len(diverse) == 4

        # 각 출처별 개수 확인
        wiki_count = sum(1 for c in diverse if "wiki.com" in c["source_url"])
        reddit_count = sum(1 for c in diverse if "reddit.com" in c["source_url"])
        assert wiki_count == 2
        assert reddit_count == 2

    def test_url_normalization(self):
        """URL 정규화 (query/fragment 제거) 테스트."""
        from app.core.rag.reranker import MultiStageReranker

        reranker = MultiStageReranker()

        chunks = [
            {"source_url": "http://wiki.com/page?q=1", "similarity": 0.9},
            {"source_url": "http://wiki.com/page?q=2", "similarity": 0.85},
            {"source_url": "http://wiki.com/page#section", "similarity": 0.8},
        ]

        diverse = reranker.ensure_source_diversity(chunks, max_per_source=2)

        # 같은 페이지로 인식되어 2개만 반환
        assert len(diverse) == 2

    def test_empty_chunks(self):
        """빈 청크 리스트 테스트."""
        from app.core.rag.reranker import MultiStageReranker

        reranker = MultiStageReranker()

        diverse = reranker.ensure_source_diversity([], max_per_source=2)
        assert diverse == []

    def test_single_source(self):
        """단일 출처 테스트."""
        from app.core.rag.reranker import MultiStageReranker

        reranker = MultiStageReranker()

        chunks = [
            {"source_url": "http://wiki.com/page1", "similarity": 0.9},
            {"source_url": "http://wiki.com/page2", "similarity": 0.85},
            {"source_url": "http://wiki.com/page3", "similarity": 0.8},
        ]

        diverse = reranker.ensure_source_diversity(chunks, max_per_source=2)

        # 각 페이지가 다르므로 모두 포함
        assert len(diverse) == 3


class TestTranslatorFallback:
    """번역 폴백 테스트."""

    def test_fallback_with_dictionary(self):
        """엔티티 사전 기반 폴백 테스트."""
        from app.core.rag.translator import QueryTranslator

        with patch.object(QueryTranslator, "__init__", lambda x: None):
            translator = QueryTranslator()
            translator.client = None
            translator._cache = {}

            # 폴백 메서드 직접 테스트
            with patch(
                "app.core.rag.translator.get_entity_dictionary"
            ) as mock_get_dict:
                mock_dict = MagicMock()
                mock_dict.translate_to_english.return_value = "Malenia strategy"
                mock_get_dict.return_value = mock_dict

                result = translator._fallback_with_dictionary("말레니아 공략", "elden-ring")

                assert result == "Malenia strategy"
                mock_get_dict.assert_called_once_with("elden-ring", auto_expand=False)


class TestRerankerMultiStage:
    """MultiStageReranker 통합 테스트."""

    def test_rerank_with_source_diversity(self):
        """출처 다양성 포함 리랭킹 테스트."""
        from app.core.rag.reranker import MultiStageReranker

        reranker = MultiStageReranker()

        chunks = [
            {
                "source_url": "http://wiki.com/malenia",
                "similarity": 0.95,
                "quality_score": 0.8,
                "content": "Malenia phase 1 strategy",
                "title": "Malenia Guide",
            },
            {
                "source_url": "http://wiki.com/malenia",
                "similarity": 0.90,
                "quality_score": 0.7,
                "content": "Malenia phase 2 tips",
                "title": "Malenia Guide",
            },
            {
                "source_url": "http://wiki.com/malenia",
                "similarity": 0.85,
                "quality_score": 0.6,
                "content": "Malenia lore",
                "title": "Malenia Guide",
            },
            {
                "source_url": "http://reddit.com/post",
                "similarity": 0.80,
                "quality_score": 0.9,
                "content": "Community Malenia tips",
                "title": "Reddit Discussion",
            },
        ]

        result = reranker.rerank_multi_stage(
            chunks=chunks,
            question="말레니아 공략",
            entities=["Malenia"],
            keywords=["Malenia"],
            top_k=5,
            max_per_source=2,
        )

        # wiki.com에서 최대 2개만 포함
        wiki_count = sum(1 for c in result if "wiki.com" in c.get("source_url", ""))
        assert wiki_count <= 2

        # reddit 포함 확인
        reddit_count = sum(1 for c in result if "reddit.com" in c.get("source_url", ""))
        assert reddit_count >= 1
