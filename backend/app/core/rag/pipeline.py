"""RAG Pipeline for BossHelp."""

import time
from dataclasses import dataclass
from typing import Literal

from app.core.llm.embeddings import EmbeddingClient, get_embedding_client
from app.core.llm.claude import ClaudeClient, get_claude_client
from app.core.rag.retriever import VectorRetriever, get_vector_retriever
from app.core.rag.reranker import QualityReranker
from app.core.rag.prompt import PromptBuilder
from app.core.entity.dictionary import EntityDictionary, get_entity_dictionary


SpoilerLevel = Literal["none", "light", "heavy"]


@dataclass
class RAGResult:
    """Result from RAG pipeline."""

    answer: str
    sources: list[dict]
    chunk_ids: list[str]
    has_detail: bool
    is_early_data: bool
    latency_ms: int


class RAGPipeline:
    """
    Main RAG pipeline orchestrator.

    Flow:
    1. Query Processing (entity detection, translation)
    2. Embedding Generation
    3. Vector Search
    4. Reranking (quality + similarity)
    5. Prompt Construction
    6. LLM Response Generation
    """

    def __init__(
        self,
        embedding_client: EmbeddingClient | None = None,
        claude_client: ClaudeClient | None = None,
        retriever: VectorRetriever | None = None,
    ):
        self.embedding_client = embedding_client or get_embedding_client()
        self.claude_client = claude_client or get_claude_client()
        self.retriever = retriever or get_vector_retriever()
        self.reranker = QualityReranker()
        self.prompt_builder = PromptBuilder()

    def run(
        self,
        question: str,
        game_id: str,
        spoiler_level: SpoilerLevel = "none",
        category: str | None = None,
        expanded: bool = False,
    ) -> RAGResult:
        """
        Run the full RAG pipeline.

        Args:
            question: User's question
            game_id: Game ID (e.g., 'elden-ring')
            spoiler_level: Spoiler filter level
            category: Optional category filter
            expanded: Whether to generate expanded answer

        Returns:
            RAGResult with answer, sources, and metadata
        """
        start_time = time.time()

        # 1. Query Processing
        entity_dict = get_entity_dictionary(game_id)
        entities = entity_dict.extract_entities(question)
        queries = entity_dict.expand_query(question)

        # 2. Generate Embedding (use English version if available)
        query_for_embedding = queries[-1] if len(queries) > 1 else queries[0]
        embedding = self.embedding_client.embed_query(
            query_for_embedding, game_id, category
        )

        # 3. Vector Search
        chunks = self.retriever.search(
            embedding=embedding,
            game_id=game_id,
            spoiler_level=spoiler_level,
            category=category,
            limit=10,
        )

        # 4. Reranking
        if chunks:
            # Apply entity boost
            chunks = self.reranker.apply_entity_boost(chunks, entities)
            # Deduplicate
            chunks = self.reranker.deduplicate(chunks)
            # Rerank by combined score
            chunks = self.reranker.rerank(chunks, top_k=5)

        # 5. Build Prompt
        system_prompt = self.prompt_builder.build_system_prompt(spoiler_level)

        if chunks:
            user_message = self.prompt_builder.build_user_message(
                question, chunks, expanded
            )
        else:
            user_message = self.prompt_builder.build_no_results_message(question)

        # 6. Generate Answer
        answer = self.claude_client.generate_answer(
            system_prompt=system_prompt,
            user_message=user_message,
            expanded=expanded,
        )

        # Calculate latency
        latency_ms = int((time.time() - start_time) * 1000)

        # Build sources
        sources = []
        chunk_ids = []
        for chunk in chunks[:5]:
            sources.append({
                "url": chunk.get("source_url", ""),
                "title": chunk.get("title", ""),
                "source_type": chunk.get("source_type", "unknown"),
                "quality_score": chunk.get("quality_score", 0.5),
            })
            chunk_ids.append(str(chunk.get("id", "")))

        # Determine if more detail is available
        has_detail = len(chunks) > 0 and not expanded

        # Check if early data (game released within 30 days)
        is_early_data = False  # TODO: Check game release date

        return RAGResult(
            answer=answer,
            sources=sources,
            chunk_ids=chunk_ids,
            has_detail=has_detail,
            is_early_data=is_early_data,
            latency_ms=latency_ms,
        )


# Singleton instance
_pipeline_instance: RAGPipeline | None = None


def get_rag_pipeline() -> RAGPipeline:
    """Get RAGPipeline singleton."""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = RAGPipeline()
    return _pipeline_instance
