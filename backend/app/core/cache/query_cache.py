"""Query result cache for BossHelp RAG pipeline."""

import hashlib
from cachetools import TTLCache
from typing import Any


class QueryCache:
    """TTL-based query result cache."""

    def __init__(self, maxsize: int = 1000, ttl: int = 3600):
        """
        Initialize query cache.

        Args:
            maxsize: Maximum number of cached entries
            ttl: Time-to-live in seconds (default: 1 hour)
        """
        self._cache: TTLCache = TTLCache(maxsize=maxsize, ttl=ttl)
        self._hits = 0
        self._misses = 0

    def _make_key(self, question: str, game_id: str, spoiler_level: str) -> str:
        """Generate cache key from query parameters."""
        content = f"{question.lower().strip()}:{game_id}:{spoiler_level}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def get(self, question: str, game_id: str, spoiler_level: str) -> dict | None:
        """
        Get cached result if exists.

        Args:
            question: User's question
            game_id: Game identifier
            spoiler_level: Spoiler level setting

        Returns:
            Cached result dict or None if not found
        """
        key = self._make_key(question, game_id, spoiler_level)
        result = self._cache.get(key)

        if result is not None:
            self._hits += 1
        else:
            self._misses += 1

        return result

    def set(
        self,
        question: str,
        game_id: str,
        spoiler_level: str,
        result: dict[str, Any],
    ) -> None:
        """
        Cache query result.

        Args:
            question: User's question
            game_id: Game identifier
            spoiler_level: Spoiler level setting
            result: Result dict to cache
        """
        key = self._make_key(question, game_id, spoiler_level)
        self._cache[key] = result

    def invalidate_all(self) -> None:
        """Clear all cached entries."""
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
            "maxsize": self._cache.maxsize,
        }


# Singleton instance
_query_cache: QueryCache | None = None


def get_query_cache() -> QueryCache:
    """Get QueryCache singleton."""
    global _query_cache
    if _query_cache is None:
        _query_cache = QueryCache()
    return _query_cache
