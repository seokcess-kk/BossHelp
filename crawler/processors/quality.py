"""Quality Scorer for BossHelp Data Pipeline.

문서의 품질 점수를 계산합니다 (0~1).
"""

from datetime import datetime, timezone
from crawler.models import ClassifiedDocument, ScoredDocument, SourceType, Category


class QualityScorer:
    """품질 점수 계산기."""

    # 카테고리별 가중치
    CATEGORY_WEIGHTS: dict[Category, float] = {
        Category.BOSS_GUIDE: 1.0,
        Category.BUILD_GUIDE: 0.9,
        Category.PROGRESSION_ROUTE: 0.95,
        Category.NPC_QUEST: 0.85,
        Category.ITEM_LOCATION: 0.8,
        Category.MECHANIC_TIP: 0.85,
        Category.SECRET_HIDDEN: 0.75,
    }

    def score(self, doc: ClassifiedDocument) -> ScoredDocument:
        """
        품질 점수 계산.

        Reddit:
            - upvote_norm: upvotes / 200 (max 1.0)
            - recency: 1 - days_old / 365 (min 0.1)
            - category_weight: 카테고리별 가중치

        Wiki:
            - content_length: word_count / 1000 (max 1.0)
            - category_weight: 카테고리별 가중치
            - recency: 1 - days_old / 365 (min 0.1)
        """
        if doc.source_type == SourceType.REDDIT:
            quality_score = self._score_reddit(doc)
        elif doc.source_type == SourceType.WIKI:
            quality_score = self._score_wiki(doc)
        else:
            quality_score = 0.5

        # 분류 신뢰도 반영
        quality_score *= (0.7 + 0.3 * doc.category_confidence)

        # 범위 제한
        quality_score = max(0.1, min(1.0, quality_score))

        return ScoredDocument(
            game_id=doc.game_id,
            source_type=doc.source_type,
            source_url=doc.source_url,
            title=doc.title,
            content=doc.content,
            category=doc.category,
            spoiler_level=doc.spoiler_level,
            entity_tags=doc.entity_tags,
            quality_score=quality_score,
            upvotes=doc.upvotes,
            created_at=doc.created_at,
        )

    def score_batch(
        self, docs: list[ClassifiedDocument]
    ) -> list[ScoredDocument]:
        """배치 품질 점수 계산."""
        return [self.score(doc) for doc in docs]

    def _score_reddit(self, doc: ClassifiedDocument) -> float:
        """Reddit 문서 품질 점수."""
        # Upvote 정규화 (200 upvotes = 1.0)
        upvote_norm = min(doc.upvotes / 200, 1.0)

        # 최신성 (1년 기준)
        recency = self._calculate_recency(doc.created_at)

        # 콘텐츠 길이 보너스 (적당한 길이가 좋음)
        word_count = len(doc.content.split())
        length_score = min(word_count / 500, 1.0) if word_count < 2000 else 0.8

        # 카테고리 가중치
        category_weight = self.CATEGORY_WEIGHTS.get(doc.category, 0.7)

        # 최종 점수
        score = (
            0.35 * upvote_norm +
            0.25 * recency +
            0.20 * length_score +
            0.20 * category_weight
        )

        return score

    def _score_wiki(self, doc: ClassifiedDocument) -> float:
        """Wiki 문서 품질 점수."""
        # 콘텐츠 완성도 (1000단어 기준)
        word_count = len(doc.content.split())
        completeness = min(word_count / 1000, 1.0)

        # 최신성
        recency = self._calculate_recency(doc.created_at)

        # 카테고리 가중치
        category_weight = self.CATEGORY_WEIGHTS.get(doc.category, 0.7)

        # 구조화 점수 (섹션 헤더 존재 여부)
        has_structure = 1.0 if "##" in doc.content or "###" in doc.content else 0.7

        # 최종 점수
        score = (
            0.30 * completeness +
            0.25 * recency +
            0.25 * category_weight +
            0.20 * has_structure
        )

        return score

    def _calculate_recency(self, created_at: datetime | None) -> float:
        """최신성 점수 계산 (0.1 ~ 1.0)."""
        if not created_at:
            return 0.5  # 날짜 불명시 중간값

        now = datetime.now(timezone.utc)
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)

        days_old = (now - created_at).days
        recency = max(1 - days_old / 365, 0.1)

        return recency
