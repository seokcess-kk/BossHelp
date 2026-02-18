"""Wiki Crawler for BossHelp.

Fextralife Wiki 데이터를 수집합니다.
Library: BeautifulSoup4
Delay: 1-2초 per page (robots.txt 준수)
Categories: Walkthrough, Boss, Build, NPC, Item
"""

import re
import time
from datetime import datetime, timezone
from typing import Generator
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from crawler.config import get_game_config, GameConfig
from crawler.models import RawDocument, SourceType, CrawlResult


class WikiCrawler:
    """Fextralife Wiki 수집기."""

    # 크롤링 대상 카테고리
    CATEGORIES = {
        "Bosses": "boss_guide",
        "Walkthrough": "progression_route",
        "Builds": "build_guide",
        "NPCs": "npc_quest",
        "Items": "item_location",
        "Weapons": "item_location",
        "Armor": "item_location",
        "Skills": "mechanic_tip",
        "Ashes of War": "item_location",  # Elden Ring specific
        "Prosthetic Tools": "item_location",  # Sekiro specific
        "Charms": "item_location",  # Hollow Knight specific
    }

    # 제외할 페이지 패턴
    EXCLUDE_PATTERNS = [
        r"/User:",
        r"/Talk:",
        r"/File:",
        r"/Category:",
        r"\?action=",
        r"#",
    ]

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "BossHelp/1.0 (Game Guide Bot; +https://bosshelp.app)",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9,ko;q=0.8",
        })
        self.delay = 1.5
        self.visited_urls: set[str] = set()

    def crawl_category(
        self,
        game_id: str,
        category: str,
        limit: int = 500,
    ) -> Generator[RawDocument, None, CrawlResult]:
        """
        특정 카테고리 페이지 수집.

        Args:
            game_id: 게임 ID
            category: 위키 카테고리 (Bosses, Walkthrough, etc.)
            limit: 최대 수집 개수

        Yields:
            RawDocument: 수집된 문서
        """
        game_config = get_game_config(game_id)

        if not game_config.wiki_base_url:
            return CrawlResult(
                game_id=game_id,
                source_type=SourceType.WIKI,
                status="failed",
                error_message="No wiki URL configured",
                started_at=datetime.now(timezone.utc),
            )

        started_at = datetime.now(timezone.utc)
        pages_crawled = 0
        error_message = None

        try:
            # 카테고리 페이지에서 링크 수집
            category_url = f"{game_config.wiki_base_url}/{category}"
            page_urls = self._get_category_links(category_url, game_config.wiki_base_url)

            for url in page_urls[:limit]:
                if url in self.visited_urls:
                    continue
                self.visited_urls.add(url)

                doc = self._fetch_page(url, game_config, category)
                if doc:
                    pages_crawled += 1
                    yield doc

                time.sleep(self.delay)

            status = "success"
        except Exception as e:
            error_message = str(e)
            status = "failed" if pages_crawled == 0 else "partial"

        return CrawlResult(
            game_id=game_id,
            source_type=SourceType.WIKI,
            status=status,
            pages_crawled=pages_crawled,
            error_message=error_message,
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
        )

    def crawl_all(
        self,
        game_id: str,
        limit_per_category: int = 100,
    ) -> Generator[RawDocument, None, CrawlResult]:
        """
        모든 카테고리 수집.

        Args:
            game_id: 게임 ID
            limit_per_category: 카테고리당 최대 수집 개수
        """
        game_config = get_game_config(game_id)

        if not game_config.wiki_base_url:
            return CrawlResult(
                game_id=game_id,
                source_type=SourceType.WIKI,
                status="failed",
                error_message="No wiki URL configured",
                started_at=datetime.now(timezone.utc),
            )

        started_at = datetime.now(timezone.utc)
        total_pages = 0
        error_message = None

        try:
            for category in self.CATEGORIES.keys():
                result = yield from self.crawl_category(
                    game_id, category, limit_per_category
                )
                if result:
                    total_pages += result.pages_crawled

            status = "success"
        except Exception as e:
            error_message = str(e)
            status = "partial"

        return CrawlResult(
            game_id=game_id,
            source_type=SourceType.WIKI,
            status=status,
            pages_crawled=total_pages,
            error_message=error_message,
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
        )

    def _get_category_links(self, category_url: str, base_url: str) -> list[str]:
        """카테고리 페이지에서 문서 링크 추출."""
        try:
            response = self.session.get(category_url, timeout=10)
            response.raise_for_status()
        except Exception:
            return []

        soup = BeautifulSoup(response.text, "lxml")
        links: list[str] = []

        # Fextralife Wiki 구조에 맞는 선택자
        for a in soup.select("#article-body a, .wiki_table a, .article-body a, #wiki-content-block a, .infobox a"):
            href = a.get("href", "")
            if not href or any(re.search(p, href) for p in self.EXCLUDE_PATTERNS):
                continue

            full_url = urljoin(base_url, href)
            parsed = urlparse(full_url)
            base_parsed = urlparse(base_url)

            # 같은 도메인의 링크만 수집
            if parsed.netloc == base_parsed.netloc:
                links.append(full_url)

        return list(set(links))  # 중복 제거

    def _fetch_page(
        self,
        url: str,
        game_config: GameConfig,
        page_category: str,
    ) -> RawDocument | None:
        """위키 페이지 내용 추출."""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
        except Exception:
            return None

        soup = BeautifulSoup(response.text, "lxml")

        # 제목 추출
        title_elem = soup.select_one("h1.page-title, h1#firstHeading, h1")
        title = title_elem.get_text(strip=True) if title_elem else ""

        if not title:
            return None

        # 본문 추출 (Fextralife Wiki 구조)
        content_elem = soup.select_one(
            "#article-body, .article-body, #wiki-content-block, .wiki-content, .page-content"
        )
        if not content_elem:
            return None

        # 불필요한 요소 제거
        for elem in content_elem.select("script, style, nav, .toc, .navbox, .infobox-toggle"):
            elem.decompose()

        # 텍스트 추출 (구조 유지)
        content = self._extract_structured_content(content_elem)

        # 너무 짧은 콘텐츠 제외
        if len(content.strip()) < 200:
            return None

        # 마지막 수정일 추출 시도
        last_edited = None
        edit_elem = soup.select_one(".page-info time, #lastmod")
        if edit_elem:
            try:
                last_edited = datetime.fromisoformat(edit_elem.get("datetime", ""))
            except Exception:
                pass

        return RawDocument(
            game_id=game_config.id,
            source_type=SourceType.WIKI,
            source_url=url,
            title=title,
            content=content,
            page_category=page_category,
            last_edited=last_edited,
        )

    def _extract_structured_content(self, element) -> str:
        """구조화된 콘텐츠 추출 (섹션 구분 유지)."""
        parts: list[str] = []

        for child in element.children:
            if child.name in ["h1", "h2", "h3", "h4"]:
                level = int(child.name[1])
                prefix = "#" * level
                parts.append(f"\n{prefix} {child.get_text(strip=True)}\n")
            elif child.name == "p":
                text = child.get_text(strip=True)
                if text:
                    parts.append(text)
            elif child.name in ["ul", "ol"]:
                for li in child.select("li"):
                    text = li.get_text(strip=True)
                    if text:
                        parts.append(f"- {text}")
            elif child.name == "table":
                # 테이블은 간단히 처리
                for row in child.select("tr"):
                    cells = [td.get_text(strip=True) for td in row.select("td, th")]
                    if cells:
                        parts.append(" | ".join(cells))

        return "\n".join(parts)
