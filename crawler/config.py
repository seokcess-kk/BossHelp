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
    subreddits: list[str]  # 복수형으로 변경 (여러 서브레딧 지원)
    wiki_base_url: str | None
    min_upvotes: int = 10
    flairs: list[str] = field(default_factory=list)


# 게임별 크롤링 설정
GAME_CONFIGS: dict[str, GameConfig] = {
    "elden-ring": GameConfig(
        id="elden-ring",
        subreddits=["Eldenring", "eldenringdiscussion", "EldenRingLoreTalk"],
        wiki_base_url="https://eldenring.wiki.fextralife.com",
        min_upvotes=10,
        flairs=["Guide", "Tips/Hints", "Help", "Strategy", "Lore"],
    ),
    "sekiro": GameConfig(
        id="sekiro",
        subreddits=["Sekiro"],
        wiki_base_url="https://sekiroshadowsdietwice.wiki.fextralife.com",
        min_upvotes=10,
        flairs=["Guide", "Tips", "Help"],
    ),
    "hollow-knight": GameConfig(
        id="hollow-knight",
        subreddits=["HollowKnight", "HollowKnightdaily", "HollowKnightArt", "ASilksong"],
        wiki_base_url="https://hollowknight.wiki.fextralife.com",
        min_upvotes=10,
        flairs=["Guide", "Tips & Tricks", "Help", "Silksong"],
    ),
    # silksong 제거 → hollow-knight로 통합
    "lies-of-p": GameConfig(
        id="lies-of-p",
        subreddits=["LiesOfP"],
        wiki_base_url="https://liesofp.wiki.fextralife.com",
        min_upvotes=10,
        flairs=["Guide", "Tips", "Help", "Build"],
    ),
    # Dark Souls 시리즈
    "dark-souls": GameConfig(
        id="dark-souls",
        subreddits=["darksouls", "darksoulsremastered"],
        wiki_base_url="https://darksouls.wiki.fextralife.com",
        min_upvotes=10,
        flairs=["Help", "Co-op", "PvP", "Lore"],
    ),
    "dark-souls-2": GameConfig(
        id="dark-souls-2",
        subreddits=["DarkSouls2"],
        wiki_base_url="https://darksouls2.wiki.fextralife.com",
        min_upvotes=10,
        flairs=["Help", "Co-op", "Build", "Lore"],
    ),
    "dark-souls-3": GameConfig(
        id="dark-souls-3",
        subreddits=["darksouls3"],
        wiki_base_url="https://darksouls3.wiki.fextralife.com",
        min_upvotes=10,
        flairs=["Help", "Co-op", "Build", "PVP", "Lore"],
    ),
}


# 공통 서브레딧 (제목으로 게임 분류)
COMMON_SUBREDDITS = ["fromsoftware", "soulslike", "shittydarksouls"]


# 게임 이름 매핑 (제목 자동 분류용)
GAME_NAME_MAPPING = {
    # Elden Ring
    "elden ring": "elden-ring",
    "eldenring": "elden-ring",
    # Dark Souls 3
    "dark souls 3": "dark-souls-3",
    "dark souls iii": "dark-souls-3",
    "ds3": "dark-souls-3",
    "darksouls3": "dark-souls-3",
    # Dark Souls 2
    "dark souls 2": "dark-souls-2",
    "dark souls ii": "dark-souls-2",
    "ds2": "dark-souls-2",
    "darksouls2": "dark-souls-2",
    # Dark Souls 1
    "dark souls": "dark-souls",
    "ds1": "dark-souls",
    "darksouls": "dark-souls",
    "dark souls remastered": "dark-souls",
    # Sekiro
    "sekiro": "sekiro",
    # Hollow Knight
    "hollow knight": "hollow-knight",
    "hollowknight": "hollow-knight",
    "silksong": "hollow-knight",  # Silksong → hollow-knight
    # Lies of P
    "lies of p": "lies-of-p",
    "liesofp": "lies-of-p",
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
