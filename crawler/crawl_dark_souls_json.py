#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dark Souls 시리즈 데이터 수집 스크립트 (공개 JSON API 사용)
"""

import os
import sys
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


def main():
    print("=" * 60)
    print("Dark Souls Series Data Collection")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 수집할 게임
    games = ["dark-souls", "dark-souls-2", "dark-souls-3"]

    # 컴포넌트 초기화
    reddit_crawler = RedditJsonCrawler()
    wiki_crawler = WikiCrawler()
    cleaner = TextCleaner()
    classifier = CategoryClassifier()
    quality_scorer = QualityScorer()
    chunker = TextChunker()
    embedder = EmbeddingGenerator()
    store = SupabaseStore()

    total_chunks = 0
    results = []

    for game_id in games:
        print(f"\n{'='*50}")
        print(f"Processing: {game_id}")
        print(f"{'='*50}")

        game_chunks = 0

        # 1. Reddit 수집
        print(f"\n[1/2] Reddit crawling...")
        reddit_docs = []
        try:
            for doc in reddit_crawler.crawl_initial(game_id, limit=200):
                reddit_docs.append(doc)
            print(f"  - Collected: {len(reddit_docs)} posts")
        except Exception as e:
            print(f"  - Error: {e}")

        # 2. Wiki 수집
        print(f"\n[2/2] Wiki crawling...")
        wiki_docs = []
        try:
            for doc in wiki_crawler.crawl_all(game_id, limit_per_category=30):
                wiki_docs.append(doc)
            print(f"  - Collected: {len(wiki_docs)} pages")
        except Exception as e:
            print(f"  - Error: {e}")

        # 3. 문서 처리
        all_docs = reddit_docs + wiki_docs
        if not all_docs:
            print(f"  - No documents collected, skipping...")
            results.append((game_id, 0, 0, "No data"))
            continue

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
        if chunks:
            print("  - Embedding and storing...")
            embedded_chunks = list(embedder.embed_batch(chunks, show_progress=False))
            saved = store.upsert_batch(embedded_chunks)
            print(f"    Saved: {saved} chunks")
            game_chunks = saved
        else:
            game_chunks = 0

        total_chunks += game_chunks
        results.append((game_id, len(reddit_docs), len(wiki_docs), game_chunks))

    # 결과 출력
    print("\n" + "=" * 60)
    print("Collection Results")
    print("=" * 60)

    for game_id, reddit, wiki, chunks in results:
        status = "[OK]" if chunks > 0 else "[SKIP]"
        print(f"{status} {game_id}:")
        print(f"     Reddit: {reddit}, Wiki: {wiki} -> Chunks: {chunks}")

    print(f"\nTotal chunks saved: {total_chunks}")
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)


if __name__ == "__main__":
    main()
