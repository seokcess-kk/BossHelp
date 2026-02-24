#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
나머지 게임 데이터 수집 스크립트 (Reddit JSON + Wiki)
- Elden Ring, Sekiro, Hollow Knight, Lies of P, Dark Souls 2, Dark Souls 3

수집 모드:
- initial: top all-time posts + 댓글 (초기 수집)
- daily: hot + new + 댓글 (일일 업데이트)
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

# 공통 서브레딧 설정 (limit 증가: 300→500)
COMMON_SUBREDDITS_CONFIG = {
    "fromsoftware": {"limit": 500},
    "soulslike": {"limit": 500},
    "shittydarksouls": {"limit": 500},
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


def crawl_game(game_id: str, skip_reddit: bool = False, skip_wiki: bool = False, include_comments: bool = False):
    """단일 게임 크롤링 (초기 수집 모드)."""
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
    comment_docs = []

    # 1. Reddit 수집
    if not skip_reddit and config["reddit_limit"] > 0:
        print(f"\n[1/3] Reddit posts (limit: {config['reddit_limit']})...")
        try:
            for doc in reddit_crawler.crawl_initial(game_id, limit=config["reddit_limit"]):
                reddit_docs.append(doc)
            print(f"  ✓ Collected: {len(reddit_docs)} posts")
        except Exception as e:
            print(f"  ✗ Error: {e}")

        # 1-2. 댓글 수집
        if include_comments:
            print(f"\n[1-2/3] Reddit comments (top 50 posts)...")
            try:
                for doc in reddit_crawler.crawl_comments(game_id, post_limit=50, comments_per_post=20):
                    comment_docs.append(doc)
                print(f"  ✓ Collected: {len(comment_docs)} comments")
            except Exception as e:
                print(f"  ✗ Error: {e}")
    else:
        print(f"\n[1/3] Reddit crawling... SKIPPED")

    # 2. Wiki 수집
    if not skip_wiki and config["wiki_limit"] > 0:
        print(f"\n[2/3] Wiki crawling (limit per category: {config['wiki_limit']})...")
        try:
            for doc in wiki_crawler.crawl_all(game_id, limit_per_category=config["wiki_limit"]):
                wiki_docs.append(doc)
            print(f"  ✓ Collected: {len(wiki_docs)} pages")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    else:
        print(f"\n[2/3] Wiki crawling... SKIPPED")

    # 3. 문서 처리
    all_docs = reddit_docs + comment_docs + wiki_docs
    if not all_docs:
        print(f"\n[SKIP] No documents collected for {game_id}")
        return {
            "game_id": game_id,
            "reddit": 0,
            "comments": 0,
            "wiki": 0,
            "chunks": 0,
            "status": "no_data"
        }

    print(f"\n[3/3] Processing {len(all_docs)} documents...")

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
        "comments": len(comment_docs),
        "wiki": len(wiki_docs),
        "chunks": saved,
        "status": "success" if saved > 0 else "no_chunks"
    }


def crawl_game_daily(game_id: str):
    """
    일일 업데이트 모드: hot + new + 댓글 수집.
    매일 실행하여 새로운 콘텐츠를 수집합니다.
    """
    config = GAMES_CONFIG.get(game_id)
    if not config:
        print(f"[ERROR] Unknown game: {game_id}")
        return None

    print(f"\n{'='*60}")
    print(f"  [DAILY] {config['name']} ({game_id})")
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
    stats = {"hot": 0, "new": 0, "comments": 0}

    try:
        # crawl_daily 메서드 사용
        print(f"\n[Daily Update] Crawling hot + new + comments...")
        for doc in reddit_crawler.crawl_daily(
            game_id,
            hot_limit=100,
            new_limit=50,
            include_comments=True,
            comments_post_limit=20
        ):
            all_docs.append(doc)

            # 통계 (제목으로 구분)
            if doc.title.startswith("[Comment]"):
                stats["comments"] += 1
            else:
                stats["hot"] += 1  # hot/new 구분 어려움

    except Exception as e:
        print(f"  ✗ Error: {e}")

    if not all_docs:
        print(f"\n[SKIP] No new documents for {game_id}")
        return {
            "game_id": game_id,
            "mode": "daily",
            "docs": 0,
            "chunks": 0,
            "status": "no_data"
        }

    print(f"\n[Processing] {len(all_docs)} documents...")

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
        "mode": "daily",
        "docs": len(all_docs),
        "comments": stats["comments"],
        "chunks": saved,
        "status": "success" if saved > 0 else "no_chunks"
    }


