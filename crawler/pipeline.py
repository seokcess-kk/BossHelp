"""Main Pipeline Orchestration for BossHelp Data Pipeline.

전체 데이터 처리 파이프라인을 관리합니다.
Crawl → Clean → Classify → Quality → Chunk → Embed → Store
"""

from datetime import datetime, timezone
from typing import Generator, Literal

from tqdm import tqdm

from crawler.config import get_game_config, get_pipeline_config, GAME_CONFIGS
from crawler.models import (
    RawDocument,
    EmbeddedChunk,
    CrawlResult,
    SourceType,
)
from crawler.crawlers import RedditCrawler, WikiCrawler
from crawler.processors import (
    TextCleaner,
    CategoryClassifier,
    QualityScorer,
    TextChunker,
    EmbeddingGenerator,
)
from crawler.store import SupabaseStore


class DataPipeline:
    """
    전체 데이터 처리 파이프라인.

    Crawl → Clean → Classify → Quality → Chunk → Embed → Store
    """

    def __init__(self):
        # Crawlers
        self.reddit_crawler = RedditCrawler()
        self.wiki_crawler = WikiCrawler()

        # Processors
        self.cleaner = TextCleaner()
        self.classifier = CategoryClassifier()
        self.quality_scorer = QualityScorer()
        self.chunker = TextChunker()
        self.embedder = EmbeddingGenerator()

        # Store
        self.store = SupabaseStore()

        # Config
        self.config = get_pipeline_config()

    def run_initial(
        self,
        game_ids: list[str] | None = None,
        sources: list[SourceType] | None = None,
        reddit_limit: int = 1000,
        wiki_limit_per_category: int = 100,
    ) -> dict[str, CrawlResult]:
        """
        초기 데이터 수집 파이프라인.

        Args:
            game_ids: 수집할 게임 ID 목록 (None이면 전체)
            sources: 수집할 소스 타입 (None이면 전체)
            reddit_limit: Reddit 수집 개수
            wiki_limit_per_category: Wiki 카테고리당 수집 개수

        Returns:
            게임별 수집 결과
        """
        if game_ids is None:
            game_ids = list(GAME_CONFIGS.keys())

        if sources is None:
            sources = [SourceType.REDDIT, SourceType.WIKI]

        results: dict[str, CrawlResult] = {}

        for game_id in game_ids:
            print(f"\n{'='*50}")
            print(f"Processing: {game_id}")
            print(f"{'='*50}")

            game_config = get_game_config(game_id)

            # Reddit 수집
            if SourceType.REDDIT in sources:
                print(f"\n[Reddit] Crawling r/{game_config.subreddit}...")
                result = self._process_reddit(game_id, "initial", reddit_limit)
                results[f"{game_id}_reddit"] = result
                print(f"[Reddit] Done: {result.chunks_created} chunks")

            # Wiki 수집
            if SourceType.WIKI in sources and game_config.wiki_base_url:
                print(f"\n[Wiki] Crawling {game_config.wiki_base_url}...")
                result = self._process_wiki(game_id, "all", wiki_limit_per_category)
                results[f"{game_id}_wiki"] = result
                print(f"[Wiki] Done: {result.chunks_created} chunks")

        return results

    def run_update(
        self,
        game_ids: list[str] | None = None,
        reddit_limit: int = 100,
    ) -> dict[str, CrawlResult]:
        """
        주기적 업데이트 파이프라인 (Reddit만).

        Args:
            game_ids: 업데이트할 게임 ID 목록
            reddit_limit: Reddit 수집 개수
        """
        if game_ids is None:
            game_ids = list(GAME_CONFIGS.keys())

        results: dict[str, CrawlResult] = {}

        for game_id in game_ids:
            result = self._process_reddit(game_id, "recent", reddit_limit)
            results[game_id] = result

        return results

    def process_documents(
        self,
        docs: list[RawDocument],
        show_progress: bool = True,
    ) -> tuple[int, int]:
        """
        문서 목록 처리.

        Args:
            docs: 처리할 문서 목록
            show_progress: 진행 표시 여부

        Returns:
            (처리된 문서 수, 저장된 청크 수)
        """
        if not docs:
            return 0, 0

        # 1. Clean
        cleaned = self.cleaner.clean_batch(docs)
        if show_progress:
            print(f"  Cleaned: {len(cleaned)}/{len(docs)}")

        # 2. Classify
        classified = self.classifier.classify_batch(cleaned)

        # 3. Quality Score
        scored = self.quality_scorer.score_batch(classified)

        # 품질 필터링
        scored = [
            doc for doc in scored
            if doc.quality_score >= self.config.min_quality_score
        ]
        if show_progress:
            print(f"  Quality filtered: {len(scored)}")

        # 4. Chunk
        chunks = self.chunker.chunk_batch(scored)
        if show_progress:
            print(f"  Chunks created: {len(chunks)}")

        # 5. Embed + Store
        embedded = self.embedder.embed_batch(chunks, show_progress=show_progress)

        if show_progress:
            embedded = tqdm(embedded, total=len(chunks), desc="  Embedding")

        saved_count = self.store.upsert_batch(embedded)

        return len(docs), saved_count

    def _process_reddit(
        self,
        game_id: str,
        mode: Literal["initial", "recent"],
        limit: int,
    ) -> CrawlResult:
        """Reddit 처리."""
        started_at = datetime.now(timezone.utc)
        docs: list[RawDocument] = []

        try:
            if mode == "initial":
                crawler_gen = self.reddit_crawler.crawl_initial(game_id, limit)
            else:
                crawler_gen = self.reddit_crawler.crawl_recent(game_id, limit)

            # 문서 수집
            for doc in crawler_gen:
                docs.append(doc)

            # 문서 처리
            _, chunks_created = self.process_documents(docs)

            return CrawlResult(
                game_id=game_id,
                source_type=SourceType.REDDIT,
                status="success",
                pages_crawled=len(docs),
                chunks_created=chunks_created,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
            )

        except Exception as e:
            return CrawlResult(
                game_id=game_id,
                source_type=SourceType.REDDIT,
                status="failed",
                pages_crawled=len(docs),
                error_message=str(e),
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
            )

    def _process_wiki(
        self,
        game_id: str,
        category: str | Literal["all"],
        limit: int,
    ) -> CrawlResult:
        """Wiki 처리."""
        started_at = datetime.now(timezone.utc)
        docs: list[RawDocument] = []

        try:
            if category == "all":
                crawler_gen = self.wiki_crawler.crawl_all(game_id, limit)
            else:
                crawler_gen = self.wiki_crawler.crawl_category(game_id, category, limit)

            # 문서 수집
            for doc in crawler_gen:
                docs.append(doc)

            # 문서 처리
            _, chunks_created = self.process_documents(docs)

            return CrawlResult(
                game_id=game_id,
                source_type=SourceType.WIKI,
                status="success",
                pages_crawled=len(docs),
                chunks_created=chunks_created,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
            )

        except Exception as e:
            return CrawlResult(
                game_id=game_id,
                source_type=SourceType.WIKI,
                status="failed",
                pages_crawled=len(docs),
                error_message=str(e),
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
            )


