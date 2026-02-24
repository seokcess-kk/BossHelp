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


# 게임 이름 매핑 (제목 자동 분류용) - 보스/캐릭터명 포함
GAME_NAME_MAPPING = {
    # ========== Elden Ring ==========
    "elden ring": "elden-ring",
    "eldenring": "elden-ring",
    # Elden Ring 보스/캐릭터
    "malenia": "elden-ring",
    "radahn": "elden-ring",
    "morgott": "elden-ring",
    "godrick": "elden-ring",
    "rennala": "elden-ring",
    "radagon": "elden-ring",
    "maliketh": "elden-ring",
    "mohg": "elden-ring",
    "godfrey": "elden-ring",
    "margit": "elden-ring",
    "ranni": "elden-ring",
    "melina": "elden-ring",
    "torrent": "elden-ring",
    "tarnished": "elden-ring",
    "lands between": "elden-ring",
    "moonveil": "elden-ring",
    "rivers of blood": "elden-ring",
    "mimic tear": "elden-ring",
    "let me solo her": "elden-ring",

    # ========== Dark Souls 3 ==========
    "dark souls 3": "dark-souls-3",
    "dark souls iii": "dark-souls-3",
    "ds3": "dark-souls-3",
    "darksouls3": "dark-souls-3",
    # DS3 보스/캐릭터
    "nameless king": "dark-souls-3",
    "soul of cinder": "dark-souls-3",
    "pontiff sulyvahn": "dark-souls-3",
    "sulyvahn": "dark-souls-3",
    "abyss watchers": "dark-souls-3",
    "dancer of the boreal": "dark-souls-3",
    "yhorm": "dark-souls-3",
    "aldrich": "dark-souls-3",
    "twin princes": "dark-souls-3",
    "lorian": "dark-souls-3",
    "lothric": "dark-souls-3",
    "sister friede": "dark-souls-3",
    "friede": "dark-souls-3",
    "slave knight gael": "dark-souls-3",
    "gael": "dark-souls-3",
    "midir": "dark-souls-3",
    "ashen one": "dark-souls-3",
    "firelink shrine": "dark-souls-3",

    # ========== Dark Souls 2 ==========
    "dark souls 2": "dark-souls-2",
    "dark souls ii": "dark-souls-2",
    "ds2": "dark-souls-2",
    "darksouls2": "dark-souls-2",
    "scholar of the first sin": "dark-souls-2",
    "sotfs": "dark-souls-2",
    # DS2 보스/캐릭터
    "fume knight": "dark-souls-2",
    "sir alonne": "dark-souls-2",
    "sinh": "dark-souls-2",
    "ivory king": "dark-souls-2",
    "burnt ivory king": "dark-souls-2",
    "velstadt": "dark-souls-2",
    "looking glass knight": "dark-souls-2",
    "pursuer": "dark-souls-2",
    "smelter demon": "dark-souls-2",
    "nashandra": "dark-souls-2",
    "vendrick": "dark-souls-2",
    "majula": "dark-souls-2",
    "bearer of the curse": "dark-souls-2",

    # ========== Dark Souls 1 ==========
    "dark souls remastered": "dark-souls",
    "dsr": "dark-souls",
    "ds1": "dark-souls",
    # DS1 보스/캐릭터 (주의: "dark souls" 단독은 마지막에)
    "ornstein": "dark-souls",
    "smough": "dark-souls",
    "o&s": "dark-souls",
    "artorias": "dark-souls",
    "sif": "dark-souls",
    "great grey wolf": "dark-souls",
    "gwyn": "dark-souls",
    "lord of cinder": "dark-souls",  # DS1 specific context
    "kalameet": "dark-souls",
    "manus": "dark-souls",
    "quelaag": "dark-souls",
    "nito": "dark-souls",
    "seath": "dark-souls",
    "four kings": "dark-souls",
    "solaire": "dark-souls",
    "praise the sun": "dark-souls",
    "patches": "dark-souls",
    "lordran": "dark-souls",
    "chosen undead": "dark-souls",
    "anor londo": "dark-souls",
    "darksouls": "dark-souls",
    "dark souls": "dark-souls",  # 가장 마지막에 (다른 DS 시리즈 먼저 매칭)

    # ========== Sekiro ==========
    "sekiro": "sekiro",
    "shadows die twice": "sekiro",
    # Sekiro 보스/캐릭터
    "isshin": "sekiro",
    "sword saint": "sekiro",
    "genichiro": "sekiro",
    "guardian ape": "sekiro",
    "headless ape": "sekiro",
    "owl": "sekiro",
    "great shinobi": "sekiro",
    "lady butterfly": "sekiro",
    "gyoubu": "sekiro",
    "emma": "sekiro",
    "wolf": "sekiro",
    "shinobi": "sekiro",
    "ashina": "sekiro",
    "divine dragon": "sekiro",
    "demon of hatred": "sekiro",
    "kuro": "sekiro",

    # ========== Hollow Knight ==========
    "hollow knight": "hollow-knight",
    "hollowknight": "hollow-knight",
    "silksong": "hollow-knight",
    # Hollow Knight 보스/캐릭터
    "hornet": "hollow-knight",
    "the knight": "hollow-knight",
    "grimm": "hollow-knight",
    "nightmare king": "hollow-knight",
    "nkg": "hollow-knight",
    "radiance": "hollow-knight",
    "absolute radiance": "hollow-knight",
    "pure vessel": "hollow-knight",
    "grey prince zote": "hollow-knight",
    "zote": "hollow-knight",
    "soul master": "hollow-knight",
    "mantis lords": "hollow-knight",
    "sisters of battle": "hollow-knight",
    "hallownest": "hollow-knight",
    "pale king": "hollow-knight",
    "white lady": "hollow-knight",
    "void": "hollow-knight",
    "charm": "hollow-knight",
    "geo": "hollow-knight",
    "dirtmouth": "hollow-knight",
    "godhome": "hollow-knight",
    "pantheon": "hollow-knight",

    # ========== Lies of P ==========
    "lies of p": "lies-of-p",
    "liesofp": "lies-of-p",
    "lie of p": "lies-of-p",
    # Lies of P 보스/캐릭터
    "pinocchio": "lies-of-p",
    "sophia": "lies-of-p",
    "geppetto": "lies-of-p",
    "fallen archbishop": "lies-of-p",
    "king of puppets": "lies-of-p",
    "simon manus": "lies-of-p",
    "laxasia": "lies-of-p",
    "victor": "lies-of-p",
    "scrapped watchman": "lies-of-p",
    "puppet": "lies-of-p",
    "ergo": "lies-of-p",
    "krat": "lies-of-p",
    "hotel krat": "lies-of-p",
    "stalker": "lies-of-p",
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
