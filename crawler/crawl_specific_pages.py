#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
특정 보스/아이템 페이지 직접 크롤링
"""

import sys
import time
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

_original_print = print
def print(*args, **kwargs):
    kwargs.setdefault("flush", True)
    _original_print(*args, **kwargs)

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "crawler"))
sys.path.insert(0, str(project_root / "backend"))

from dotenv import load_dotenv
load_dotenv(project_root / "backend" / ".env")

from datetime import datetime
import requests
from bs4 import BeautifulSoup

from crawler.models import RawDocument, SourceType
from processors.cleaner import TextCleaner
from processors.classifier import CategoryClassifier
from processors.quality import QualityScorer
from processors.chunker import TextChunker
from processors.embedder import EmbeddingGenerator
from store import SupabaseStore


# 직접 크롤링할 주요 페이지 목록
ELDEN_RING_PAGES = {
    "bosses": [
        # 메인 보스
        "https://eldenring.wiki.fextralife.com/Malenia+Blade+of+Miquella",
        "https://eldenring.wiki.fextralife.com/Starscourge+Radahn",
        "https://eldenring.wiki.fextralife.com/Morgott+the+Omen+King",
        "https://eldenring.wiki.fextralife.com/Godfrey+First+Elden+Lord",
        "https://eldenring.wiki.fextralife.com/Radagon+of+the+Golden+Order",
        "https://eldenring.wiki.fextralife.com/Elden+Beast",
        "https://eldenring.wiki.fextralife.com/Rykard+Lord+of+Blasphemy",
        "https://eldenring.wiki.fextralife.com/Mohg+Lord+of+Blood",
        "https://eldenring.wiki.fextralife.com/Maliketh+the+Black+Blade",
        "https://eldenring.wiki.fextralife.com/Fire+Giant",
        "https://eldenring.wiki.fextralife.com/Godrick+the+Grafted",
        "https://eldenring.wiki.fextralife.com/Rennala+Queen+of+the+Full+Moon",
        "https://eldenring.wiki.fextralife.com/Margit+the+Fell+Omen",
        "https://eldenring.wiki.fextralife.com/Godskin+Duo",
        "https://eldenring.wiki.fextralife.com/Dragonlord+Placidusax",
        # DLC 보스
        "https://eldenring.wiki.fextralife.com/Messmer+the+Impaler",
        "https://eldenring.wiki.fextralife.com/Promised+Consort+Radahn",
    ],
    "weapons": [
        # 인기 무기
        "https://eldenring.wiki.fextralife.com/Moonveil",
        "https://eldenring.wiki.fextralife.com/Rivers+of+Blood",
        "https://eldenring.wiki.fextralife.com/Blasphemous+Blade",
        "https://eldenring.wiki.fextralife.com/Greatsword",
        "https://eldenring.wiki.fextralife.com/Uchigatana",
        "https://eldenring.wiki.fextralife.com/Ruins+Greatsword",
        "https://eldenring.wiki.fextralife.com/Sword+of+Night+and+Flame",
        "https://eldenring.wiki.fextralife.com/Dark+Moon+Greatsword",
        "https://eldenring.wiki.fextralife.com/Hand+of+Malenia",
        "https://eldenring.wiki.fextralife.com/Starscourge+Greatsword",
        "https://eldenring.wiki.fextralife.com/Bloodhound's+Fang",
        "https://eldenring.wiki.fextralife.com/Reduvia",
        "https://eldenring.wiki.fextralife.com/Meteoric+Ore+Blade",
        "https://eldenring.wiki.fextralife.com/Wing+of+Astel",
    ],
    "items": [
        # 탈리스만
        "https://eldenring.wiki.fextralife.com/Shard+of+Alexander",
        "https://eldenring.wiki.fextralife.com/Radagon's+Soreseal",
        "https://eldenring.wiki.fextralife.com/Erdtree's+Favor",
        "https://eldenring.wiki.fextralife.com/Lord+of+Blood's+Exultation",
        "https://eldenring.wiki.fextralife.com/Rotten+Winged+Sword+Insignia",
        "https://eldenring.wiki.fextralife.com/Green+Turtle+Talisman",
        "https://eldenring.wiki.fextralife.com/Carian+Filigreed+Crest",
        # 스피릿 애쉬
        "https://eldenring.wiki.fextralife.com/Mimic+Tear+Ashes",
        "https://eldenring.wiki.fextralife.com/Black+Knife+Tiche+Ashes",
    ],
}

DARK_SOULS_3_PAGES = {
    "bosses": [
        "https://darksouls3.wiki.fextralife.com/Nameless+King",
        "https://darksouls3.wiki.fextralife.com/Soul+of+Cinder",
        "https://darksouls3.wiki.fextralife.com/Pontiff+Sulyvahn",
        "https://darksouls3.wiki.fextralife.com/Dancer+of+the+Boreal+Valley",
        "https://darksouls3.wiki.fextralife.com/Abyss+Watchers",
        "https://darksouls3.wiki.fextralife.com/Slave+Knight+Gael",
        "https://darksouls3.wiki.fextralife.com/Sister+Friede",
        "https://darksouls3.wiki.fextralife.com/Darkeater+Midir",
        "https://darksouls3.wiki.fextralife.com/Aldrich+Devourer+of+Gods",
        "https://darksouls3.wiki.fextralife.com/Yhorm+the+Giant",
        "https://darksouls3.wiki.fextralife.com/Twin+Princes",
    ],
}

SEKIRO_PAGES = {
    "bosses": [
        "https://sekiroshadowsdietwice.wiki.fextralife.com/Isshin+the+Sword+Saint",
        "https://sekiroshadowsdietwice.wiki.fextralife.com/Genichiro+Ashina",
        "https://sekiroshadowsdietwice.wiki.fextralife.com/Guardian+Ape",
        "https://sekiroshadowsdietwice.wiki.fextralife.com/Lady+Butterfly",
        "https://sekiroshadowsdietwice.wiki.fextralife.com/Owl+(Father)",
        "https://sekiroshadowsdietwice.wiki.fextralife.com/Demon+of+Hatred",
        "https://sekiroshadowsdietwice.wiki.fextralife.com/Divine+Dragon",
        "https://sekiroshadowsdietwice.wiki.fextralife.com/Corrupted+Monk",
    ],
}


class DirectPageCrawler:
    """직접 URL 크롤러."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "BossHelp/1.0 (Game Guide Bot)",
            "Accept": "text/html",
        })
        self.delay = 1.5

    def crawl_url(self, url: str, game_id: str, category: str) -> RawDocument | None:
        """단일 URL 크롤링."""
        try:
            response = self.session.get(url, timeout=20)
            response.raise_for_status()
        except Exception as e:
            print(f"    [ERROR] {e}")
            return None

        soup = BeautifulSoup(response.text, "lxml")

        # 제목 추출
        title_elem = soup.select_one("h1.page-title, h1#firstHeading, h1")
        title = title_elem.get_text(strip=True) if title_elem else ""

        if not title:
            return None

        # 본문 추출
        content_elem = soup.select_one(
            "#wiki-content-block, #article-body, .article-body"
        )
        if not content_elem:
            return None

        # 불필요한 요소 제거
        for elem in content_elem.select("script, style, nav, .toc, .navbox, .comments, .infobox"):
            elem.decompose()

        # 상세 콘텐츠 추출
        content = self._extract_detailed_content(content_elem, title)

        if len(content.strip()) < 300:
            return None

        print(f"    ✓ {title} ({len(content)} chars)")

        return RawDocument(
            game_id=game_id,
            source_type=SourceType.WIKI,
            source_url=url,
            title=title,
            content=content,
            page_category=category,
        )

    def _extract_detailed_content(self, element, title: str) -> str:
        """상세 콘텐츠 추출 (전략, 공략 포함)."""
        parts = [f"# {title}"]

        for elem in element.find_all(["h2", "h3", "h4", "p", "ul", "ol", "table"]):
            if elem.name in ["h2", "h3", "h4"]:
                text = elem.get_text(strip=True)
                if text:
                    level = int(elem.name[1])
                    parts.append(f"\n{'#' * level} {text}\n")
            elif elem.name == "p":
                text = elem.get_text(strip=True)
                if text and len(text) > 30:
                    parts.append(text)
            elif elem.name in ["ul", "ol"]:
                for li in elem.find_all("li", recursive=False):
                    text = li.get_text(strip=True)
                    if text and len(text) > 10:
                        parts.append(f"- {text}")
            elif elem.name == "table":
                # 테이블 (스탯, 드롭 등)
                for row in elem.select("tr")[:30]:
                    cells = [td.get_text(strip=True) for td in row.select("td, th")]
                    if cells and any(c for c in cells if len(c) > 2):
                        parts.append(" | ".join(cells))

        return "\n".join(parts)