def get_pipeline() -> DataPipeline:
    """Get DataPipeline instance."""
    return DataPipeline()


# CLI Entry Point
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="BossHelp Data Pipeline")
    parser.add_argument(
        "--mode",
        choices=["initial", "update"],
        default="update",
        help="Pipeline mode",
    )
    parser.add_argument(
        "--games",
        nargs="+",
        default=None,
        help="Game IDs to process",
    )
    parser.add_argument(
        "--reddit-limit",
        type=int,
        default=100,
        help="Reddit crawl limit",
    )
    parser.add_argument(
        "--wiki-limit",
        type=int,
        default=50,
        help="Wiki crawl limit per category",
    )

    args = parser.parse_args()

    pipeline = get_pipeline()

    if args.mode == "initial":
        results = pipeline.run_initial(
            game_ids=args.games,
            reddit_limit=args.reddit_limit,
            wiki_limit_per_category=args.wiki_limit,
        )
    else:
        results = pipeline.run_update(
            game_ids=args.games,
            reddit_limit=args.reddit_limit,
        )

    # 결과 출력
    print("\n" + "=" * 50)
    print("Pipeline Results")
    print("=" * 50)
    for key, result in results.items():
        status_icon = "✅" if result.status == "success" else "❌"
        print(f"{status_icon} {key}: {result.chunks_created} chunks")
        if result.error_message:
            print(f"   Error: {result.error_message}")
