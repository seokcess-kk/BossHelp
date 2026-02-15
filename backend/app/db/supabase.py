from supabase import create_client, Client
from functools import lru_cache
from app.config import get_settings


@lru_cache()
def get_supabase_client() -> Client:
    """Get Supabase client singleton."""
    settings = get_settings()
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)


class SupabaseDB:
    """Supabase database operations."""

    def __init__(self):
        self.client = get_supabase_client()

    # ==================== Games ====================
    async def get_games(self, active_only: bool = True):
        """Get all games."""
        query = self.client.table("games").select("*")
        if active_only:
            query = query.eq("is_active", True)
        response = query.execute()
        return response.data

    async def get_game(self, game_id: str):
        """Get a single game by ID."""
        response = (
            self.client.table("games")
            .select("*")
            .eq("id", game_id)
            .single()
            .execute()
        )
        return response.data

    # ==================== Chunks ====================
    async def search_chunks(
        self,
        game_id: str,
        embedding: list[float],
        spoiler_level: str = "none",
        category: str | None = None,
        limit: int = 10,
    ):
        """Search chunks using vector similarity."""
        # Build the RPC call for vector search
        params = {
            "query_embedding": embedding,
            "match_threshold": 0.5,
            "match_count": limit,
            "filter_game_id": game_id,
            "filter_spoiler_level": spoiler_level,
        }

        if category:
            params["filter_category"] = category

        # Using Supabase RPC for vector search
        # This requires a custom function in Supabase
        response = self.client.rpc("search_chunks", params).execute()
        return response.data

    async def get_chunks_by_ids(self, chunk_ids: list[str]):
        """Get chunks by IDs."""
        response = (
            self.client.table("chunks")
            .select("*")
            .in_("id", chunk_ids)
            .execute()
        )
        return response.data

    # ==================== Conversations ====================
    async def create_conversation(
        self,
        session_id: str,
        game_id: str,
        question: str,
        answer: str,
        chunk_ids: list[str],
        spoiler_level: str,
        latency_ms: int,
    ):
        """Create a conversation log."""
        response = (
            self.client.table("conversations")
            .insert({
                "session_id": session_id,
                "game_id": game_id,
                "question": question,
                "answer": answer,
                "chunk_ids": chunk_ids,
                "spoiler_level": spoiler_level,
                "latency_ms": latency_ms,
            })
            .execute()
        )
        return response.data[0] if response.data else None

    async def update_feedback(self, conversation_id: str, is_helpful: bool):
        """Update conversation feedback."""
        response = (
            self.client.table("conversations")
            .update({"is_helpful": is_helpful})
            .eq("id", conversation_id)
            .execute()
        )
        return response.data[0] if response.data else None

    async def get_popular_questions(self, game_id: str, limit: int = 10):
        """Get popular questions for a game."""
        # This would require aggregation - simplified version
        response = (
            self.client.table("conversations")
            .select("question, category:chunks(category)")
            .eq("game_id", game_id)
            .limit(limit)
            .execute()
        )
        return response.data


# Singleton instance
db = SupabaseDB()
