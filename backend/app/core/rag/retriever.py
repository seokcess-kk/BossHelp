"""Vector Retriever for BossHelp RAG."""

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
            response = self.client.rpc(
                "search_chunks",
                {
                    "query_embedding": embedding,
                    "match_threshold": threshold,
                    "match_count": limit,
                    "filter_game_id": game_id,
                    "filter_spoiler_levels": spoiler_levels,
                    "filter_category": category,
                },
            ).execute()

            return response.data or []
        except Exception as e:
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
