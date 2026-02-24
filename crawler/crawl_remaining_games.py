#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
나머지 게임 데이터 수집 스크립트 (Reddit JSON + Wiki)
- Elden Ring, Sekiro, Hollow Knight, Lies of P, Dark Souls 2, Dark Souls 3
"""

import os
import sys
import argparse
from pathlib import Path

# Windows 콘솔 UTF-8 설정 및 버퍼링 해제
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# 출력 버퍼링 해제
_original_print = print
def print(*args, **kwargs):
    kwargs.setdefault("flush", True)
    _original_print(*args, **kwargs)

# 프로젝트 경로 설정
project_root = Path(__file__).parent.parent
crawler_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(crawler_root))
sys.path.insert(0, str(project_root / "backend"))

from dotenv import load_dotenv
load_dotenv(project_root / "backend" / ".env")

from datetime import datetime, timezone
from crawlers.reddit_json import RedditJsonCrawler
from crawlers.wiki import WikiCrawler
from processors.cleaner import TextCleaner
from processors.classifier import CategoryClassifier
from processors.quality import QualityScorer
from processors.chunker import TextChunker
from processors.embedder import EmbeddingGenerator
from store import SupabaseStore

# 수집 대상 게임 (우선순위 순) - Reddit 500개로 증가
GAMES_CONFIG = {
    "elden-ring": {
        "name": "Elden Ring",
        "reddit_limit": 500,  # 200 → 500
        "wiki_limit": 50,  # 카테고리당
    },
    "dark-souls-3": {
        "name": "Dark Souls III",
        "reddit_limit": 500,  # 200 → 500
        "wiki_limit": 40,
    },
    "sekiro": {
        "name": "Sekiro: Shadows Die Twice",
        "reddit_limit": 500,  # 200 → 500
        "wiki_limit": 40,
    },
    "dark-souls-2": {
        "name": "Dark Souls II",
        "reddit_limit": 500,  # 200 → 500
        "wiki_limit": 40,
    },
    "dark-souls": {
        "name": "Dark Souls",
        "reddit_limit": 500,  # 신규 추가
        "wiki_limit": 40,
    },
    "lies-of-p": {
        "name": "Lies of P",
        "reddit_limit": 500,  # 200 → 500
        "wiki_limit": 40,
    },
    "hollow-knight": {
        "name": "Hollow Knight (+ Silksong)",  # Silksong 통합
        "reddit_limit": 500,  # 200 → 500, Silksong 포함
        "wiki_limit": 40,
    },
    # "silksong" 제거 → hollow-knight로 통합
}

# 공통 서브레딧 설정
COMMON_SUBREDDITS_CONFIG = {
    "fromsoftware": {"limit": 300},
    "soulslike": {"limit": 300},
    "shittydarksouls": {"limit": 300},
}


def crawl_common_subreddits():
    """
    공통 서브레딧 크롤링 (r/fromsoftware, r/soulslike, r/shittydarksouls).
    제목 기반으로 게임을 자동 분류합니다.
    """
    print(f"\n{'='*60}")
    print("  Common Subreddits (Auto-Classification)")
    print(f"{'='*60}")

    # 컴포넌트 초기화
    reddit_crawler = RedditJsonCrawler()
    cleaner = TextCleaner()
    classifier = CategoryClassifier()
    quality_scorer = QualityScorer()
    chunker = TextChunker()
    embedder = EmbeddingGenerator()
    store = SupabaseStore()

    all_docs = []

    for subreddit, config in COMMON_SUBREDDITS_CONFIG.items():
        print(f"\n[Common] r/{subreddit} (limit: {config['limit']})...")
        try:
            for doc in reddit_crawler.crawl_common_subreddit(subreddit, limit=config["limit"]):
                all_docs.append(doc)
        except Exception as e:
            print(f"  ✗ Error: {e}")

    if not all_docs:
        print(f"\n[SKIP] No documents collected from common subreddits")
        return {
            "source": "common_subreddits",
            "total_docs": 0,
            "chunks": 0,
            "status": "no_data",
            "by_game": {}
        }

    # 게임별 통계
    by_game = {}
    for doc in all_docs:
        by_game[doc.game_id] = by_game.get(doc.game_id, 0) + 1

    print(f"\n[Processing] Total documents: {len(all_docs)}")
    print(f"  By game: {by_game}")

    # Clean
    print("  - Cleaning...")
    cleaned = cleaner.clean_batch(all_docs)
    print(f"    Cleaned: {len(cleaned)}")

    # Classify
    print("  - Classifying...")
    classified = classifier.classify_batch(cleaned)

    # Quality Score
    print("  - Scoring quality...")
    scored = quality_scorer.score_batch(classified)
    scored = [d for d in scored if d.quality_score >= 0.3]
    print(f"    After quality filter: {len(scored)}")

    # Chunk
    print("  - Chunking...")
    chunks = chunker.chunk_batch(scored)
    print(f"    Chunks created: {len(chunks)}")

    # Embed & Store
    saved = 0
    if chunks:
        print("  - Embedding and storing...")
        embedded_chunks = list(embedder.embed_batch(chunks, show_progress=False))
        saved = store.upsert_batch(embedded_chunks)
        print(f"    ✓ Saved: {saved} chunks")

    return {
        "source": "common_subreddits",
        "total_docs": len(all_docs),
        "chunks": saved,
        "status": "success" if saved > 0 else "no_chunks",
        "by_game": by_game
    }


def crawl_game(game_id: str, skip_reddit: bool = False, skip_wiki: bool = False):
    """단일 게임 크롤링."""
    config = GAMES_CONFIG.get(game_id)
    if not config:
        print(f"[ERROR] Unknown game: {game_id}")
        return None

    print(f"\n{'='*60}")
    print(f"  {config['name']} ({game_id})")
    print(f"{'='*60}")

    # 컴포넌트 초기화
    reddit_crawler = RedditJsonCrawler()
    wiki_crawler = WikiCrawler()
    cleaner = TextCleaner()
    classifier = CategoryClassifier()
    quality_scorer = QualityScorer()
    chunker = TextChunker()
    embedder = EmbeddingGenerator()
    store = SupabaseStore()

    reddit_docs = []
    wiki_docs = []

    # 1. Reddit 수집
    if not skip_reddit and config["reddit_limit"] > 0:
        print(f"\n[1/2] Reddit crawling (limit: {config['reddit_limit']})...")
        try:
            for doc in reddit_crawler.crawl_initial(game_id, limit=config["reddit_limit"]):
                reddit_docs.append(doc)
            print(f"  ✓ Collected: {len(reddit_docs)} posts")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    else:
        print(f"\n[1/2] Reddit crawling... SKIPPED")

    # 2. Wiki 수집
    if not skip_wiki and config["wiki_limit"] > 0:
        print(f"\n[2/2] Wiki crawling (limit per category: {config['wiki_limit']})...")
        try:
            for doc in wiki_crawler.crawl_all(game_id, limit_per_category=config["wiki_limit"]):
                wiki_docs.append(doc)
            print(f"  ✓ Collected: {len(wiki_docs)} pages")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    else:
        print(f"\n[2/2] Wiki crawling... SKIPPED")

    # 3. 문서 처리
    all_docs = reddit_docs + wiki_docs
    if not all_docs:
        print(f"\n[SKIP] No documents collected for {game_id}")
        return {
            "game_id": game_id,
            "reddit": 0,
            "wiki": 0,
            "chunks": 0,
            "status": "no_data"
        }

    print(f"\n[Processing] Total documents: {len(all_docs)}")

    # Clean
    print("  - Cleaning...")
    cleaned = cleaner.clean_batch(all_docs)
    print(f"    Cleaned: {len(cleaned)}")

    # Classify
    print("  - Classifying...")
    classified = classifier.classify_batch(cleaned)

    # Quality Score
    print("  - Scoring quality...")
    scored = quality_scorer.score_batch(classified)
    scored = [d for d in scored if d.quality_score >= 0.3]
    print(f"    After quality filter: {len(scored)}")

    # Chunk
    print("  - Chunking...")
    chunks = chunker.chunk_batch(scored)
    print(f"    Chunks created: {len(chunks)}")

    # Embed & Store
    saved = 0
    if chunks:
        print("  - Embedding and storing...")
        embedded_chunks = list(embedder.embed_batch(chunks, show_progress=False))
        saved = store.upsert_batch(embedded_chunks)
        print(f"    ✓ Saved: {saved} chunks")

    return {
        "game_id": game_id,
        "reddit": len(reddit_docs),
        "wiki": len(wiki_docs),
        "chunks": saved,
        "status": "success" if saved > 0 else "no_chunks"
    }


def main():
    parser = argparse.ArgumentParser(description="Crawl remaining games data")
    parser.add_argument(
        "--games",
        nargs="+",
        choices=list(GAMES_CONFIG.keys()) + ["all"],
        default=["all"],
        help="Games to crawl (default: all)"
    )
    parser.add_argument(
        "--skip-reddit",
        action="store_true",
        help="Skip Reddit crawling"
    )
    parser.add_argument(
        "--skip-wiki",
        action="store_true",
        help="Skip Wiki crawling"
    )
    parser.add_argument(
        "--include-common",
        action="store_true",
        help="Include common subreddits (r/fromsoftware, r/soulslike, r/shittydarksouls)"
    )
    parser.add_argument(
        "--common-only",
        action="store_true",
        help="Only crawl common subreddits"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  BossHelp Data Collection")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = []
    total_chunks = 0

    # 공통 서브레딧만 크롤링
    if args.common_only:
        print("Mode: Common subreddits only")
        common_result = crawl_common_subreddits()
        if common_result:
            results.append(common_result)
            total_chunks += common_result["chunks"]
    else:
        # 게임 목록 결정
        if "all" in args.games:
            games = list(GAMES_CONFIG.keys())
        else:
            games = args.games

        print(f"Games: {', '.join(games)}")
        print(f"Skip Reddit: {args.skip_reddit}")
        print(f"Skip Wiki: {args.skip_wiki}")
        print(f"Include Common: {args.include_common}")

        # 게임별 크롤링
        for game_id in games:
            result = crawl_game(
                game_id,
                skip_reddit=args.skip_reddit,
                skip_wiki=args.skip_wiki
            )
            if result:
                results.append(result)
                total_chunks += result["chunks"]

        # 공통 서브레딧 크롤링 (옵션)
        if args.include_common:
            common_result = crawl_common_subreddits()
            if common_result:
                results.append(common_result)
                total_chunks += common_result["chunks"]

    # 결과 출력
    print("\n" + "=" * 60)
    print("  Collection Results")
    print("=" * 60)

    for r in results:
        status = "✓" if r["status"] == "success" else "✗"
        if r.get("source") == "common_subreddits":
            print(f"{status} Common Subreddits:")
            print(f"    Total: {r['total_docs']} docs → Chunks: {r['chunks']}")
            print(f"    By game: {r['by_game']}")
        else:
            print(f"{status} {r['game_id']}:")
            print(f"    Reddit: {r['reddit']}, Wiki: {r['wiki']} → Chunks: {r['chunks']}")

    print(f"\n{'='*60}")
    print(f"Total chunks saved: {total_chunks}")
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)


if __name__ == "__main__":
    main()