def main():
    print("=" * 60)
    print("  Specific Pages Crawling")
    print("=" * 60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    crawler = DirectPageCrawler()
    cleaner = TextCleaner()
    classifier = CategoryClassifier()
    quality_scorer = QualityScorer()
    chunker = TextChunker()
    embedder = EmbeddingGenerator()
    store = SupabaseStore()

    all_configs = [
        ("elden-ring", ELDEN_RING_PAGES),
        ("dark-souls-3", DARK_SOULS_3_PAGES),
        ("sekiro", SEKIRO_PAGES),
    ]

    total_chunks = 0
    results = []

    for game_id, pages_config in all_configs:
        for category, urls in pages_config.items():
            print(f"\n{'='*50}")
            print(f"  {game_id} / {category} ({len(urls)} pages)")
            print(f"{'='*50}")

            docs = []
            for url in urls:
                doc = crawler.crawl_url(url, game_id, category)
                if doc:
                    docs.append(doc)
                time.sleep(crawler.delay)

            print(f"  Collected: {len(docs)} pages")

            if not docs:
                results.append((game_id, category, 0, 0))
                continue

            # 처리
            print("  Processing...")
            cleaned = cleaner.clean_batch(docs)
            classified = classifier.classify_batch(cleaned)
            scored = quality_scorer.score_batch(classified)
            scored = [d for d in scored if d.quality_score >= 0.25]
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
