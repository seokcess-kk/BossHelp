"""Embedding Generator for BossHelp Data Pipeline.

OpenAI text-embedding-3-small을 사용하여 임베딩을 생성합니다.
"""

import time
from typing import Iterator

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from crawler.config import get_pipeline_config
from crawler.models import Chunk, EmbeddedChunk


class EmbeddingGenerator:
    """임베딩 생성기."""

    def __init__(self):
        config = get_pipeline_config()
        self.client = OpenAI(api_key=config.openai_api_key)
        self.model = config.embedding_model
        self.batch_size = config.embedding_batch_size
        self.dimension = 1536  # text-embedding-3-small 차원

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
    )
    def embed(self, text: str, prefix: str = "") -> list[float]:
        """
        단일 텍스트 임베딩.

        Args:
            text: 임베딩할 텍스트
            prefix: 검색 효율을 위한 접두사 (카테고리, 게임 등)

        Returns:
            1536차원 임베딩 벡터
        """
        # 접두사 추가 (검색 품질 향상)
        if prefix:
            text = f"{prefix} {text}"

        response = self.client.embeddings.create(
            model=self.model,
            input=text,
            dimensions=self.dimension,
        )

        return response.data[0].embedding

    def embed_chunk(self, chunk: Chunk) -> EmbeddedChunk:
        """청크 임베딩."""
        # 검색 효율을 위한 접두사 생성
        prefix_parts = [
            f"[{chunk.category.value}]",
            f"[{chunk.game_id}]",
        ]
        if chunk.entity_tags:
            prefix_parts.append(f"[{', '.join(chunk.entity_tags[:3])}]")

        prefix = " ".join(prefix_parts)

        # 제목 + 내용 임베딩
        text = f"{chunk.title}\n\n{chunk.content}"
        embedding = self.embed(text, prefix)

        return EmbeddedChunk(
            game_id=chunk.game_id,
            source_type=chunk.source_type,
            source_url=chunk.source_url,
            title=chunk.title,
            content=chunk.content,
            category=chunk.category,
            spoiler_level=chunk.spoiler_level,
            entity_tags=chunk.entity_tags,
            quality_score=chunk.quality_score,
            embedding=embedding,
            chunk_index=chunk.chunk_index,
            total_chunks=chunk.total_chunks,
        )

    def embed_batch(
        self, chunks: list[Chunk], show_progress: bool = True
    ) -> Iterator[EmbeddedChunk]:
        """
        배치 임베딩 (제너레이터).

        메모리 효율을 위해 제너레이터로 구현.
        """
        total = len(chunks)

        for i in range(0, total, self.batch_size):
            batch = chunks[i:i + self.batch_size]

            # 배치 텍스트 준비
            texts = []
            for chunk in batch:
                prefix_parts = [
                    f"[{chunk.category.value}]",
                    f"[{chunk.game_id}]",
                ]
                if chunk.entity_tags:
                    prefix_parts.append(f"[{', '.join(chunk.entity_tags[:3])}]")
                prefix = " ".join(prefix_parts)
                text = f"{prefix} {chunk.title}\n\n{chunk.content}"
                texts.append(text)

            # 배치 API 호출
            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=texts,
                    dimensions=self.dimension,
                )

                # 결과 매핑
                for chunk, data in zip(batch, response.data):
                    yield EmbeddedChunk(
                        game_id=chunk.game_id,
                        source_type=chunk.source_type,
                        source_url=chunk.source_url,
                        title=chunk.title,
                        content=chunk.content,
                        category=chunk.category,
                        spoiler_level=chunk.spoiler_level,
                        entity_tags=chunk.entity_tags,
                        quality_score=chunk.quality_score,
                        embedding=data.embedding,
                        chunk_index=chunk.chunk_index,
                        total_chunks=chunk.total_chunks,
                    )

            except Exception as e:
                print(f"Batch embedding error: {e}")
                # 개별 임베딩으로 폴백
                for chunk in batch:
                    try:
                        yield self.embed_chunk(chunk)
                    except Exception as chunk_error:
                        print(f"Chunk embedding error: {chunk_error}")
                        continue

            # Rate limit 방지
            if i + self.batch_size < total:
                time.sleep(0.5)
