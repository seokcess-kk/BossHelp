"""RAG Pipeline for BossHelp."""

import time
from dataclasses import dataclass, asdict
from typing import Literal, Iterator, Any

from app.core.llm.embeddings import EmbeddingClient, get_embedding_client
from app.core.llm.claude import ClaudeClient, get_claude_client
from app.core.rag.retriever import VectorRetriever, get_vector_retriever
from app.core.rag.reranker import MultiStageReranker
from app.core.rag.prompt import PromptBuilder, calculate_answer_confidence, ConfidenceLevel
from app.core.rag.translator import QueryTranslator, get_query_translator
from app.core.entity.dictionary import EntityDictionary, get_entity_dictionary
from app.core.cache import get_query_cache, get_embedding_cache


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
    confidence: ConfidenceLevel = "medium"
    cached: bool = False


class RAGPipeline:
    """
    Main RAG pipeline orchestrator.

    Flow:
    1. Cache Check (optional)
    2. Query Processing (entity detection, translation)
    3. Embedding Generation (with cache)
    4. Vector Search
    5. Multi-Stage Reranking
    6. Prompt Construction
    7. LLM Response Generation (sync or streaming)
    """

    def __init__(
        self,
        embedding_client: EmbeddingClient | None = None,
        claude_client: ClaudeClient | None = None,
        retriever: VectorRetriever | None = None,
        translator: QueryTranslator | None = None,
        enable_cache: bool = True,
    ):
        self.embedding_client = embedding_client or get_embedding_client()
        self.claude_client = claude_client or get_claude_client()
        self.retriever = retriever or get_vector_retriever()
        self.translator = translator or get_query_translator()
        self.reranker = MultiStageReranker()
        self.prompt_builder = PromptBuilder(version="v2")

        # Caching
        self.enable_cache = enable_cache
        self._query_cache = get_query_cache() if enable_cache else None
        self._embedding_cache = get_embedding_cache() if enable_cache else None

    def _get_embedding_with_cache(
        self,
        query: str,
        game_id: str,
        category: str | None = None,
    ) -> list[float]:
        """Get embedding with optional caching."""
        # Try cache first
        if self._embedding_cache:
            cached = self._embedding_cache.get(query, game_id)
            if cached is not None:
                return cached

        # Generate embedding
        embedding = self.embedding_client.embed_query(query, game_id, category)

        # Cache the result
        if self._embedding_cache:
            self._embedding_cache.set(query, game_id, embedding)

        return embedding

    def prepare_context(
        self,
        question: str,
        game_id: str,
        spoiler_level: SpoilerLevel = "none",
        category: str | None = None,
    ) -> dict[str, Any]:
        """
        Prepare context for answer generation (without LLM call).

        Used for streaming to send sources before generating answer.

        Returns:
            Dict with chunks, confidence, latency_ms, entities
        """
        start_time = time.time()

        # 1. Query Translation (한글 → 영어)
        translated_query = self.translator.translate(question, game_id)

        # 2. Query Processing (엔티티 추출)
        entity_dict = get_entity_dictionary(game_id)
        entities = entity_dict.extract_entities(translated_query)
        queries = entity_dict.expand_query(translated_query)

        # 3. Generate Embedding (with cache)
        query_for_embedding = queries[-1] if len(queries) > 1 else queries[0]
        embedding = self._get_embedding_with_cache(
            query_for_embedding, game_id, category
        )

        # 4. Vector Search
        chunks = self.retriever.search(
            embedding=embedding,
            game_id=game_id,
            spoiler_level=spoiler_level,
            category=category,
            limit=20,  # Fetch more for multi-stage reranking
            query=translated_query,
        )

        # 5. Multi-Stage Reranking
        if chunks:
            # Extract keywords from translated query
            keywords = [w for w in translated_query.split() if len(w) > 2]
            chunks = self.reranker.rerank_multi_stage(
                chunks=chunks,
                question=question,
                entities=entities,
                keywords=keywords,
                top_k=5,
            )

        # Calculate confidence
        confidence = calculate_answer_confidence(chunks)

        # Calculate latency (context preparation only)
        latency_ms = int((time.time() - start_time) * 1000)

        return {
            "chunks": chunks,
            "confidence": confidence,
            "latency_ms": latency_ms,
            "entities": entities,
            "translated_query": translated_query,
        }

    def run_stream(
        self,
        question: str,
        game_id: str,
        spoiler_level: SpoilerLevel = "none",
        chunks: list[dict] | None = None,
        expanded: bool = False,
    ) -> Iterator[str]:
        """
        Run RAG pipeline with streaming response.

        Args:
            question: User's question
            game_id: Game ID
            spoiler_level: Spoiler filter level
            chunks: Pre-fetched chunks (from prepare_context)
            expanded: Whether to generate expanded answer

        Yields:
            Text chunks as they are generated
        """
        # If chunks not provided, prepare context first
        if chunks is None:
            context = self.prepare_context(question, game_id, spoiler_level)
            chunks = context["chunks"]

        # Build prompt
        system_prompt = self.prompt_builder.build_system_prompt(spoiler_level)

        if chunks:
            user_message = self.prompt_builder.build_user_message(
                question, chunks, expanded
            )
        else:
            user_message = self.prompt_builder.build_no_results_message(question)

        # Stream answer
        yield from self.claude_client.generate_answer_stream(
            system_prompt=system_prompt,
            user_message=user_message,
            expanded=expanded,
        )

    def run(
        self,
        question: str,
        game_id: str,
        spoiler_level: SpoilerLevel = "none",
        category: str | None = None,
        expanded: bool = False,
    ) -> RAGResult:
        """
        Run the full RAG pipeline (synchronous).

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

        # Check query cache first
        if self._query_cache:
            cached = self._query_cache.get(question, game_id, spoiler_level)
            if cached is not None:
                return RAGResult(
                    answer=cached["answer"],
                    sources=cached["sources"],
                    chunk_ids=cached["chunk_ids"],
                    has_detail=cached["has_detail"],
                    is_early_data=cached["is_early_data"],
                    latency_ms=int((time.time() - start_time) * 1000),
                    confidence=cached.get("confidence", "medium"),
                    cached=True,
                )

        # Prepare context
        context = self.prepare_context(question, game_id, spoiler_level, category)
        chunks = context["chunks"]
        confidence = context["confidence"]

        # Build prompt
        system_prompt = self.prompt_builder.build_system_prompt(spoiler_level)

        if chunks:
            user_message = self.prompt_builder.build_user_message(
                question, chunks, expanded
            )
        else:
            user_message = self.prompt_builder.build_no_results_message(question)

        # Generate answer (sync)
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

        result = RAGResult(
            answer=answer,
            sources=sources,
            chunk_ids=chunk_ids,
            has_detail=has_detail,
            is_early_data=is_early_data,
            latency_ms=latency_ms,
            confidence=confidence,
            cached=False,
        )

        # Cache the result (only for non-expanded queries)
        if self._query_cache and not expanded:
            self._query_cache.set(
                question,
                game_id,
                spoiler_level,
                {
                    "answer": answer,
                    "sources": sources,
                    "chunk_ids": chunk_ids,
                    "has_detail": has_detail,
                    "is_early_data": is_early_data,
                    "confidence": confidence,
                },
            )

        return result


# Singleton instance
_pipeline_instance: RAGPipeline | None = None


def get_rag_pipeline() -> RAGPipeline:
    """Get RAGPipeline singleton."""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = RAGPipeline()
    return _pipeline_instance
