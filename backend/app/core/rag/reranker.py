"""Quality-based Reranker for BossHelp RAG."""


class QualityReranker:
    """Rerank retrieved chunks based on similarity and quality score."""

    def __init__(
        self,
        similarity_weight: float = 0.7,
        quality_weight: float = 0.3,
    ):
        """
        Initialize reranker with weights.

        Args:
            similarity_weight: Weight for cosine similarity (default 0.7)
            quality_weight: Weight for quality score (default 0.3)
        """
        self.similarity_weight = similarity_weight
        self.quality_weight = quality_weight

    def rerank(
        self,
        chunks: list[dict],
        top_k: int = 5,
        min_score: float = 0.3,
    ) -> list[dict]:
        """
        Rerank chunks based on combined score.

        Formula: final_score = similarity * 0.7 + quality_score * 0.3

        Args:
            chunks: List of chunks with similarity scores
            top_k: Number of top chunks to return
            min_score: Minimum combined score threshold

        Returns:
            Reranked and filtered list of chunks
        """
        scored_chunks = []

        for chunk in chunks:
            similarity = chunk.get("similarity", 0.5)
            quality_score = chunk.get("quality_score", 0.5)

            # Calculate combined score
            combined_score = (
                self.similarity_weight * similarity +
                self.quality_weight * quality_score
            )

            if combined_score >= min_score:
                chunk["combined_score"] = combined_score
                scored_chunks.append(chunk)

        # Sort by combined score (descending)
        scored_chunks.sort(key=lambda x: x.get("combined_score", 0), reverse=True)

        # Return top_k chunks
        return scored_chunks[:top_k]

    def deduplicate(self, chunks: list[dict], threshold: float = 0.9) -> list[dict]:
        """
        Remove near-duplicate chunks based on content similarity.

        Args:
            chunks: List of chunks to deduplicate
            threshold: Similarity threshold for considering duplicates

        Returns:
            Deduplicated list of chunks
        """
        if not chunks:
            return []

        unique_chunks = [chunks[0]]

        for chunk in chunks[1:]:
            is_duplicate = False
            chunk_content = chunk.get("content", "").lower()

            for unique_chunk in unique_chunks:
                unique_content = unique_chunk.get("content", "").lower()

                # Simple overlap check
                overlap = self._calculate_overlap(chunk_content, unique_content)
                if overlap > threshold:
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique_chunks.append(chunk)

        return unique_chunks

    @staticmethod
    def _calculate_overlap(text1: str, text2: str) -> float:
        """Calculate word overlap ratio between two texts."""
        words1 = set(text1.split())
        words2 = set(text2.split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def apply_entity_boost(
        self,
        chunks: list[dict],
        entities: list[str],
        boost_factor: float = 1.2,
    ) -> list[dict]:
        """
        Boost scores for chunks that mention specific entities.

        Args:
            chunks: List of chunks to boost
            entities: List of entity names to match
            boost_factor: Multiplier for matching chunks

        Returns:
            Chunks with boosted scores
        """
        if not entities:
            return chunks

        entities_lower = [e.lower() for e in entities]

        for chunk in chunks:
            content = chunk.get("content", "").lower()
            entity_tags = [t.lower() for t in chunk.get("entity_tags", [])]

            # Check if any entity is mentioned
            matches = sum(
                1 for entity in entities_lower
                if entity in content or entity in entity_tags
            )

            if matches > 0:
                current_score = chunk.get("combined_score", 0.5)
                chunk["combined_score"] = min(1.0, current_score * boost_factor)

        # Re-sort after boosting
        chunks.sort(key=lambda x: x.get("combined_score", 0), reverse=True)
        return chunks


class MultiStageReranker(QualityReranker):
    """Multi-stage reranking with category boost and diversity."""

    # 질문 유형별 카테고리 패턴
    CATEGORY_PATTERNS: dict[str, list[str]] = {
        "boss_guide": [
            "공략", "패턴", "이기", "잡", "처치", "쓰러뜨리", "물리치",
            "guide", "strategy", "beat", "defeat", "kill", "how to",
        ],
        "item_location": [
            "위치", "어디", "획득", "얻", "찾",
            "location", "where", "find", "get", "obtain",
        ],
        "build_guide": [
            "빌드", "스탯", "무기", "방어구", "추천",
            "build", "stat", "weapon", "armor", "equipment",
        ],
        "npc_quest": [
            "퀘스트", "NPC", "엔딩", "루트", "선택",
            "quest", "ending", "storyline", "route", "choice",
        ],
        "mechanic_tip": [
            "시스템", "메카닉", "팁", "방법", "하는 법",
            "mechanic", "system", "tip", "how", "tutorial",
        ],
    }

    def detect_question_type(self, question: str) -> str | None:
        """
        Detect question type from query text.

        Args:
            question: User's question

        Returns:
            Detected category or None
        """
        question_lower = question.lower()

        for category, patterns in self.CATEGORY_PATTERNS.items():
            if any(p in question_lower for p in patterns):
                return category
        return None

    def apply_category_boost(
        self,
        chunks: list[dict],
        question: str,
        boost_factor: float = 1.3,
    ) -> list[dict]:
        """
        Boost chunks matching detected question category.

        Args:
            chunks: List of chunks to boost
            question: User's question for type detection
            boost_factor: Multiplier for matching chunks

        Returns:
            Chunks with category boost applied
        """
        detected_category = self.detect_question_type(question)

        if not detected_category:
            return chunks

        for chunk in chunks:
            chunk_category = chunk.get("category", "")
            if chunk_category == detected_category:
                current_score = chunk.get("combined_score", 0.5)
                chunk["combined_score"] = min(1.0, current_score * boost_factor)
                chunk["category_boosted"] = True

        # Re-sort after boosting
        chunks.sort(key=lambda x: x.get("combined_score", 0), reverse=True)
        return chunks

    def apply_keyword_boost(
        self,
        chunks: list[dict],
        keywords: list[str],
        boost_factor: float = 1.15,
    ) -> list[dict]:
        """
        Boost chunks containing exact keyword matches.

        Args:
            chunks: List of chunks to boost
            keywords: Keywords to match (from query)
            boost_factor: Multiplier for matching chunks

        Returns:
            Chunks with keyword boost applied
        """
        if not keywords:
            return chunks

        keywords_lower = [k.lower() for k in keywords]

        for chunk in chunks:
            content = chunk.get("content", "").lower()
            title = chunk.get("title", "").lower()

            # Count keyword matches
            matches = sum(
                1 for kw in keywords_lower
                if kw in content or kw in title
            )

            if matches > 0:
                current_score = chunk.get("combined_score", 0.5)
                # Progressive boost for more matches
                boost = boost_factor ** min(matches, 3)
                chunk["combined_score"] = min(1.0, current_score * boost)
                chunk["keyword_matches"] = matches

        # Re-sort after boosting
        chunks.sort(key=lambda x: x.get("combined_score", 0), reverse=True)
        return chunks

    def rerank_multi_stage(
        self,
        chunks: list[dict],
        question: str,
        entities: list[str],
        keywords: list[str] | None = None,
        top_k: int = 5,
        min_quality: float = 0.4,
    ) -> list[dict]:
        """
        Multi-stage reranking pipeline.

        Stage 1: Initial combined score calculation
        Stage 2: Entity boost
        Stage 3: Keyword boost
        Stage 4: Category boost
        Stage 5: Quality filter
        Stage 6: Deduplication
        Stage 7: Final ranking

        Args:
            chunks: List of chunks to rerank
            question: User's question
            entities: Detected entities
            keywords: Optional keywords for boost
            top_k: Number of top chunks to return
            min_quality: Minimum quality score threshold

        Returns:
            Reranked list of chunks
        """
        if not chunks:
            return []

        # Stage 1: Calculate initial combined scores
        for chunk in chunks:
            similarity = chunk.get("similarity", 0.5)
            quality_score = chunk.get("quality_score", 0.5)
            chunk["combined_score"] = (
                self.similarity_weight * similarity +
                self.quality_weight * quality_score
            )

        # Stage 2: Entity boost
        chunks = self.apply_entity_boost(chunks, entities)

        # Stage 3: Keyword boost (if provided)
        if keywords:
            chunks = self.apply_keyword_boost(chunks, keywords)

        # Stage 4: Category boost
        chunks = self.apply_category_boost(chunks, question)

        # Stage 5: Quality filter
        chunks = [c for c in chunks if c.get("quality_score", 0) >= min_quality]

        # Stage 6: Deduplication
        chunks = self.deduplicate(chunks)

        # Stage 7: Final ranking (already sorted, just slice)
        return chunks[:top_k]


# 기본 리랭커 (하위 호환성)
def get_reranker(multi_stage: bool = True) -> QualityReranker | MultiStageReranker:
    """
    Get reranker instance.

    Args:
        multi_stage: Whether to use multi-stage reranker

    Returns:
        Reranker instance
    """
    if multi_stage:
        return MultiStageReranker()
    return QualityReranker()
