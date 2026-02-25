"""Vector Retriever for BossHelp RAG."""

import json
import logging
import re
from supabase import Client
from functools import lru_cache
from app.db.supabase import get_supabase_client

logger = logging.getLogger(__name__)

# 게임 특화 용어 (검색 키워드로 중요)
GAME_TERMS = {
    "phase", "build", "dodge", "parry", "roll", "guard", "counter",
    "attack", "combo", "pattern", "strategy", "guide", "weakness",
    "buff", "debuff", "status", "damage", "heal", "stamina", "posture",
    "weapon", "armor", "item", "spell", "skill", "ability",
}


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
        query: str = "",
        entities: list[str] | None = None,
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
            query: Original query text
            entities: Extracted entities for filtering (NEW)

        Returns:
            List of matching chunks with similarity scores
        """
        # Map spoiler level to allowed levels
        spoiler_levels = self._get_allowed_spoiler_levels(spoiler_level)

        # NEW: 엔티티 기반 1차 필터링 시도
        if entities:
            logger.info(f"[Retriever] Entity-based pre-filtering: {entities}")
            pre_filtered = self._filter_by_entities(
                game_id=game_id,
                entities=entities,
                spoiler_levels=spoiler_levels,
                limit=500,
            )

            if pre_filtered:
                logger.info(f"[Retriever] Pre-filtered {len(pre_filtered)} chunks by entities")
                # 엔티티 필터링된 청크에서 벡터 검색
                chunks = self._search_within_chunks(
                    embedding=embedding,
                    chunks=pre_filtered,
                    limit=limit,
                )
                # 엔티티 부스트 적용
                chunks = self._apply_entity_boost(chunks, entities)
                return chunks

        # Build RPC call for vector search
        # This requires a Supabase function: search_chunks
        try:
            # 다중 키워드 추출
            search_keywords = self._extract_search_keywords(query)
            search_keyword = search_keywords[0] if search_keywords else None

            logger.info(f"[Retriever] RPC call: game={game_id}, spoiler_levels={spoiler_levels}, search_text={search_keyword}")

            response = self.client.rpc(
                "search_chunks",
                {
                    "query_embedding": embedding,
                    "match_threshold": 0.0,  # threshold 제거, 텍스트 검색 우선
                    "match_count": limit,
                    "filter_game_id": game_id,
                    "filter_spoiler_levels": spoiler_levels,
                    "filter_category": category,
                    "search_text": search_keyword,
                },
            ).execute()

            logger.info(f"[Retriever] RPC result count: {len(response.data) if response.data else 0}")

            if response.data:
                return response.data

            # 텍스트 검색 결과가 없으면 텍스트 없이 재시도
            logger.info("[Retriever] No results with text search, trying without")
            response = self.client.rpc(
                "search_chunks",
                {
                    "query_embedding": embedding,
                    "match_threshold": 0.3,
                    "match_count": limit,
                    "filter_game_id": game_id,
                    "filter_spoiler_levels": spoiler_levels,
                    "filter_category": category,
                    "search_text": None,
                },
            ).execute()

            logger.info(f"[Retriever] RPC retry result count: {len(response.data) if response.data else 0}")
            return response.data or []

        except Exception as e:
            logger.warning(f"[Retriever] RPC failed: {e}, using fallback")
            # Fallback to direct query if RPC not available
            return self._fallback_search(
                embedding, game_id, spoiler_levels, category, limit
            )

    def _extract_search_keywords(self, query: str) -> list[str]:
        """쿼리에서 복수 검색 키워드 추출.

        추출 우선순위:
        1. 대문자로 시작하는 단어 (엔티티명)
        2. 숫자 포함 단어 (phase 2, 1st floor 등)
        3. 게임 특화 용어 (build, dodge, parry 등)

        Args:
            query: 검색 쿼리

        Returns:
            검색 키워드 리스트 (중요도 순)
        """
        if not query:
            return []

        # 구두점 제거 (하이픈은 유지)
        clean_query = re.sub(r'[^\w\s\-]', '', query)
        words = clean_query.split()

        # Stop words (의문사, 관사 등)
        stop_words = {
            "how", "what", "where", "when", "why", "can", "does", "do",
            "the", "this", "that", "are", "is", "could", "would", "should",
            "for", "with", "and", "or", "but", "in", "on", "at", "to",
            "a", "an", "i", "my", "me", "best", "good", "way",
        }

        keywords = []

        # 1. 대문자로 시작하는 단어 (엔티티명 가능성 높음)
        for word in words:
            if len(word) >= 2 and word[0].isupper() and word.lower() not in stop_words:
                keywords.append(word)

        # 2. 숫자 포함 단어 (phase 2, 1st 등)
        for word in words:
            if any(c.isdigit() for c in word) and len(word) >= 2:
                if word not in keywords:
                    keywords.append(word)

        # 숫자 + 단어 조합 패턴 (예: "phase 2", "stage 1")
        phase_pattern = re.findall(r'(phase|stage|floor|level|part)\s*(\d+)', query, re.IGNORECASE)
        for match in phase_pattern:
            combined = f"{match[0]} {match[1]}"
            if combined not in keywords:
                keywords.append(combined)

        # 3. 게임 특화 용어
        for word in words:
            word_lower = word.lower()
            if word_lower in GAME_TERMS and word not in keywords:
                keywords.append(word)

        # 4. 나머지 의미 있는 단어 (3글자 이상, stop word 제외)
        for word in words:
            if len(word) >= 3 and word.lower() not in stop_words and word not in keywords:
                keywords.append(word)

        return keywords[:5]  # 최대 5개 키워드 반환

    def _get_allowed_spoiler_levels(self, spoiler_level: str) -> list[str]:
        """Get list of allowed spoiler levels."""
        levels = {
            "none": ["none"],
            "light": ["none", "light"],
            "heavy": ["none", "light", "heavy"],
        }
        return levels.get(spoiler_level, ["none"])

    def _boost_by_keywords(self, chunks: list[dict], query: str) -> list[dict]:
        """키워드 매칭으로 관련 청크 우선순위 부여."""
        # 다중 키워드 추출 (중요도 순)
        keywords = [kw.lower() for kw in self._extract_search_keywords(query)]
        logger.debug(f"[Retriever] Boosting by keywords: {keywords}")

        for chunk in chunks:
            title = (chunk.get("title") or "").lower()
            content = (chunk.get("content") or "").lower()
            text = title + " " + content

            # 키워드 매칭 점수
            match_count = sum(1 for kw in keywords if kw in text)
            title_match = sum(1 for kw in keywords if kw in title)

            # 기존 similarity에 보너스 추가
            similarity = chunk.get("similarity", 0.5)
            boost = (match_count * 0.1) + (title_match * 0.2)
            chunk["similarity"] = min(1.0, similarity + boost)
            chunk["keyword_matches"] = match_count

        # 다시 정렬
        chunks.sort(key=lambda x: x.get("similarity", 0), reverse=True)
        return chunks

    def _filter_by_entities(
        self,
        game_id: str,
        entities: list[str],
        spoiler_levels: list[str],
        limit: int = 500,
    ) -> list[dict]:
        """
        엔티티 기반 1차 필터링.

        우선순위:
        1. primary_entity 일치 (해당 엔티티 전용 페이지)
        2. entity_tags 포함 (해당 엔티티 언급된 페이지)

        Args:
            game_id: 게임 ID
            entities: 검색할 엔티티 목록
            spoiler_levels: 허용 스포일러 레벨
            limit: 최대 반환 수

        Returns:
            필터링된 청크 목록
        """
        results = []
        existing_ids: set[str] = set()

        for entity in entities:
            entity_lower = entity.lower()

            # 1. primary_entity 일치 (ILIKE)
            try:
                response = (
                    self.client.table("chunks")
                    .select("id", "title", "content", "category", "source_url",
                            "quality_score", "spoiler_level", "entity_tags",
                            "primary_entity", "entity_type")
                    .eq("game_id", game_id)
                    .eq("is_active", True)
                    .in_("spoiler_level", spoiler_levels)
                    .ilike("primary_entity", f"%{entity_lower}%")
                    .limit(100)
                    .execute()
                )

                for chunk in response.data or []:
                    if chunk["id"] not in existing_ids:
                        chunk["entity_match_type"] = "primary"
                        results.append(chunk)
                        existing_ids.add(chunk["id"])

            except Exception as e:
                logger.warning(f"[Retriever] primary_entity search failed: {e}")

            # 2. entity_tags 포함
            if len(results) < limit:
                try:
                    response = (
                        self.client.table("chunks")
                        .select("id", "title", "content", "category", "source_url",
                                "quality_score", "spoiler_level", "entity_tags",
                                "primary_entity", "entity_type")
                        .eq("game_id", game_id)
                        .eq("is_active", True)
                        .in_("spoiler_level", spoiler_levels)
                        .contains("entity_tags", [entity_lower])
                        .limit(100)
                        .execute()
                    )

                    for chunk in response.data or []:
                        if chunk["id"] not in existing_ids:
                            chunk["entity_match_type"] = "tags"
                            results.append(chunk)
                            existing_ids.add(chunk["id"])

                except Exception as e:
                    logger.warning(f"[Retriever] entity_tags search failed: {e}")

            if len(results) >= limit:
                break

        logger.info(f"[Retriever] Entity filter found {len(results)} chunks")
        return results[:limit]

    def _search_within_chunks(
        self,
        embedding: list[float],
        chunks: list[dict],
        limit: int = 10,
    ) -> list[dict]:
        """
        주어진 청크 목록 내에서 벡터 유사도 계산.

        Note: embedding 필드가 없는 경우 기본 점수 적용.

        Args:
            embedding: 쿼리 임베딩
            chunks: 검색 대상 청크 목록
            limit: 반환할 최대 개수

        Returns:
            유사도 정렬된 청크 목록
        """
        # 청크에 embedding이 없으면 DB에서 다시 조회
        chunk_ids = [c["id"] for c in chunks]

        if chunk_ids:
            try:
                # embedding 포함하여 다시 조회
                response = (
                    self.client.table("chunks")
                    .select("*")
                    .in_("id", chunk_ids[:100])  # 최대 100개
                    .execute()
                )

                if response.data:
                    chunks_with_embedding = {c["id"]: c for c in response.data}

                    for chunk in chunks:
                        if chunk["id"] in chunks_with_embedding:
                            full_chunk = chunks_with_embedding[chunk["id"]]
                            if full_chunk.get("embedding"):
                                # DB에서 가져온 embedding이 문자열이면 파싱
                                chunk_embedding = full_chunk["embedding"]
                                if isinstance(chunk_embedding, str):
                                    chunk_embedding = json.loads(chunk_embedding)
                                similarity = self._cosine_similarity(
                                    embedding, chunk_embedding
                                )
                                chunk["similarity"] = similarity
                                chunk["embedding"] = chunk_embedding
                            else:
                                # embedding 없으면 entity match 기반 점수
                                chunk["similarity"] = (
                                    0.6 if chunk.get("entity_match_type") == "primary" else 0.4
                                )
            except Exception as e:
                logger.warning(f"[Retriever] Failed to fetch embeddings: {e}")
                # 폴백: entity match 기반 점수
                for chunk in chunks:
                    chunk["similarity"] = (
                        0.6 if chunk.get("entity_match_type") == "primary" else 0.4
                    )

        # 유사도로 정렬
        chunks.sort(key=lambda x: x.get("similarity", 0), reverse=True)
        return chunks[:limit]

    def _apply_entity_boost(
        self,
        chunks: list[dict],
        entities: list[str],
    ) -> list[dict]:
        """
        엔티티 매칭 기반 점수 부스트.

        primary_entity 일치 시 더 높은 부스트 적용.

        Args:
            chunks: 청크 목록
            entities: 검색 엔티티 목록

        Returns:
            부스트 적용된 청크 목록
        """
        for chunk in chunks:
            primary_entity = (chunk.get("primary_entity") or "").lower()
            entity_tags = [t.lower() for t in chunk.get("entity_tags", [])]

            boost = 0.0

            for entity in entities:
                entity_lower = entity.lower()

                # primary_entity 일치: +0.25
                if entity_lower in primary_entity or primary_entity in entity_lower:
                    boost += 0.25
                    chunk["primary_entity_match"] = True
                # entity_tags 포함: +0.1
                elif entity_lower in entity_tags:
                    boost += 0.1

            current_similarity = chunk.get("similarity", 0.5)
            chunk["similarity"] = min(1.0, current_similarity + boost)
            chunk["entity_boost"] = boost

        # 다시 정렬
        chunks.sort(key=lambda x: x.get("similarity", 0), reverse=True)
        return chunks

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
                # DB에서 가져온 embedding이 문자열이면 파싱
                chunk_embedding = chunk["embedding"]
                if isinstance(chunk_embedding, str):
                    chunk_embedding = json.loads(chunk_embedding)
                similarity = self._cosine_similarity(embedding, chunk_embedding)
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
