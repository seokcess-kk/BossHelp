"""Vector Retriever for BossHelp RAG."""

import json
from supabase import Client
from functools import lru_cache
from app.db.supabase import get_supabase_client


class VectorRetriever:
    """Retrieve relevant chunks using pgvector similarity search."""

    def __init__(self, client: Client | None = None):
        self.client = client or get_supabase_client()

    def search(
        self,
        embedding: list[float],
        game_id: str,
        spoiler_level: str = "none",
        category: str | None = None,
        limit: int = 10,
        threshold: float = 0.5,
        query: str = "",
    ) -> list[dict]:
        """
        Search for similar chunks using vector similarity.

        Args:
            embedding: Query embedding vector (1536 dimensions)
            game_id: Game ID to filter by
            spoiler_level: Maximum spoiler level ('none', 'light', 'heavy')
            category: Optional category filter
            limit: Maximum number of results
            threshold: Minimum similarity threshold

        Returns:
            List of matching chunks with similarity scores
        """
        # Map spoiler level to allowed levels
        spoiler_levels = self._get_allowed_spoiler_levels(spoiler_level)

        # Build RPC call for vector search
        # This requires a Supabase function: search_chunks
        try:
            # 쿼리에서 핵심 키워드 추출 (대문자 단어 우선, 없으면 가장 긴 단어)
            search_keyword = None
            if query:
                words = [w for w in query.split() if len(w) >= 3]
                # 대문자로 시작하는 단어 우선 (엔티티 이름일 가능성 높음)
                capitalized = [w for w in words if w[0].isupper() and w not in ("How", "What", "Where", "When", "Why", "Can", "Does", "The", "This")]
                if capitalized:
                    search_keyword = max(capitalized, key=len)
                elif words:
                    search_keyword = max(words, key=len)

            print(f"[Retriever] RPC call: game={game_id}, spoiler_levels={spoiler_levels}, search_text={search_keyword}")

            response = self.client.rpc(
                "search_chunks",
                {
                    "query_embedding": embedding,
                    "match_threshold": 0.0,  # threshold 제거, 텍스트 검색 우선
                    "match_count": limit,
                    "filter_game_id": game_id,
                    "filter_spoiler_levels": spoiler_levels,
                    "filter_category": category,
                    "search_text": search_keyword,
                },
            ).execute()

            print(f"[Retriever] RPC result count: {len(response.data) if response.data else 0}")

            if response.data:
                return response.data

            # 텍스트 검색 결과가 없으면 텍스트 없이 재시도
            print(f"[Retriever] No results with text search, trying without")
            response = self.client.rpc(
                "search_chunks",
                {
                    "query_embedding": embedding,
                    "match_threshold": 0.3,
                    "match_count": limit,
                    "filter_game_id": game_id,
                    "filter_spoiler_levels": spoiler_levels,
                    "filter_category": category,
                    "search_text": None,
                },
            ).execute()

            print(f"[Retriever] RPC retry result count: {len(response.data) if response.data else 0}")
            return response.data or []

        except Exception as e:
            print(f"[Retriever] RPC failed: {e}, using fallback")
            # Fallback to direct query if RPC not available
            return self._fallback_search(
                embedding, game_id, spoiler_levels, category, limit
            )

    def _get_allowed_spoiler_levels(self, spoiler_level: str) -> list[str]:
        """Get list of allowed spoiler levels."""
        levels = {
            "none": ["none"],
            "light": ["none", "light"],
            "heavy": ["none", "light", "heavy"],
        }
        return levels.get(spoiler_level, ["none"])

    def _boost_by_keywords(self, chunks: list[dict], query: str) -> list[dict]:
        """키워드 매칭으로 관련 청크 우선순위 부여."""
        # 쿼리에서 키워드 추출 (2글자 이상)
        keywords = [w.lower() for w in query.split() if len(w) >= 2]
        print(f"[Retriever] Boosting by keywords: {keywords}")

        for chunk in chunks:
            title = (chunk.get("title") or "").lower()
            content = (chunk.get("content") or "").lower()
            text = title + " " + content

            # 키워드 매칭 점수
            match_count = sum(1 for kw in keywords if kw in text)
            title_match = sum(1 for kw in keywords if kw in title)

            # 기존 similarity에 보너스 추가
            similarity = chunk.get("similarity", 0.5)
            boost = (match_count * 0.1) + (title_match * 0.2)
            chunk["similarity"] = min(1.0, similarity + boost)
            chunk["keyword_matches"] = match_count

            print(f"[Retriever] Chunk '{title[:30]}': sim={similarity:.3f}, boost={boost:.2f}, matches={match_count}")

        # 다시 정렬
        chunks.sort(key=lambda x: x.get("similarity", 0), reverse=True)
        return chunks

    def _fallback_search(
        self,
        embedding: list[float],
        game_id: str,
        spoiler_levels: list[str],
        category: str | None,
        limit: int,
    ) -> list[dict]:
        """
        Fallback search using direct query (less efficient).
        Used when RPC function is not available.
        """
        query = (
            self.client.table("chunks")
            .select("*")
            .eq("game_id", game_id)
            .eq("is_active", True)
            .in_("spoiler_level", spoiler_levels)
        )

        if category:
            query = query.eq("category", category)

        # Get all matching chunks (we'll sort client-side)
        response = query.limit(100).execute()

        if not response.data:
            return []

        # Calculate cosine similarity client-side (not ideal but works)
        chunks_with_scores = []
        for chunk in response.data:
            if chunk.get("embedding"):
                similarity = self._cosine_similarity(embedding, chunk["embedding"])
                chunk["similarity"] = similarity
                chunks_with_scores.append(chunk)

        # Sort by similarity and return top results
        chunks_with_scores.sort(key=lambda x: x.get("similarity", 0), reverse=True)
        return chunks_with_scores[:limit]

    @staticmethod
    def _cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)


@lru_cache()
def get_vector_retriever() -> VectorRetriever:
    """Get VectorRetriever singleton."""
    return VectorRetriever()
