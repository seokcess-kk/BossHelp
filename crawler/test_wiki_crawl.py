#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wiki 데이터 수집 테스트 (Dark Souls 3)
"""

import os
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

project_root = Path(__file__).parent.parent
crawler_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(crawler_root))
sys.path.insert(0, str(project_root / "backend"))

from dotenv import load_dotenv
load_dotenv(project_root / "backend" / ".env")

from datetime import datetime
from crawlers.wiki import WikiCrawler
from processors.cleaner import TextCleaner
from processors.classifier import CategoryClassifier
from processors.quality import QualityScorer
from processors.chunker import TextChunker
from processors.embedder import EmbeddingGenerator
from store import SupabaseStore


def main():
    print("=" * 50)
    print("Dark Souls 3 Wiki Data Collection Test")
    print("=" * 50)
    print(f"Started: {datetime.now().strftime('%H:%M:%S')}")

    # 컴포넌트 초기화
    wiki_crawler = WikiCrawler()
    cleaner = TextCleaner()
    classifier = CategoryClassifier()
    quality_scorer = QualityScorer()
    chunker = TextChunker()
    embedder = EmbeddingGenerator()
    store = SupabaseStore()

    game_id = "dark-souls-3"

    # Wiki 수집 (10개만)
    print("\n[1] Wiki crawling (limit=10)...")
    wiki_docs = []
    try:
        for doc in wiki_crawler.crawl_all(game_id, limit_per_category=2):
            wiki_docs.append(doc)
            print(f"  - {doc.title[:50]}...")
            if len(wiki_docs) >= 10:
                break
        print(f"  Total: {len(wiki_docs)} pages")
    except Exception as e:
        print(f"  Error: {e}")
        return

    if not wiki_docs:
        print("No documents collected!")
        return

    # 처리
    print("\n[2] Processing...")
    cleaned = cleaner.clean_batch(wiki_docs)
    print(f"  Cleaned: {len(cleaned)}")

    classified = classifier.classify_batch(cleaned)
    scored = quality_scorer.score_batch(classified)
    scored = [d for d in scored if d.quality_score >= 0.3]
    print(f"  Scored: {len(scored)}")

    chunks = chunker.chunk_batch(scored)
    print(f"  Chunks: {len(chunks)}")

    # Embed & Store
    if chunks:
        print("\n[3] Embedding and storing...")
        embedded = list(embedder.embed_batch(chunks[:20], show_progress=False))
        saved = store.upsert_batch(embedded)
        print(f"  Saved: {saved} chunks")
    else:
        print("No chunks to save!")

    print(f"\nCompleted: {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 50)


if __name__ == "__main__":
    main()
