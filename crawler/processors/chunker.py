"""Text Chunker for BossHelp Data Pipeline.

문서를 적절한 크기의 청크로 분할합니다.
"""

import re
from dataclasses import dataclass

import tiktoken

from crawler.models import ScoredDocument, Chunk, SourceType


@dataclass
class ChunkConfig:
    """청킹 설정."""
    max_tokens: int = 500
    overlap_tokens: int = 100
    min_tokens: int = 50


class TextChunker:
    """텍스트 청킹 프로세서."""

    def __init__(self, config: ChunkConfig | None = None):
        self.config = config or ChunkConfig()
        # text-embedding-3-small과 호환되는 인코더
        self.encoder = tiktoken.get_encoding("cl100k_base")

    def chunk(self, doc: ScoredDocument) -> list[Chunk]:
        """
        문서를 청크로 분할.

        전략:
        - Wiki: 섹션(h2/h3) 기준 분할
        - Reddit: 단락 기준 분할
        - 큰 섹션은 토큰 기준으로 추가 분할
        """
        if doc.source_type == SourceType.WIKI:
            chunks = self._chunk_by_section(doc)
        else:
            chunks = self._chunk_by_paragraph(doc)

        # 빈 청크 필터링
        chunks = [c for c in chunks if len(c.content.strip()) > 0]

        # 청크 인덱스 설정
        total = len(chunks)
        for i, chunk in enumerate(chunks):
            chunk.chunk_index = i
            chunk.total_chunks = total

        return chunks

    def chunk_batch(self, docs: list[ScoredDocument]) -> list[Chunk]:
        """배치 청킹."""
        all_chunks: list[Chunk] = []
        for doc in docs:
            all_chunks.extend(self.chunk(doc))
        return all_chunks

    def _chunk_by_section(self, doc: ScoredDocument) -> list[Chunk]:
        """섹션 기준 분할 (Wiki용)."""
        # 섹션 헤더로 분할
        section_pattern = r"(?=^#{1,3}\s)"
        sections = re.split(section_pattern, doc.content, flags=re.MULTILINE)

        chunks: list[Chunk] = []
        current_section = ""

        for section in sections:
            section = section.strip()
            if not section:
                continue

            # 섹션 토큰 수 확인
            tokens = self._count_tokens(section)

            if tokens <= self.config.max_tokens:
                # 섹션이 적절한 크기면 그대로 사용
                chunks.append(self._create_chunk(doc, section, tokens))
            else:
                # 큰 섹션은 추가 분할
                sub_chunks = self._split_large_text(section)
                for sub_text in sub_chunks:
                    chunks.append(
                        self._create_chunk(doc, sub_text, self._count_tokens(sub_text))
                    )

        return chunks

    def _chunk_by_paragraph(self, doc: ScoredDocument) -> list[Chunk]:
        """단락 기준 분할 (Reddit용)."""
        # 빈 줄로 단락 구분
        paragraphs = re.split(r"\n\s*\n", doc.content)

        chunks: list[Chunk] = []
        current_chunk = ""
        current_tokens = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            para_tokens = self._count_tokens(para)

            # 단락이 너무 크면 분할
            if para_tokens > self.config.max_tokens:
                # 현재 청크 저장
                if current_chunk:
                    chunks.append(
                        self._create_chunk(doc, current_chunk, current_tokens)
                    )
                    current_chunk = ""
                    current_tokens = 0

                # 큰 단락 분할
                for sub_text in self._split_large_text(para):
                    chunks.append(
                        self._create_chunk(doc, sub_text, self._count_tokens(sub_text))
                    )
                continue

            # 현재 청크에 추가 가능한지 확인
            if current_tokens + para_tokens <= self.config.max_tokens:
                current_chunk += ("\n\n" if current_chunk else "") + para
                current_tokens += para_tokens
            else:
                # 현재 청크 저장하고 새 청크 시작
                if current_chunk:
                    chunks.append(
                        self._create_chunk(doc, current_chunk, current_tokens)
                    )
                current_chunk = para
                current_tokens = para_tokens

        # 마지막 청크 저장
        if current_chunk and current_tokens >= self.config.min_tokens:
            chunks.append(self._create_chunk(doc, current_chunk, current_tokens))

        return chunks

    def _split_large_text(self, text: str) -> list[str]:
        """큰 텍스트를 오버랩으로 분할."""
        tokens = self.encoder.encode(text)
        chunks: list[str] = []

        start = 0
        while start < len(tokens):
            end = min(start + self.config.max_tokens, len(tokens))
            chunk_tokens = tokens[start:end]
            chunk_text = self.encoder.decode(chunk_tokens)
            chunks.append(chunk_text)

            # 오버랩 적용
            start = end - self.config.overlap_tokens
            if start < 0:
                start = end

        return chunks

    def _count_tokens(self, text: str) -> int:
        """토큰 수 계산."""
        return len(self.encoder.encode(text))

    def _create_chunk(
        self, doc: ScoredDocument, content: str, token_count: int
    ) -> Chunk:
        """Chunk 객체 생성."""
        return Chunk(
            game_id=doc.game_id,
            source_type=doc.source_type,
            source_url=doc.source_url,
            title=doc.title,
            content=content,
            category=doc.category,
            spoiler_level=doc.spoiler_level,
            entity_tags=doc.entity_tags,
            quality_score=doc.quality_score,
            token_count=token_count,
        )
