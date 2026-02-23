"""Reddit JSON Crawler for BossHelp.

공개 JSON 엔드포인트를 사용하여 인증 없이 Reddit 데이터를 수집합니다.
- URL: https://www.reddit.com/r/{subreddit}/top/.json
- 인증 불필요
- Rate limit: ~10 requests/minute
"""

import time
import httpx
from datetime import datetime, timezone
from typing import Generator

from crawler.config import get_game_config, GameConfig
from crawler.models import RawDocument, SourceType, CrawlResult


class RedditJsonCrawler:
    """Reddit 공개 JSON API 크롤러."""

    BASE_URL = "https://www.reddit.com"
    USER_AGENT = "BossHelp/1.0 (Game Guide Q&A Platform)"

    def __init__(self):
        self.client = httpx.Client(
            headers={"User-Agent": self.USER_AGENT},
            timeout=30.0,
            follow_redirects=True,
        )
        self.delay = 6.0  # 분당 10개 제한 준수 (6초 간격)

    def __del__(self):
        if hasattr(self, "client"):
            self.client.close()

    def crawl_initial(
        self,
        game_id: str,
        limit: int = 500,
    ) -> Generator[RawDocument, None, CrawlResult]:
        """
        초기 수집: top all-time posts.

        Args:
            game_id: 게임 ID
            limit: 최대 수집 개수

        Yields:
            RawDocument: 수집된 문서
        """
        game_config = get_game_config(game_id)
        started_at = datetime.now(timezone.utc)
        pages_crawled = 0
        error_message = None

        try:
            # Reddit JSON API는 한 번에 최대 100개
            after = None
            collected = 0

            while collected < limit:
                batch_limit = min(100, limit - collected)
                url = f"{self.BASE_URL}/r/{game_config.subreddit}/top/.json"
                params = {
                    "t": "all",
                    "limit": batch_limit,
                }
                if after:
                    params["after"] = after

                print(f"  [Reddit] Fetching {game_config.subreddit} (collected: {collected})")

                response = self.client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                posts = data.get("data", {}).get("children", [])
                if not posts:
                    break

                for post in posts:
                    post_data = post.get("data", {})
                    doc = self._process_post(post_data, game_config)
                    if doc:
                        pages_crawled += 1
                        collected += 1
                        yield doc

                # 다음 페이지
                after = data.get("data", {}).get("after")
                if not after:
                    break

                time.sleep(self.delay)

            status = "success"

        except httpx.HTTPStatusError as e:
            error_message = f"HTTP {e.response.status_code}: {e.response.text[:200]}"
            status = "failed" if pages_crawled == 0 else "partial"
        except Exception as e:
            error_message = str(e)
            status = "failed" if pages_crawled == 0 else "partial"

        return CrawlResult(
            game_id=game_id,
            source_type=SourceType.REDDIT,
            status=status,
            pages_crawled=pages_crawled,
            error_message=error_message,
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
        )

    def crawl_recent(
        self,
        game_id: str,
        limit: int = 100,
    ) -> Generator[RawDocument, None, CrawlResult]:
        """
        주기적 수집: hot posts.
        """
        game_config = get_game_config(game_id)
        started_at = datetime.now(timezone.utc)
        pages_crawled = 0
        error_message = None

        try:
            url = f"{self.BASE_URL}/r/{game_config.subreddit}/hot/.json"
            params = {"limit": min(100, limit)}

            response = self.client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            for post in data.get("data", {}).get("children", []):
                post_data = post.get("data", {})
                doc = self._process_post(post_data, game_config)
                if doc:
                    pages_crawled += 1
                    yield doc

            status = "success"

        except Exception as e:
            error_message = str(e)
            status = "failed" if pages_crawled == 0 else "partial"

        return CrawlResult(
            game_id=game_id,
            source_type=SourceType.REDDIT,
            status=status,
            pages_crawled=pages_crawled,
            error_message=error_message,
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
        )

    def _process_post(
        self,
        post_data: dict,
        game_config: GameConfig,
    ) -> RawDocument | None:
        """
        Post JSON을 RawDocument로 변환.
        """
        # 삭제된 게시물 제외
        if post_data.get("removed_by_category") or post_data.get("selftext") == "[removed]":
            return None

        # upvote 필터
        score = post_data.get("score", 0)
        if score < game_config.min_upvotes:
            return None

        # flair 필터
        if game_config.flairs:
            flair = post_data.get("link_flair_text") or ""
            if not any(f.lower() in flair.lower() for f in game_config.flairs):
                if score < game_config.min_upvotes * 5:
                    return None

        # 콘텐츠
        content = post_data.get("selftext") or ""

        # 너무 짧은 콘텐츠 제외
        if len(content.strip()) < 50:
            return None

        # 타임스탬프 변환
        created_utc = post_data.get("created_utc", 0)
        created_at = datetime.fromtimestamp(created_utc, tz=timezone.utc)

        return RawDocument(
            game_id=game_config.id,
            source_type=SourceType.REDDIT,
            source_url=f"https://reddit.com{post_data.get('permalink', '')}",
            title=post_data.get("title", ""),
            content=content,
            author=post_data.get("author"),
            created_at=created_at,
            upvotes=score,
            comments_count=post_data.get("num_comments", 0),
            flair=post_data.get("link_flair_text"),
        )


# Singleton
_crawler_instance: RedditJsonCrawler | None = None


def get_reddit_json_crawler() -> RedditJsonCrawler:
    """Get RedditJsonCrawler singleton."""
    global _crawler_instance
    if _crawler_instance is None:
        _crawler_instance = RedditJsonCrawler()
    return _crawler_instance
