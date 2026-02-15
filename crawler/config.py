"""Configuration for BossHelp Data Pipeline."""

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class RedditConfig:
    """Reddit API configuration."""
    client_id: str = field(default_factory=lambda: os.getenv("REDDIT_CLIENT_ID", ""))
    client_secret: str = field(default_factory=lambda: os.getenv("REDDIT_CLIENT_SECRET", ""))
    user_agent: str = field(default_factory=lambda: os.getenv("REDDIT_USER_AGENT", "BossHelp/1.0"))


@dataclass
class GameConfig:
    """Game-specific crawling configuration."""
    id: str
    subreddit: str
    wiki_base_url: str | None
    min_upvotes: int = 10
    flairs: list[str] = field(default_factory=list)


# 게임별 크롤링 설정
GAME_CONFIGS: dict[str, GameConfig] = {
    "elden-ring": GameConfig(
        id="elden-ring",
        subreddit="Eldenring",
        wiki_base_url="https://eldenring.wiki.fextralife.com",
        min_upvotes=10,
        flairs=["Guide", "Tips/Hints", "Help", "Strategy"],
    ),
    "sekiro": GameConfig(
        id="sekiro",
        subreddit="Sekiro",
        wiki_base_url="https://sekiroshadowsdietwice.wiki.fextralife.com",
        min_upvotes=10,
        flairs=["Guide", "Tips", "Help"],
    ),
    "hollow-knight": GameConfig(
        id="hollow-knight",
        subreddit="HollowKnight",
        wiki_base_url="https://hollowknight.wiki.fextralife.com",
        min_upvotes=10,
        flairs=["Guide", "Tips & Tricks", "Help"],
    ),
    "silksong": GameConfig(
        id="silksong",
        subreddit="HollowKnight",
        wiki_base_url=None,  # 아직 출시 전
        min_upvotes=5,
        flairs=["Silksong", "News"],
    ),
    "lies-of-p": GameConfig(
        id="lies-of-p",
        subreddit="LiesOfP",
        wiki_base_url="https://liesofp.wiki.fextralife.com",
        min_upvotes=10,
        flairs=["Guide", "Tips", "Help", "Build"],
    ),
}


@dataclass
class PipelineConfig:
    """Pipeline configuration."""
    # Supabase
    supabase_url: str = field(default_factory=lambda: os.getenv("SUPABASE_URL", ""))
    supabase_key: str = field(default_factory=lambda: os.getenv("SUPABASE_SERVICE_KEY", ""))

    # OpenAI
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    embedding_model: str = "text-embedding-3-small"

    # Chunking
    max_chunk_tokens: int = 500
    overlap_tokens: int = 100

    # Quality
    min_quality_score: float = 0.3

    # Rate limiting
    reddit_delay: float = 1.0
    wiki_delay: float = 1.5
    embedding_batch_size: int = 100


def get_pipeline_config() -> PipelineConfig:
    """Get pipeline configuration."""
    return PipelineConfig()


def get_reddit_config() -> RedditConfig:
    """Get Reddit configuration."""
    return RedditConfig()


def get_game_config(game_id: str) -> GameConfig:
    """Get game-specific configuration."""
    if game_id not in GAME_CONFIGS:
        raise ValueError(f"Unknown game: {game_id}")
    return GAME_CONFIGS[game_id]