def crawl_comments_only(game_id: str, post_limit: int = 100):
    """
    댓글만 수집 (기존 인기 게시물의 댓글).
    """
    config = GAMES_CONFIG.get(game_id)
    if not config:
        print(f"[ERROR] Unknown game: {game_id}")
        return None

    print(f"\n{'='*60}")
    print(f"  [COMMENTS] {config['name']} ({game_id})")
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

    try:
        print(f"\n[Comments] Crawling from top {post_limit} posts...")
        for doc in reddit_crawler.crawl_comments(game_id, post_limit=post_limit, comments_per_post=20):
            all_docs.append(doc)
        print(f"  ✓ Collected: {len(all_docs)} comments")

    except Exception as e:
        print(f"  ✗ Error: {e}")

    if not all_docs:
        print(f"\n[SKIP] No comments collected for {game_id}")
        return {
            "game_id": game_id,
            "mode": "comments",
            "comments": 0,
            "chunks": 0,
            "status": "no_data"
        }

    print(f"\n[Processing] {len(all_docs)} comments...")

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
        "mode": "comments",
        "comments": len(all_docs),
        "chunks": saved,
        "status": "success" if saved > 0 else "no_chunks"
    }


def main():
    parser = argparse.ArgumentParser(
        description="BossHelp Data Collection (Reddit + Wiki)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
수집 모드:
  initial   초기 수집 (top all-time + 댓글 + Wiki)
  daily     일일 업데이트 (hot + new + 댓글)
  comments  댓글만 수집

예시:
  python crawl_remaining_games.py --mode initial --games all
  python crawl_remaining_games.py --mode daily --games elden-ring dark-souls-3
  python crawl_remaining_games.py --mode comments --games elden-ring
        """
    )
    parser.add_argument(
        "--mode",
        choices=["initial", "daily", "comments"],
        default="initial",
        help="수집 모드: initial (초기), daily (일일 업데이트), comments (댓글만)"
    )
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
        help="Skip Reddit posts (initial mode only)"
    )
    parser.add_argument(
        "--skip-wiki",
        action="store_true",
        help="Skip Wiki crawling (initial mode only)"
    )
    parser.add_argument(
        "--skip-comments",
        action="store_true",
        help="Skip comments crawling"
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
    parser.add_argument(
        "--comment-posts",
        type=int,
        default=50,
        help="Number of posts to crawl comments from (default: 50)"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  BossHelp Data Collection")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Mode: {args.mode.upper()}")

    results = []
    total_chunks = 0

    # 공통 서브레딧만 크롤링
    if args.common_only:
        print("Target: Common subreddits only")
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

        if args.mode == "initial":
            # ========== 초기 수집 모드 ==========
            print(f"Skip Reddit: {args.skip_reddit}")
            print(f"Skip Wiki: {args.skip_wiki}")
            print(f"Include Comments: {not args.skip_comments}")
            print(f"Include Common: {args.include_common}")

            for game_id in games:
                result = crawl_game(
                    game_id,
                    skip_reddit=args.skip_reddit,
                    skip_wiki=args.skip_wiki,
                    include_comments=not args.skip_comments
                )
                if result:
                    results.append(result)
                    total_chunks += result["chunks"]

        elif args.mode == "daily":
            # ========== 일일 업데이트 모드 ==========
            print("Collecting: hot + new + comments")

            for game_id in games:
                result = crawl_game_daily(game_id)
                if result:
                    results.append(result)
                    total_chunks += result["chunks"]

        elif args.mode == "comments":
            # ========== 댓글만 수집 모드 ==========
            print(f"Comment posts limit: {args.comment_posts}")

            for game_id in games:
                result = crawl_comments_only(game_id, post_limit=args.comment_posts)
                if result:
                    results.append(result)
                    total_chunks += result["chunks"]

        # 공통 서브레딧 크롤링 (옵션)
        if args.include_common and args.mode != "comments":
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
        elif r.get("mode") == "daily":
            print(f"{status} {r['game_id']} [DAILY]:")
            print(f"    Docs: {r['docs']}, Comments: {r['comments']} → Chunks: {r['chunks']}")
        elif r.get("mode") == "comments":
            print(f"{status} {r['game_id']} [COMMENTS]:")
            print(f"    Comments: {r['comments']} → Chunks: {r['chunks']}")
        else:
            comments = r.get('comments', 0)
            print(f"{status} {r['game_id']}:")
            print(f"    Reddit: {r['reddit']}, Comments: {comments}, Wiki: {r['wiki']} → Chunks: {r['chunks']}")

    print(f"\n{'='*60}")
    print(f"Total chunks saved: {total_chunks}")
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)


if __name__ == "__main__":
    main()
