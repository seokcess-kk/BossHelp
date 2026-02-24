#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
보스 공략 및 아이템 위치 데이터 추가 수집 스크립트
- 보스 개별 페이지 집중 크롤링
- 아이템/무기 위치 정보 수집
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

from datetime import datetime
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

from crawler.models import RawDocument, SourceType
from processors.cleaner import TextCleaner
from processors.classifier import CategoryClassifier
from processors.quality import QualityScorer
from processors.chunker import TextChunker
from processors.embedder import EmbeddingGenerator
from store import SupabaseStore


class BossItemCrawler:
    """보스 및 아이템 전용 크롤러."""

    # 게임별 보스/아이템 카테고리 URL
    GAME_CONFIGS = {
        "elden-ring": {
            "base_url": "https://eldenring.wiki.fextralife.com",
            "categories": {
                "bosses": [
                    "/Bosses",
                    "/Legacy+Dungeon+Bosses",
                    "/Field+Bosses",
                    "/Great+Enemy+Bosses",
                    "/Demigods",
                ],
                "weapons": [
                    "/Weapons",
                    "/Katanas",
                    "/Greatswords",
                    "/Colossal+Weapons",
                    "/Straight+Swords",
                ],
                "items": [
                    "/Items",
                    "/Talismans",
                    "/Ashes+of+War",
                    "/Spirit+Ashes",
                    "/Key+Items",
                ],
                "locations": [
                    "/Locations",
                    "/Limgrave",
                    "/Liurnia+of+the+Lakes",
                    "/Caelid",
                    "/Altus+Plateau",
                    "/Mountaintops+of+the+Giants",
                ],
            }
        },
        "dark-souls-3": {
            "base_url": "https://darksouls3.wiki.fextralife.com",
            "categories": {
                "bosses": [
                    "/Bosses",
                    "/Lords+of+Cinder",
                    "/Optional+Bosses",
                ],
                "weapons": [
                    "/Weapons",
                    "/Ultra+Greatswords",
                    "/Straight+Swords",
                    "/Katanas",
                ],
                "items": [
                    "/Items",
                    "/Rings",
                    "/Estus+Shards",
                    "/Titanite",
                ],
            }
        },
        "sekiro": {
            "base_url": "https://sekiroshadowsdietwice.wiki.fextralife.com",
            "categories": {
                "bosses": [
                    "/Bosses",
                    "/Mini-Bosses",
                ],
                "items": [
                    "/Items",
                    "/Prosthetic+Tools",
                    "/Combat+Arts",
                    "/Skills",
                ],
            }
        },
    }

    EXCLUDE_PATTERNS = [
        "/User:", "/Talk:", "/File:", "/Category:",
        "?action=", "#", "/Search", "/Recent+Changes",
    ]

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "BossHelp/1.0 (Game Guide Bot)",
            "Accept": "text/html",
        })
        self.delay = 1.5
        self.visited_urls = set()

    def crawl_category_deep(self, game_id: str, category_type: str, limit: int = 100):
        """카테고리 깊이 우선 크롤링."""
        config = self.GAME_CONFIGS.get(game_id)
        if not config:
            print(f"[SKIP] Unknown game: {game_id}")
            return []

        base_url = config["base_url"]
        category_urls = config["categories"].get(category_type, [])

        all_docs = []

        for cat_path in category_urls:
            cat_url = f"{base_url}{cat_path}"
            print(f"  [Category] {cat_path}")

            # 카테고리 페이지에서 링크 수집
            links = self._get_all_links(cat_url, base_url)
            print(f"    Found {len(links)} links")

            for url in links[:limit]:
                if url in self.visited_urls:
                    continue
                self.visited_urls.add(url)

                doc = self._fetch_page(url, game_id, category_type)
                if doc:
                    all_docs.append(doc)

                time.sleep(self.delay)

                if len(all_docs) >= limit:
                    break

            if len(all_docs) >= limit:
                break

        return all_docs

    def _get_all_links(self, url: str, base_url: str) -> list[str]:
        """페이지에서 모든 관련 링크 추출."""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
        except Exception as e:
            print(f"    [ERROR] {e}")
            return []

        soup = BeautifulSoup(response.text, "lxml")
        links = []

        # 다양한 선택자로 링크 추출
        selectors = [
            "#wiki-content-block a",
            ".wiki_table a",
            "#tagged-pages a",
            ".article-body a",
            ".infobox a",
            "#infobox a",
            "table.wiki_table a",
        ]

        for selector in selectors:
            for a in soup.select(selector):
                href = a.get("href", "")
                if not href:
                    continue

                # 제외 패턴 확인
                if any(p in href for p in self.EXCLUDE_PATTERNS):
                    continue

                full_url = urljoin(base_url, href)

                # 같은 도메인만
                if base_url in full_url and full_url not in links:
                    links.append(full_url)

        return list(set(links))

    def _fetch_page(self, url: str, game_id: str, category: str) -> RawDocument | None:
        """개별 페이지 내용 추출."""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
        except Exception:
            return None

        soup = BeautifulSoup(response.text, "lxml")

        # 제목 추출
        title_elem = soup.select_one("h1.page-title, h1#firstHeading, h1")
        title = title_elem.get_text(strip=True) if title_elem else ""

        if not title or len(title) < 2:
            return None

        # 본문 추출
        content_elem = soup.select_one(
            "#wiki-content-block, #article-body, .article-body, .page-content"
        )
        if not content_elem:
            return None

        # 불필요한 요소 제거
        for elem in content_elem.select("script, style, nav, .toc, .navbox, .comments"):
            elem.decompose()

        content = self._extract_content(content_elem)

        if len(content.strip()) < 200:
            return None

        return RawDocument(
            game_id=game_id,
            source_type=SourceType.WIKI,
            source_url=url,
            title=title,
            content=content,
            page_category=category,
        )

    def _extract_content(self, element) -> str:
        """구조화된 콘텐츠 추출."""
        parts = []

        for elem in element.find_all(["h1", "h2", "h3", "h4", "p", "ul", "ol", "table", "div"]):
            if elem.name in ["h1", "h2", "h3", "h4"]:
                text = elem.get_text(strip=True)
                if text:
                    level = int(elem.name[1])
                    parts.append(f"\n{'#' * level} {text}\n")
            elif elem.name == "p":
                text = elem.get_text(strip=True)
                if text and len(text) > 20:
                    parts.append(text)
            elif elem.name in ["ul", "ol"]:
                for li in elem.find_all("li", recursive=False):
                    text = li.get_text(strip=True)
                    if text:
                        parts.append(f"- {text}")
            elif elem.name == "table":
                for row in elem.select("tr")[:20]:  # 테이블 행 제한
                    cells = [td.get_text(strip=True) for td in row.select("td, th")]
                    if cells and any(cells):
                        parts.append(" | ".join(cells))

        return "\n".join(parts)


