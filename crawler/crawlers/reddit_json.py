"""Reddit JSON Crawler for BossHelp.

공개 JSON 엔드포인트를 사용하여 인증 없이 Reddit 데이터를 수집합니다.
- URL: https://www.reddit.com/r/{subreddit}/top/.json
- 인증 불필요
- Rate limit: ~10 requests/minute

수집 모드:
- initial: /top?t=all (역대 최고 인기)
- daily: /hot + /new + 댓글 (일일 업데이트)
"""

import time
import httpx
from datetime import datetime, timezone
from typing import Generator, Literal

from crawler.config import get_game_config, GameConfig, GAME_NAME_MAPPING, COMMON_SUBREDDITS
from crawler.models import RawDocument, SourceType, CrawlResult


# 수집 모드 타입
CrawlMode = Literal["initial", "daily"]


def detect_game_from_title(title: str) -> str | None:
    """제목에서 게임 이름 감지.

    Args:
        title: Reddit 포스트 제목

    Returns:
        게임 ID 또는 None (감지 실패 시)
    """
    title_lower = title.lower()

    # 긴 매핑부터 검사 (예: "dark souls 3"이 "dark souls"보다 먼저 매칭되도록)
    sorted_mappings = sorted(GAME_NAME_MAPPING.items(), key=lambda x: -len(x[0]))

    for name, game_id in sorted_mappings:
        if name in title_lower:
            return game_id
    return None


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
        초기 수집: top all-time posts (복수 서브레딧 지원).

        Args:
            game_id: 게임 ID
            limit: 최대 수집 개수 (전체 서브레딧 합산)

        Yields:
            RawDocument: 수집된 문서
        """
        game_config = get_game_config(game_id)
        started_at = datetime.now(timezone.utc)
        pages_crawled = 0
        error_message = None

        # 각 서브레딧별 수집 개수 분배
        subreddits = game_config.subreddits
        per_sub_limit = limit // len(subreddits)
        # 나머지는 첫 번째 서브레딧에 추가
        extra = limit % len(subreddits)

        try:
            for idx, subreddit in enumerate(subreddits):
                sub_limit = per_sub_limit + (extra if idx == 0 else 0)
                print(f"  [Reddit] Crawling r/{subreddit} (limit: {sub_limit})")

                sub_collected = 0
                for doc in self._crawl_subreddit(subreddit, sub_limit, game_config):
                    pages_crawled += 1
                    sub_collected += 1
                    yield doc

                print(f"    → Collected: {sub_collected}")

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

    def _crawl_subreddit(
        self,
        subreddit: str,
        limit: int,
        game_config: GameConfig,
    ) -> Generator[RawDocument, None, None]:
        """단일 서브레딧에서 top posts 수집."""
        after = None
        collected = 0

        while collected < limit:
            batch_limit = min(100, limit - collected)
            url = f"{self.BASE_URL}/r/{subreddit}/top/.json"
            params = {
                "t": "all",
                "limit": batch_limit,
            }
            if after:
                params["after"] = after

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
                    collected += 1
                    yield doc

            # 다음 페이지
            after = data.get("data", {}).get("after")
            if not after:
                break

            time.sleep(self.delay)

    def crawl_common_subreddit(
        self,
        subreddit: str,
        limit: int = 300,
    ) -> Generator[RawDocument, None, CrawlResult]:
        """
        공통 서브레딧 크롤링 (제목으로 게임 자동 분류).

        r/fromsoftware, r/soulslike, r/shittydarksouls 등에서 수집.
        제목에서 게임 이름을 감지하여 자동 분류.

        Args:
            subreddit: 서브레딧 이름
            limit: 최대 수집 개수

        Yields:
            RawDocument: 수집된 문서 (game_id 자동 분류됨)
        """
        started_at = datetime.now(timezone.utc)
        pages_crawled = 0
        classified_count = 0
        error_message = None

        print(f"  [Reddit Common] Crawling r/{subreddit} (limit: {limit})")

        try:
            after = None
            fetched = 0

            while fetched < limit:
                batch_limit = min(100, limit - fetched)
                url = f"{self.BASE_URL}/r/{subreddit}/top/.json"
                params = {
                    "t": "all",
                    "limit": batch_limit,
                }
                if after:
                    params["after"] = after

                response = self.client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                posts = data.get("data", {}).get("children", [])
                if not posts:
                    break

                for post in posts:
                    post_data = post.get("data", {})
                    fetched += 1

                    # 제목에서 게임 감지
                    title = post_data.get("title", "")
                    game_id = detect_game_from_title(title)

                    if game_id:
                        # 감지된 게임의 설정 사용
                        game_config = get_game_config(game_id)
                        doc = self._process_post(post_data, game_config)
                        if doc:
                            pages_crawled += 1
                            classified_count += 1
                            yield doc

                # 다음 페이지
                after = data.get("data", {}).get("after")
                if not after:
                    break

                time.sleep(self.delay)

            print(f"    → Fetched: {fetched}, Classified: {classified_count}")
            status = "success"

        except httpx.HTTPStatusError as e:
            error_message = f"HTTP {e.response.status_code}: {e.response.text[:200]}"
            status = "failed" if pages_crawled == 0 else "partial"
        except Exception as e:
            error_message = str(e)
            status = "failed" if pages_crawled == 0 else "partial"

        return CrawlResult(
            game_id="common",
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
        주기적 수집: hot posts (복수 서브레딧 지원).
        """
        game_config = get_game_config(game_id)
        started_at = datetime.now(timezone.utc)
        pages_crawled = 0
        error_message = None

        # 각 서브레딧별 수집 개수 분배
        subreddits = game_config.subreddits
        per_sub_limit = limit // len(subreddits)

        try:
            for subreddit in subreddits:
                url = f"{self.BASE_URL}/r/{subreddit}/hot/.json"
                params = {"limit": min(100, per_sub_limit)}

                response = self.client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                for post in data.get("data", {}).get("children", []):
                    post_data = post.get("data", {})
                    doc = self._process_post(post_data, game_config)
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

        # 너무 짧은 콘텐츠 제외 (30자 이상)
        if len(content.strip()) < 30:
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

    # ========== 댓글 수집 ==========

    def crawl_comments(
        self,
        game_id: str,
        post_limit: int = 50,
        comments_per_post: int = 20,
        sort: str = "top",
    ) -> Generator[RawDocument, None, CrawlResult]:
        """
        인기 게시물의 댓글 수집.

        Args:
            game_id: 게임 ID
            post_limit: 댓글을 수집할 게시물 수
            comments_per_post: 게시물당 수집할 댓글 수
            sort: 정렬 방식 (top, best, new)

        Yields:
            RawDocument: 댓글 문서
        """
        game_config = get_game_config(game_id)
        started_at = datetime.now(timezone.utc)
        comments_crawled = 0
        error_message = None

        try:
            # 먼저 인기 게시물 목록 가져오기
            posts = list(self._get_top_posts_for_comments(game_config, post_limit))
            print(f"  [Comments] Found {len(posts)} posts to crawl comments from")

            for post_url, post_title in posts:
                try:
                    for doc in self._crawl_post_comments(
                        post_url, post_title, game_config, comments_per_post, sort
                    ):
                        comments_crawled += 1
                        yield doc
                except Exception as e:
                    print(f"    ✗ Error crawling comments: {e}")
                    continue

                time.sleep(self.delay)

            status = "success"

        except Exception as e:
            error_message = str(e)
            status = "failed" if comments_crawled == 0 else "partial"

        print(f"  [Comments] Total collected: {comments_crawled}")

        return CrawlResult(
            game_id=game_id,
            source_type=SourceType.REDDIT,
            status=status,
            pages_crawled=comments_crawled,
            error_message=error_message,
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
        )

    def _get_top_posts_for_comments(
        self,
        game_config: GameConfig,
        limit: int,
    ) -> Generator[tuple[str, str], None, None]:
        """댓글 수집을 위한 인기 게시물 URL 목록."""
        collected = 0
        per_sub = limit // len(game_config.subreddits)

        for subreddit in game_config.subreddits:
            url = f"{self.BASE_URL}/r/{subreddit}/top/.json"
            params = {"t": "all", "limit": min(100, per_sub)}

            try:
                response = self.client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                for post in data.get("data", {}).get("children", []):
                    post_data = post.get("data", {})
                    # 댓글이 있는 게시물만
                    if post_data.get("num_comments", 0) >= 5:
                        permalink = post_data.get("permalink", "")
                        title = post_data.get("title", "")
                        if permalink:
                            collected += 1
                            yield (permalink, title)
                            if collected >= limit:
                                return

                time.sleep(self.delay)

            except Exception as e:
                print(f"    ✗ Error fetching posts from r/{subreddit}: {e}")

    def _crawl_post_comments(
        self,
        permalink: str,
        post_title: str,
        game_config: GameConfig,
        limit: int,
        sort: str,
    ) -> Generator[RawDocument, None, None]:
        """단일 게시물의 댓글 수집."""
        url = f"{self.BASE_URL}{permalink}.json"
        params = {"sort": sort, "limit": limit}

        response = self.client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        # Reddit 댓글 JSON 구조: [post_data, comments_data]
        if len(data) < 2:
            return

        comments_data = data[1].get("data", {}).get("children", [])

        for comment in comments_data:
            if comment.get("kind") != "t1":  # t1 = comment
                continue

            comment_data = comment.get("data", {})
            doc = self._process_comment(comment_data, post_title, game_config)
            if doc:
                yield doc

    def _process_comment(
        self,
        comment_data: dict,
        post_title: str,
        game_config: GameConfig,
    ) -> RawDocument | None:
        """댓글을 RawDocument로 변환."""
        # 삭제된 댓글 제외
        body = comment_data.get("body", "")
        if not body or body in ["[removed]", "[deleted]"]:
            return None

        # 너무 짧은 댓글 제외 (20자 이상)
        if len(body.strip()) < 20:
            return None

        # upvote 필터 (댓글은 5 이상)
        score = comment_data.get("score", 0)
        if score < 5:
            return None

        # 타임스탬프
        created_utc = comment_data.get("created_utc", 0)
        created_at = datetime.fromtimestamp(created_utc, tz=timezone.utc)

        # 댓글 URL
        permalink = comment_data.get("permalink", "")

        return RawDocument(
            game_id=game_config.id,
            source_type=SourceType.REDDIT,
            source_url=f"https://reddit.com{permalink}" if permalink else "",
            title=f"[Comment] {post_title[:50]}",  # 원본 게시물 제목 포함
            content=body,
            author=comment_data.get("author"),
            created_at=created_at,
            upvotes=score,
            comments_count=0,
            flair=None,
        )

    # ========== 일일 업데이트 (hot + new) ==========

    def crawl_daily(
        self,
        game_id: str,
        hot_limit: int = 100,
        new_limit: int = 50,
        include_comments: bool = True,
        comments_post_limit: int = 20,
    ) -> Generator[RawDocument, None, CrawlResult]:
        """
        일일 업데이트: hot + new + 댓글 수집.

        Args:
            game_id: 게임 ID
            hot_limit: hot 게시물 수집 수
            new_limit: new 게시물 수집 수
            include_comments: 댓글 수집 여부
            comments_post_limit: 댓글 수집할 게시물 수

        Yields:
            RawDocument: 수집된 문서
        """
        game_config = get_game_config(game_id)
        started_at = datetime.now(timezone.utc)
        total_crawled = 0
        error_message = None

        try:
            # 1. Hot posts
            print(f"  [Daily] Crawling /hot (limit: {hot_limit})...")
            hot_count = 0
            for doc in self._crawl_by_sort(game_config, "hot", hot_limit):
                total_crawled += 1
                hot_count += 1
                yield doc
            print(f"    → Hot: {hot_count}")

            # 2. New posts
            print(f"  [Daily] Crawling /new (limit: {new_limit})...")
            new_count = 0
            for doc in self._crawl_by_sort(game_config, "new", new_limit):
                total_crawled += 1
                new_count += 1
                yield doc
            print(f"    → New: {new_count}")

            # 3. Comments (선택적)
            if include_comments:
                print(f"  [Daily] Crawling comments (posts: {comments_post_limit})...")
                comments_count = 0
                for doc in self.crawl_comments(game_id, comments_post_limit, 15):
                    total_crawled += 1
                    comments_count += 1
                    yield doc
                print(f"    → Comments: {comments_count}")

            status = "success"

        except Exception as e:
            error_message = str(e)
            status = "failed" if total_crawled == 0 else "partial"

        return CrawlResult(
            game_id=game_id,
            source_type=SourceType.REDDIT,
            status=status,
            pages_crawled=total_crawled,
            error_message=error_message,
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
        )

    def _crawl_by_sort(
        self,
        game_config: GameConfig,
        sort: str,  # "hot", "new", "rising"
        limit: int,
    ) -> Generator[RawDocument, None, None]:
        """정렬 방식별 게시물 수집."""
        subreddits = game_config.subreddits
        per_sub_limit = limit // len(subreddits)

        for subreddit in subreddits:
            url = f"{self.BASE_URL}/r/{subreddit}/{sort}/.json"
            params = {"limit": min(100, per_sub_limit)}

            try:
                response = self.client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                for post in data.get("data", {}).get("children", []):
                    post_data = post.get("data", {})
                    doc = self._process_post(post_data, game_config)
                    if doc:
                        yield doc

                time.sleep(self.delay)

            except Exception as e:
                print(f"    ✗ Error crawling r/{subreddit}/{sort}: {e}")

    # ========== 초기 + 댓글 통합 수집 ==========

    def crawl_initial_with_comments(
        self,
        game_id: str,
        post_limit: int = 500,
        comments_post_limit: int = 50,
    ) -> Generator[RawDocument, None, CrawlResult]:
        """
        초기 수집 + 댓글 통합.

        Args:
            game_id: 게임 ID
            post_limit: top 게시물 수집 수
            comments_post_limit: 댓글 수집할 게시물 수

        Yields:
            RawDocument: 수집된 문서
        """
        started_at = datetime.now(timezone.utc)
        total_crawled = 0
        error_message = None

        try:
            # 1. Top posts
            print(f"  [Initial] Crawling top posts (limit: {post_limit})...")
            posts_count = 0
            for doc in self.crawl_initial(game_id, post_limit):
                total_crawled += 1
                posts_count += 1
                yield doc
            print(f"    → Posts: {posts_count}")

            # 2. Comments
            print(f"  [Initial] Crawling comments (posts: {comments_post_limit})...")
            comments_count = 0
            for doc in self.crawl_comments(game_id, comments_post_limit, 20):
                total_crawled += 1
                comments_count += 1
                yield doc
            print(f"    → Comments: {comments_count}")

            status = "success"

        except Exception as e:
            error_message = str(e)
            status = "failed" if total_crawled == 0 else "partial"

        return CrawlResult(
            game_id=game_id,
            source_type=SourceType.REDDIT,
            status=status,
            pages_crawled=total_crawled,
            error_message=error_message,
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
        )


# Singleton
_crawler_instance: RedditJsonCrawler | None = None


def get_reddit_json_crawler() -> RedditJsonCrawler:
    """Get RedditJsonCrawler singleton."""
    global _crawler_instance
    if _crawler_instance is None:
        _crawler_instance = RedditJsonCrawler()
    return _crawler_instance
