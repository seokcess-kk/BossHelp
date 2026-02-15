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
