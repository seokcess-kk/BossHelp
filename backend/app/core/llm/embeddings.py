"""OpenAI Embedding Client for BossHelp."""

from openai import OpenAI
from functools import lru_cache
from app.config import get_settings


class EmbeddingClient:
    """OpenAI text-embedding-3-small client."""

    MODEL = "text-embedding-3-small"
    DIMENSIONS = 1536

    def __init__(self):
        settings = get_settings()
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def embed(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        response = self.client.embeddings.create(
            model=self.MODEL,
            input=text,
            dimensions=self.DIMENSIONS,
        )
        return response.data[0].embedding

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        response = self.client.embeddings.create(
            model=self.MODEL,
            input=texts,
            dimensions=self.DIMENSIONS,
        )
        return [item.embedding for item in response.data]

    def embed_query(self, query: str, game_id: str, category: str | None = None) -> list[float]:
        """
        Generate embedding for a search query with metadata prefix.

        Format: "[category] [game] query"
        Example: "[boss_guide] [elden-ring] 말레니아 공략"
        """
        prefix_parts = []
        if category:
            prefix_parts.append(f"[{category}]")
        prefix_parts.append(f"[{game_id}]")

        enriched_query = " ".join(prefix_parts) + " " + query
        return self.embed(enriched_query)


@lru_cache()
def get_embedding_client() -> EmbeddingClient:
    """Get EmbeddingClient singleton."""
    return EmbeddingClient()