def main():
    print("=" * 60)
    print("  Boss & Item Data Collection")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    crawler = BossItemCrawler()
    cleaner = TextCleaner()
    classifier = CategoryClassifier()
    quality_scorer = QualityScorer()
    chunker = TextChunker()
    embedder = EmbeddingGenerator()
    store = SupabaseStore()

    # 수집 대상
    targets = [
        ("elden-ring", "bosses", 80),
        ("elden-ring", "weapons", 80),
        ("elden-ring", "items", 80),
        ("elden-ring", "locations", 50),
        ("dark-souls-3", "bosses", 50),
        ("dark-souls-3", "weapons", 50),
        ("sekiro", "bosses", 40),
        ("sekiro", "items", 40),
    ]

    total_chunks = 0
    results = []

    for game_id, category, limit in targets:
        print(f"\n{'='*50}")
        print(f"  {game_id} / {category} (limit: {limit})")
        print(f"{'='*50}")

        docs = crawler.crawl_category_deep(game_id, category, limit)
        print(f"  Collected: {len(docs)} pages")

        if not docs:
            results.append((game_id, category, 0, 0))
            continue

        # 처리
        print("  Processing...")
        cleaned = cleaner.clean_batch(docs)
        classified = classifier.classify_batch(cleaned)
        scored = quality_scorer.score_batch(classified)
        scored = [d for d in scored if d.quality_score >= 0.3]
        chunks = chunker.chunk_batch(scored)
        print(f"    Chunks: {len(chunks)}")

        # 저장
        if chunks:
            print("  Embedding and storing...")
            embedded = list(embedder.embed_batch(chunks, show_progress=False))
            saved = store.upsert_batch(embedded)
            print(f"    Saved: {saved}")
            total_chunks += saved
            results.append((game_id, category, len(docs), saved))
        else:
            results.append((game_id, category, len(docs), 0))

    # 결과 출력
    print("\n" + "=" * 60)
    print("  Collection Results")
    print("=" * 60)

    for game_id, category, pages, chunks in results:
        status = "✓" if chunks > 0 else "✗"
        print(f"{status} {game_id}/{category}: {pages} pages → {chunks} chunks")

    print(f"\nTotal new chunks: {total_chunks}")
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)


if __name__ == "__main__":
    main()
