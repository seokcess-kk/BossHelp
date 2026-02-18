#!/usr/bin/env python3
"""Wiki-only crawling script for BossHelp.

Reddit API 없이 Wiki만 크롤링합니다.

Usage:
    python run_wiki.py                    # 모든 게임
    python run_wiki.py --games elden-ring # 특정 게임
    python run_wiki.py --limit 50         # 카테고리당 50개
"""

import argparse
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv
load_dotenv()

from crawler.config import GAME_CONFIGS, get_game_config, get_pipeline_config
from crawler.crawlers.wiki import WikiCrawler
from crawler.processors import (
    TextCleaner,
    CategoryClassifier,
    QualityScorer,
    TextChunker,
    EmbeddingGenerator,
)
from crawler.store import SupabaseStore
from crawler.models import RawDocument, SourceType


def run_wiki_pipeline(
    game_ids: list[str] | None = None,
    limit_per_category: int = 50,
    dry_run: bool = False,
):
    """Wiki 전용 파이프라인 실행."""

    if game_ids is None:
        # Silksong 제외 (Wiki 없음)
        game_ids = [gid for gid in GAME_CONFIGS.keys() if gid != "silksong"]

    # 컴포넌트 초기화
    wiki_crawler = WikiCrawler()
    cleaner = TextCleaner()
    classifier = CategoryClassifier()
    quality_scorer = QualityScorer()
    chunker = TextChunker()
    embedder = EmbeddingGenerator()
    store = SupabaseStore()
    config = get_pipeline_config()

    total_results = {}

    for game_id in game_ids:
        game_config = get_game_config(game_id)

        if not game_config.wiki_base_url:
            print(f"\n⏭️  {game_id}: Wiki URL 없음, 스킵")
            continue

        print(f"\n{'='*60}")
        print(f"🎮 {game_id.upper()}")
        print(f"📚 Wiki: {game_config.wiki_base_url}")
        print(f"{'='*60}")

        started_at = datetime.now(timezone.utc)
        docs: list[RawDocument] = []

        try:
            # 1. Wiki 크롤링
            print("\n📥 크롤링 중...")
            crawler_gen = wiki_crawler.crawl_all(game_id, limit_per_category)

            for doc in crawler_gen:
                docs.append(doc)
                if len(docs) % 10 == 0:
                    print(f"   수집: {len(docs)}개 문서")

            print(f"✅ 크롤링 완료: {len(docs)}개 문서")

            if dry_run:
                print("🔍 [Dry Run] 저장하지 않음")
                total_results[game_id] = {
                    "docs": len(docs),
                    "chunks": 0,
                    "status": "dry_run"
                }
                continue

            if not docs:
                print("⚠️  수집된 문서 없음")
                continue

            # 2. 정제
            print("\n🧹 텍스트 정제 중...")
            cleaned = cleaner.clean_batch(docs)
            print(f"   정제 완료: {len(cleaned)}개")

            # 3. 분류
            print("🏷️  카테고리 분류 중...")
            classified = classifier.classify_batch(cleaned)

            # 4. 품질 점수
            print("⭐ 품질 평가 중...")
            scored = quality_scorer.score_batch(classified)

            # 품질 필터링
            min_quality = config.min_quality_score
            filtered = [doc for doc in scored if doc.quality_score >= min_quality]
            print(f"   품질 필터 통과: {len(filtered)}/{len(scored)}개 (기준: {min_quality})")

            if not filtered:
                print("⚠️  품질 기준을 통과한 문서 없음")
                continue

            # 5. 청킹
            print("✂️  청크 분할 중...")
            chunks = chunker.chunk_batch(filtered)
            print(f"   청크 생성: {len(chunks)}개")

            # 6. 임베딩
            print("🧠 임베딩 생성 중...")
            embedded_chunks = list(embedder.embed_batch(chunks, show_progress=True))
            print(f"   임베딩 완료: {len(embedded_chunks)}개")

            # 7. 저장
            print("💾 Supabase 저장 중...")
            saved_count = store.upsert_batch(embedded_chunks)
            print(f"   저장 완료: {saved_count}개")

            elapsed = (datetime.now(timezone.utc) - started_at).total_seconds()

            total_results[game_id] = {
                "docs": len(docs),
                "filtered": len(filtered),
                "chunks": len(chunks),
                "saved": saved_count,
                "elapsed": f"{elapsed:.1f}s",
                "status": "success"
            }

        except Exception as e:
            print(f"❌ 에러: {e}")
            total_results[game_id] = {
                "docs": len(docs),
                "status": "failed",
                "error": str(e)
            }

    # 최종 결과 출력
    print("\n" + "="*60)
    print("📊 최종 결과")
    print("="*60)

    total_docs = 0
    total_chunks = 0

    for game_id, result in total_results.items():
        status_icon = "✅" if result.get("status") == "success" else "❌"
        docs_count = result.get("docs", 0)
        chunks_count = result.get("saved", result.get("chunks", 0))

        total_docs += docs_count
        total_chunks += chunks_count

        print(f"{status_icon} {game_id}: {docs_count} docs → {chunks_count} chunks")
        if result.get("error"):
            print(f"   └─ Error: {result['error']}")

    print("-"*60)
    print(f"📦 총합: {total_docs} docs → {total_chunks} chunks")

    return total_results


def main():
    parser = argparse.ArgumentParser(
        description="BossHelp Wiki Crawler",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python run_wiki.py                         # 모든 게임 크롤링
    python run_wiki.py --games elden-ring      # Elden Ring만
    python run_wiki.py --games elden-ring sekiro  # 여러 게임
    python run_wiki.py --limit 100             # 카테고리당 100개
    python run_wiki.py --dry-run               # 테스트 (저장 안함)
        """
    )

    parser.add_argument(
        "--games",
        nargs="+",
        default=None,
        help="크롤링할 게임 ID (기본: 전체)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="카테고리당 최대 페이지 수 (기본: 50)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="테스트 모드 (저장하지 않음)",
    )

    args = parser.parse_args()

    # 환경변수 체크
    import os
    required_vars = ["SUPABASE_URL", "SUPABASE_SERVICE_KEY", "OPENAI_API_KEY"]
    missing = [v for v in required_vars if not os.getenv(v)]

    if missing and not args.dry_run:
        print("❌ 필수 환경변수가 설정되지 않았습니다:")
        for var in missing:
            print(f"   - {var}")
        print("\ncrawler/.env 파일을 생성하거나 환경변수를 설정하세요.")
        sys.exit(1)

    run_wiki_pipeline(
        game_ids=args.games,
        limit_per_category=args.limit,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
