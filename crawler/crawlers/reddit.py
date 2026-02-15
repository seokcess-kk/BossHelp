"""Reddit Crawler for BossHelp.

PRAW (Python Reddit API Wrapper)를 사용하여 Reddit 데이터를 수집합니다.
Rate: 100 QPM (Free tier)
Filters: upvote >= 10, flair in [Guide, Tips, Help]
"""

import time
from datetime import datetime, timezone
from typing import Generator

import praw
from praw.models import Submission

from crawler.config import get_reddit_config, get_game_config, GameConfig
from crawler.models import RawDocument, SourceType, CrawlResult


class RedditCrawler:
    """Reddit 데이터 수집기."""

    def __init__(self):
        config = get_reddit_config()
        self.reddit = praw.Reddit(
            client_id=config.client_id,
            client_secret=config.client_secret,
            user_agent=config.user_agent,
        )
        self.delay = 1.0  # Rate limit delay

    def crawl_initial(
        self,
        game_id: str,
        limit: int = 1000,
    ) -> Generator[RawDocument, None, CrawlResult]:
        """
        초기 수집: top all-time posts.

        Args:
            game_id: 게임 ID
            limit: 최대 수집 개수

        Yields:
            RawDocument: 수집된 문서

        Returns:
            CrawlResult: 수집 결과
        """
        game_config = get_game_config(game_id)
        started_at = datetime.now(timezone.utc)
        pages_crawled = 0
        error_message = None

        try:
            subreddit = self.reddit.subreddit(game_config.subreddit)

            # top all-time
            for submission in subreddit.top(time_filter="all", limit=limit):
                doc = self._process_submission(submission, game_config)
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

    def crawl_recent(
        self,
        game_id: str,
        limit: int = 100,
    ) -> Generator[RawDocument, None, CrawlResult]:
        """
        주기적 수집: new + hot posts.

        Args:
            game_id: 게임 ID
            limit: 최대 수집 개수 (각 카테고리당)

        Yields:
            RawDocument: 수집된 문서

        Returns:
            CrawlResult: 수집 결과
        """
        game_config = get_game_config(game_id)
        started_at = datetime.now(timezone.utc)
        pages_crawled = 0
        seen_ids: set[str] = set()
        error_message = None

        try:
            subreddit = self.reddit.subreddit(game_config.subreddit)

            # Hot posts
            for submission in subreddit.hot(limit=limit // 2):
                if submission.id in seen_ids:
                    continue
                seen_ids.add(submission.id)

                doc = self._process_submission(submission, game_config)
                if doc:
                    pages_crawled += 1
                    yield doc
                time.sleep(self.delay)

            # New posts
            for submission in subreddit.new(limit=limit // 2):
                if submission.id in seen_ids:
                    continue
                seen_ids.add(submission.id)

                doc = self._process_submission(submission, game_config)
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

    def _process_submission(
        self,
        submission: Submission,
        game_config: GameConfig,
    ) -> RawDocument | None:
        """
        Submission을 RawDocument로 변환.

        필터링:
        - upvote >= min_upvotes
        - flair 매칭 (설정된 경우)
        - 삭제/제거된 게시물 제외
        """
        # 삭제된 게시물 제외
        if submission.removed_by_category or submission.selftext == "[removed]":
            return None

        # upvote 필터
        if submission.score < game_config.min_upvotes:
            return None

        # flair 필터 (설정된 경우)
        if game_config.flairs:
            flair = submission.link_flair_text or ""
            if not any(f.lower() in flair.lower() for f in game_config.flairs):
                # Flair가 없어도 높은 upvote면 포함
                if submission.score < game_config.min_upvotes * 5:
                    return None

        # 콘텐츠 구성 (본문 + 상위 댓글)
        content_parts = [submission.selftext or ""]

        # 상위 댓글 추가 (upvote 높은 순, 최대 5개)
        submission.comment_sort = "best"
        submission.comments.replace_more(limit=0)
        top_comments = sorted(
            submission.comments.list()[:20],
            key=lambda c: c.score,
            reverse=True,
        )[:5]

        for comment in top_comments:
            if comment.score >= 5 and len(comment.body) > 50:
                content_parts.append(f"\n---\n[Comment +{comment.score}]\n{comment.body}")

        content = "\n".join(content_parts)

        # 너무 짧은 콘텐츠 제외
        if len(content.strip()) < 100:
            return None

        return RawDocument(
            game_id=game_config.id,
            source_type=SourceType.REDDIT,
            source_url=f"https://reddit.com{submission.permalink}",
            title=submission.title,
            content=content,
            author=str(submission.author) if submission.author else None,
            created_at=datetime.fromtimestamp(submission.created_utc, tz=timezone.utc),
            upvotes=submission.score,
            comments_count=submission.num_comments,
            flair=submission.link_flair_text,
        )
