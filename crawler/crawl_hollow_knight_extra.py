#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hollow Knight 추가 데이터 수집 스크립트
- Gap Analysis에서 확인된 데이터 부족 해결
- Wiki 카테고리별 상세 크롤링
"""

import os
import sys
import time
from pathlib import Path

# Windows 콘솔 UTF-8 설정
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

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
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from crawler.models import RawDocument, SourceType
from processors.cleaner import TextCleaner
from processors.classifier import CategoryClassifier
from processors.quality import QualityScorer
from processors.chunker import TextChunker
from processors.embedder import EmbeddingGenerator
from store import SupabaseStore


# Hollow Knight Wiki 카테고리 (확장)
HOLLOW_KNIGHT_CATEGORIES = [
    # 기본 카테고리
    "Bosses",
    "Charms",
    "Items",
    "NPCs",
    "Enemies",
    "Areas",
    # 추가 카테고리 (상세)
    "Spells",
    "Nail Arts",
    "Abilities",
    "Equipment",
    "Upgrades",
    "Locations",
    "Lore",
    "Achievements",
    # 보스 상세
    "Main Bosses",
    "Optional Bosses",
    "Dream Bosses",
    # 아이템 상세
    "Pale Ore",
    "Mask Shards",
    "Vessel Fragments",
    "Rancid Eggs",
    "Grubs",
]

WIKI_BASE = "https://hollowknight.wiki.fextralife.com"


class HollowKnightCrawler:
    """Hollow Knight Wiki 전용 크롤러."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "BossHelp/1.0 (Game Guide Bot; +https://bosshelp.app)",
            "Accept": "text/html,application/xhtml+xml",
        })
        self.delay = 1.5
        self.visited_urls = set()

    def get_page_links(self, category_url: str) -> list[str]:
        """카테고리 페이지에서 링크 추출."""
        links = []
        try:
            resp = self.session.get(category_url, timeout=30)
            if resp.status_code != 200:
                return links

            soup = BeautifulSoup(resp.text, "html.parser")

            # 메인 콘텐츠 영역에서 링크 추출
            content = soup.select_one(".wiki-content-block, #wiki-content-block, .infobox")
            if not content:
                content = soup

            for a in content.find_all("a", href=True):
                href = a["href"]
                if not href.startswith("http"):
                    href = urljoin(WIKI_BASE, href)

                # 필터링
                if WIKI_BASE not in href:
                    continue
                if any(x in href for x in ["User:", "Talk:", "File:", "?action=", "#"]):
                    continue
                if href not in self.visited_urls:
                    links.append(href)

            time.sleep(self.delay)
        except Exception as e:
            print(f"  Error getting links from {category_url}: {e}")

        return links

    def crawl_page(self, url: str) -> RawDocument | None:
        """단일 페이지 크롤링."""
        try:
            resp = self.session.get(url, timeout=30)
            if resp.status_code != 200:
                return None

            soup = BeautifulSoup(resp.text, "html.parser")

            # 제목 추출
            title_elem = soup.select_one("h1.page-title, h1#firstHeading, h1")
            title = title_elem.get_text(strip=True) if title_elem else url.split("/")[-1]

            # 콘텐츠 추출
            content_elem = soup.select_one(".wiki-content-block, #wiki-content-block, .mw-parser-output")
            if not content_elem:
                return None

            # 불필요한 요소 제거
            for elem in content_elem.select("script, style, nav, .navbox, .toc, .infobox-image"):
                elem.decompose()

            content = content_elem.get_text(separator="\n", strip=True)

            if len(content) < 100:
                return None

            time.sleep(self.delay)

            return RawDocument(
                game_id="hollow-knight",
                source_type=SourceType.WIKI,
                source_url=url,
                title=title,
                content=content,
                page_category="hollow_knight_extra",
            )

        except Exception as e:
            print(f"  Error crawling {url}: {e}")
            return None

    def crawl_category(self, category: str, limit: int = 100) -> list[RawDocument]:
        """카테고리 크롤링."""
        docs = []
        category_url = f"{WIKI_BASE}/{category}"

        print(f"  Crawling category: {category}")

        # 카테고리 페이지 자체도 크롤링
        if category_url not in self.visited_urls:
            self.visited_urls.add(category_url)
            doc = self.crawl_page(category_url)
            if doc:
                docs.append(doc)

        # 링크된 페이지들 크롤링
        links = self.get_page_links(category_url)

        for url in links[:limit]:
            if url in self.visited_urls:
                continue
            self.visited_urls.add(url)

            doc = self.crawl_page(url)
            if doc:
                docs.append(doc)
                print(f"    ✓ {doc.title[:40]}...")

        return docs


def main():
    print("=" * 60)
    print("  Hollow Knight Extra Data Collection")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    crawler = HollowKnightCrawler()
    cleaner = TextCleaner()
    classifier = CategoryClassifier()
    quality_scorer = QualityScorer()
    chunker = TextChunker()
    embedder = EmbeddingGenerator()
    store = SupabaseStore()

    all_docs = []

    # 카테고리별 크롤링
    for category in HOLLOW_KNIGHT_CATEGORIES:
        docs = crawler.crawl_category(category, limit=50)
        all_docs.extend(docs)
        print(f"  → {category}: {len(docs)} pages")

    print(f"\n[Total Raw Documents] {len(all_docs)}")

    if not all_docs:
        print("[SKIP] No documents collected")
        return

    # 데이터 처리
    print("\n[Processing]")

    print("  - Cleaning...")
    cleaned = cleaner.clean_batch(all_docs)
    print(f"    Cleaned: {len(cleaned)}")

    print("  - Classifying...")
    classified = classifier.classify_batch(cleaned)

    print("  - Scoring quality...")
    scored = quality_scorer.score_batch(classified)
    scored = [d for d in scored if d.quality_score >= 0.3]
    print(f"    After quality filter: {len(scored)}")

    print("  - Chunking...")
    chunks = chunker.chunk_batch(scored)
    print(f"    Chunks created: {len(chunks)}")

    # 임베딩 & 저장
    saved = 0
    if chunks:
        print("  - Embedding and storing...")
        embedded = list(embedder.embed_batch(chunks, show_progress=False))
        saved = store.upsert_batch(embedded)
        print(f"    ✓ Saved: {saved} chunks")

    print("\n" + "=" * 60)
    print(f"Hollow Knight Extra Data: {saved} chunks saved")
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)


if __name__ == "__main__":
    main()
