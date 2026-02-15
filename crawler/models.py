"""Data models for BossHelp Data Pipeline."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Literal


class SourceType(str, Enum):
    """Source type enum."""
    REDDIT = "reddit"
    WIKI = "wiki"
    STEAM = "steam"


class Category(str, Enum):
    """Content category enum."""
    BOSS_GUIDE = "boss_guide"
    BUILD_GUIDE = "build_guide"
    PROGRESSION_ROUTE = "progression_route"
    NPC_QUEST = "npc_quest"
    ITEM_LOCATION = "item_location"
    MECHANIC_TIP = "mechanic_tip"
    SECRET_HIDDEN = "secret_hidden"


class SpoilerLevel(str, Enum):
    """Spoiler level enum."""
    NONE = "none"
    LIGHT = "light"
    HEAVY = "heavy"


@dataclass
class RawDocument:
    """Raw document from crawler."""
    game_id: str
    source_type: SourceType
    source_url: str
    title: str
    content: str

    # Metadata
    author: str | None = None
    created_at: datetime | None = None
    upvotes: int = 0
    comments_count: int = 0
    flair: str | None = None

    # Wiki specific
    page_category: str | None = None
    last_edited: datetime | None = None


@dataclass
class CleanedDocument:
    """Cleaned and processed document."""
    game_id: str
    source_type: SourceType
    source_url: str
    title: str
    content: str  # Cleaned content

    # Original metadata
    original_length: int = 0
    cleaned_length: int = 0
    upvotes: int = 0
    created_at: datetime | None = None
    flair: str | None = None


@dataclass
class ClassifiedDocument:
    """Document with category classification."""
    game_id: str
    source_type: SourceType
    source_url: str
    title: str
    content: str

    # Classification
    category: Category = Category.MECHANIC_TIP
    category_confidence: float = 0.5
    spoiler_level: SpoilerLevel = SpoilerLevel.NONE
    entity_tags: list[str] = field(default_factory=list)

    # Original metadata
    upvotes: int = 0
    created_at: datetime | None = None


@dataclass
class ScoredDocument:
    """Document with quality score."""
    game_id: str
    source_type: SourceType
    source_url: str
    title: str
    content: str
    category: Category
    spoiler_level: SpoilerLevel
    entity_tags: list[str]

    # Quality
    quality_score: float = 0.5

    # Original metadata
    upvotes: int = 0
    created_at: datetime | None = None


@dataclass
class Chunk:
    """Text chunk ready for embedding."""
    game_id: str
    source_type: SourceType
    source_url: str
    title: str
    content: str
    category: Category
    spoiler_level: SpoilerLevel
    entity_tags: list[str]
    quality_score: float

    # Chunk metadata
    chunk_index: int = 0
    total_chunks: int = 1
    token_count: int = 0


@dataclass
class EmbeddedChunk:
    """Chunk with embedding vector."""
    game_id: str
    source_type: SourceType
    source_url: str
    title: str
    content: str
    category: Category
    spoiler_level: SpoilerLevel
    entity_tags: list[str]
    quality_score: float

    # Embedding
    embedding: list[float] = field(default_factory=list)

    # Chunk metadata
    chunk_index: int = 0
    total_chunks: int = 1


@dataclass
class CrawlResult:
    """Result of a crawl operation."""
    game_id: str
    source_type: SourceType
    status: Literal["success", "failed", "partial"]
    pages_crawled: int = 0
    chunks_created: int = 0
    error_message: str | None = None
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime | None = None
