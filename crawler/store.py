"""Supabase Store for BossHelp Data Pipeline.

임베딩된 청크를 Supabase에 저장합니다.
"""

from datetime import datetime, timezone
from typing import Iterator

from supabase import create_client, Client

from crawler.config import get_pipeline_config
from crawler.models import EmbeddedChunk, CrawlResult, SourceType


class SupabaseStore:
    """Supabase 저장소."""

    def __init__(self):
        config = get_pipeline_config()
        self.client: Client = create_client(
            config.supabase_url,
            config.supabase_key,
        )

    def upsert_chunk(self, chunk: EmbeddedChunk) -> str | None:
        """
        청크 저장 (upsert).

        동일 source_url의 청크가 있으면 업데이트.
        Returns: 저장된 청크 ID
        """
        data = {
            "game_id": chunk.game_id,
            "source_type": chunk.source_type.value,
            "source_url": chunk.source_url,
            "title": chunk.title,
            "content": chunk.content,
            "category": chunk.category.value,
            "spoiler_level": chunk.spoiler_level.value,
            "entity_tags": chunk.entity_tags,
            "quality_score": chunk.quality_score,
            "embedding": chunk.embedding,
            "is_active": True,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        try:
            result = (
                self.client.table("chunks")
                .upsert(data, on_conflict="source_url")
                .execute()
            )
            if result.data:
                return result.data[0].get("id")
        except Exception as e:
            print(f"Upsert error: {e}")

        return None

    def upsert_batch(
        self,
        chunks: Iterator[EmbeddedChunk] | list[EmbeddedChunk],
        batch_size: int = 50,
    ) -> int:
        """
        배치 저장.

        Returns: 저장된 청크 수
        """
        saved_count = 0
        batch: list[dict] = []

        for chunk in chunks:
            data = {
                "game_id": chunk.game_id,
                "source_type": chunk.source_type.value,
                "source_url": f"{chunk.source_url}#chunk{chunk.chunk_index}",
                "title": chunk.title,
                "content": chunk.content,
                "category": chunk.category.value,
                "spoiler_level": chunk.spoiler_level.value,
                "entity_tags": chunk.entity_tags,
                "quality_score": chunk.quality_score,
                "embedding": chunk.embedding,
                "is_active": True,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            batch.append(data)

            if len(batch) >= batch_size:
                saved_count += self._flush_batch(batch)
                batch = []

        # 남은 배치 저장
        if batch:
            saved_count += self._flush_batch(batch)

        return saved_count

    def _flush_batch(self, batch: list[dict]) -> int:
        """배치 플러시."""
        try:
            result = (
                self.client.table("chunks")
                .upsert(batch, on_conflict="source_url")
                .execute()
            )
            return len(result.data) if result.data else 0
        except Exception as e:
            print(f"Batch upsert error: {e}")
            # 개별 저장 시도
            saved = 0
            for item in batch:
                try:
                    self.client.table("chunks").upsert(
                        item, on_conflict="source_url"
                    ).execute()
                    saved += 1
                except Exception:
                    continue
            return saved

    def log_crawl(self, result: CrawlResult) -> str | None:
        """크롤링 로그 저장."""
        data = {
            "game_id": result.game_id,
            "source_type": result.source_type.value,
            "status": result.status,
            "pages_crawled": result.pages_crawled,
            "chunks_created": result.chunks_created,
            "error_message": result.error_message,
            "started_at": result.started_at.isoformat(),
            "completed_at": (
                result.completed_at.isoformat()
                if result.completed_at
                else None
            ),
        }

        try:
            result_data = (
                self.client.table("crawl_logs").insert(data).execute()
            )
            if result_data.data:
                return result_data.data[0].get("id")
        except Exception as e:
            print(f"Log error: {e}")

        return None

    def get_chunk_count(self, game_id: str | None = None) -> int:
        """청크 수 조회."""
        query = self.client.table("chunks").select("id", count="exact")

        if game_id:
            query = query.eq("game_id", game_id)

        result = query.eq("is_active", True).execute()
        return result.count or 0

    def deactivate_old_chunks(
        self,
        game_id: str,
        source_type: SourceType,
        before: datetime,
    ) -> int:
        """오래된 청크 비활성화."""
        try:
            result = (
                self.client.table("chunks")
                .update({"is_active": False})
                .eq("game_id", game_id)
                .eq("source_type", source_type.value)
                .lt("updated_at", before.isoformat())
                .execute()
            )
            return len(result.data) if result.data else 0
        except Exception as e:
            print(f"Deactivate error: {e}")
            return 0
