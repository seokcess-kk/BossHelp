"""간단한 Wiki 크롤러 - 직접 실행용"""
import os
import time
import re
from urllib.parse import urljoin, urlparse
from datetime import datetime, timezone
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

# OpenAI와 Supabase 임포트
from openai import OpenAI
from supabase import create_client

@dataclass
class WikiPage:
    game_id: str
    title: str
    content: str
    url: str
    category: str


class SimpleWikiCrawler:
    """간단한 Wiki 크롤러"""

    EXCLUDE_PATTERNS = [
        r"/User:", r"/Talk:", r"/File:", r"/Category:",
        r"\?action=", r"#", r"javascript:", r"mailto:",
    ]

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml",
        })
        self.visited = set()

    def get_links(self, url: str, base_url: str) -> list[str]:
        """페이지에서 Wiki 링크 추출"""
        try:
            resp = self.session.get(url, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            print(f"   ❌ 요청 실패: {e}")
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        links = []

        # #wiki-content-block 내의 링크 찾기
        for a in soup.select("#wiki-content-block a"):
            href = a.get("href", "")

            # 제외 패턴 체크
            if not href or any(re.search(p, href) for p in self.EXCLUDE_PATTERNS):
                continue

            # 전체 URL로 변환
            full_url = urljoin(base_url, href)
            parsed = urlparse(full_url)
            base_parsed = urlparse(base_url)

            # 같은 도메인만
            if parsed.netloc == base_parsed.netloc:
                # 쿼리스트링 제거
                clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                if clean_url not in self.visited:
                    links.append(clean_url)

        return list(set(links))

    def get_page_content(self, url: str, game_id: str, category: str) -> WikiPage | None:
        """페이지 내용 추출"""
        try:
            resp = self.session.get(url, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            return None

        soup = BeautifulSoup(resp.text, "html.parser")

        # 제목
        title_elem = soup.select_one("h1.page-title, h1#page-title, #page-title")
        title = title_elem.get_text(strip=True) if title_elem else ""

        if not title:
            return None

        # 본문
        content_elem = soup.select_one("#wiki-content-block")
        if not content_elem:
            return None

        # 불필요한 요소 제거
        for elem in content_elem.select("script, style, nav, .toc, .navbox, iframe, .ad"):
            elem.decompose()

        # 텍스트 추출
        content = content_elem.get_text(separator="\n", strip=True)

        # 너무 짧으면 제외
        if len(content) < 200:
            return None

        return WikiPage(
            game_id=game_id,
            title=title,
            content=content,
            url=url,
            category=category,
        )

    def crawl(self, game_id: str, base_url: str, categories: list[str], limit: int = 50) -> list[WikiPage]:
        """크롤링 실행"""
        pages = []

        for category in categories:
            print(f"\n📂 카테고리: {category}")
            category_url = f"{base_url}/{category}"
            self.visited.add(category_url)

            # 카테고리 페이지에서 링크 수집
            links = self.get_links(category_url, base_url)
            print(f"   발견된 링크: {len(links)}개")

            # 각 링크 크롤링
            count = 0
            for link in links[:limit]:
                if link in self.visited:
                    continue
                self.visited.add(link)

                page = self.get_page_content(link, game_id, category)
                if page:
                    pages.append(page)
                    count += 1
                    print(f"   ✅ [{count}] {page.title[:40]}")

                time.sleep(1.5)  # Rate limiting

            print(f"   수집 완료: {count}개")

        return pages


def map_category(wiki_category: str) -> str:
    """Wiki 카테고리를 DB 카테고리로 매핑"""
    mapping = {
        "Bosses": "boss_guide",
        "Weapons": "item_location",
        "Armor": "item_location",
        "Talismans": "item_location",
        "Items": "item_location",
        "Walkthrough": "progression_route",
        "Builds": "build_guide",
        "NPCs": "npc_quest",
        "Skills": "mechanic_tip",
        "Ashes of War": "item_location",
    }
    return mapping.get(wiki_category, "mechanic_tip")


def chunk_text(text: str, max_tokens: int = 400) -> list[str]:
    """텍스트를 청크로 분할 (개선된 버전)

    text-embedding-3-small 토큰 제한: 8192
    안전하게 400 토큰 = ~1600 chars로 설정
    """
    # 대략 4글자 = 1토큰으로 계산 (영어 기준, 위키 콘텐츠)
    max_chars = max_tokens * 4
    chunks = []

    # 먼저 줄바꿈으로 분할
    paragraphs = text.split("\n")
    current_chunk = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # 현재 청크 + 새 단락이 제한 이내면 추가
        if len(current_chunk) + len(para) + 1 < max_chars:
            current_chunk += para + "\n"
        else:
            # 현재 청크 저장
            if current_chunk.strip():
                chunks.append(current_chunk.strip())

            # 단락 자체가 너무 길면 강제 분할
            if len(para) >= max_chars:
                words = para.split(" ")
                current_chunk = ""
                for word in words:
                    if len(current_chunk) + len(word) + 1 < max_chars:
                        current_chunk += word + " "
                    else:
                        if current_chunk.strip():
                            chunks.append(current_chunk.strip())
                        current_chunk = word + " "
            else:
                current_chunk = para + "\n"

    # 마지막 청크 저장
    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    # 너무 짧은 청크 필터링 (최소 50자)
    return [c for c in chunks if len(c) >= 50]


def main():
    print("=" * 60)
    print("🎮 BossHelp Wiki Crawler")
    print("=" * 60)

    # 환경변수 확인
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if not all([supabase_url, supabase_key, openai_key]):
        print("❌ 환경변수가 설정되지 않았습니다.")
        return

    # 클라이언트 초기화
    supabase = create_client(supabase_url, supabase_key)
    openai_client = OpenAI(api_key=openai_key)

    # 게임 설정
    games = {
        "elden-ring": {
            "base_url": "https://eldenring.wiki.fextralife.com",
            "categories": ["Bosses", "Weapons", "Armor", "Talismans"],
        }
    }

    crawler = SimpleWikiCrawler()

    for game_id, config in games.items():
        print(f"\n{'='*60}")
        print(f"🎮 {game_id.upper()}")
        print(f"📚 {config['base_url']}")
        print(f"{'='*60}")

        # 크롤링
        pages = crawler.crawl(
            game_id=game_id,
            base_url=config["base_url"],
            categories=config["categories"],
            limit=20,  # 카테고리당 20개
        )

        print(f"\n📄 총 {len(pages)}개 페이지 수집 완료")

        if not pages:
            continue

        # 청킹
        print("\n✂️ 청크 생성 중...")
        chunks = []
        for page in pages:
            page_chunks = chunk_text(page.content)
            for i, chunk in enumerate(page_chunks):
                chunks.append({
                    "game_id": page.game_id,
                    "title": page.title,
                    "content": chunk,
                    "url": page.url,
                    "category": page.category,
                    "chunk_index": i,
                })

        print(f"   청크 수: {len(chunks)}개")

        # 임베딩 생성 및 저장
        print("\n🧠 임베딩 생성 및 저장 중...")
        saved = 0

        for i, chunk in enumerate(chunks):
            try:
                # 임베딩 생성
                response = openai_client.embeddings.create(
                    model="text-embedding-3-small",
                    input=chunk["content"]
                )
                embedding = response.data[0].embedding

                # chunks 테이블에 저장 (migration 스키마에 맞춤)
                data = {
                    "game_id": chunk["game_id"],
                    "category": map_category(chunk["category"]),
                    "source_type": "wiki",
                    "source_url": chunk["url"],
                    "title": chunk["title"],
                    "content": chunk["content"],
                    "embedding": embedding,
                    "quality_score": 0.8,
                    "spoiler_level": "none",
                    "is_active": True,
                }

                supabase.table("chunks").insert(data).execute()
                saved += 1

                if saved % 10 == 0:
                    print(f"   저장: {saved}/{len(chunks)}")

                time.sleep(0.1)  # Rate limiting

            except Exception as e:
                print(f"   ❌ 에러: {e}")
                continue

        print(f"\n✅ 저장 완료: {saved}개")

    print("\n" + "=" * 60)
    print("🎉 크롤링 완료!")
    print("=" * 60)


if __name__ == "__main__":
    main()
