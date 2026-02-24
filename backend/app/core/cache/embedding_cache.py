"""Embedding cache for BossHelp RAG pipeline."""

import hashlib
from collections import OrderedDict


class EmbeddingCache:
    """LRU cache for query embeddings."""

    def __init__(self, maxsize: int = 1000):
        """
        Initialize embedding cache.

        Args:
            maxsize: Maximum number of cached embeddings
        """
        self.maxsize = maxsize
        self._cache: OrderedDict[str, list[float]] = OrderedDict()
        self._hits = 0
        self._misses = 0

    def _make_key(self, query: str, game_id: str) -> str:
        """Generate cache key from query and game_id."""
        content = f"{query.lower().strip()}:{game_id}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def get(self, query: str, game_id: str) -> list[float] | None:
        """
        Get cached embedding if exists.

        Args:
            query: Search query
            game_id: Game identifier

        Returns:
            Cached embedding vector or None if not found
        """
        key = self._make_key(query, game_id)

        if key in self._cache:
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            self._hits += 1
            return self._cache[key]

        self._misses += 1
        return None

    def set(self, query: str, game_id: str, embedding: list[float]) -> None:
        """
        Cache embedding vector.

        Args:
            query: Search query
            game_id: Game identifier
            embedding: Embedding vector to cache
        """
        key = self._make_key(query, game_id)

        if key in self._cache:
            # Update existing and move to end
            self._cache.move_to_end(key)
            self._cache[key] = embedding
        else:
            # Add new entry
            if len(self._cache) >= self.maxsize:
                # Remove oldest (first) entry
                self._cache.popitem(last=False)
            self._cache[key] = embedding

    def invalidate_all(self) -> None:
        """Clear all cached embeddings."""
        self._cache.clear()

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0

    @property
    def stats(self) -> dict:
        """Get cache statistics."""
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{self.hit_rate:.1%}",
            "size": len(self._cache),
            "maxsize": self.maxsize,
        }


# Singleton instance
_embedding_cache: EmbeddingCache | None = None


def get_embedding_cache() -> EmbeddingCache:
    """Get EmbeddingCache singleton."""
    global _embedding_cache
    if _embedding_cache is None:
        _embedding_cache = EmbeddingCache()
    return _embedding_cache
