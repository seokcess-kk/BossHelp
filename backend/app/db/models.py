from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime


# ==================== Enums ====================
SpoilerLevel = Literal["none", "light", "heavy"]
ConfidenceLevel = Literal["high", "medium", "low"]
Category = Literal[
    "boss_guide",
    "build_guide",
    "progression_route",
    "npc_quest",
    "item_location",
    "mechanic_tip",
    "secret_hidden",
]
SourceType = Literal["reddit", "wiki", "steam"]
Genre = Literal["soulslike", "metroidvania", "action_rpg"]


# ==================== Request Models ====================
class AskRequest(BaseModel):
    game_id: str = Field(..., min_length=1, max_length=50)
    question: str = Field(..., min_length=1, max_length=500)
    spoiler_level: SpoilerLevel = "none"
    session_id: str = Field(..., min_length=1, max_length=100)
    category: Category | None = None
    expand: bool = False


class FeedbackRequest(BaseModel):
    conversation_id: str
    is_helpful: bool


# ==================== Response Models ====================
class Source(BaseModel):
    url: str
    title: str
    source_type: SourceType
    quality_score: float = Field(..., ge=0, le=1)


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]
    conversation_id: str
    has_detail: bool
    is_early_data: bool = False
    latency_ms: int
    confidence: ConfidenceLevel = "medium"
    cached: bool = False


class Game(BaseModel):
    id: str
    title: str
    genre: Genre
    thumbnail_url: str | None = None
    is_active: bool = True


class GamesResponse(BaseModel):
    games: list[Game]


class PopularQuestion(BaseModel):
    question: str
    category: Category
    ask_count: int


class PopularQuestionsResponse(BaseModel):
    questions: list[PopularQuestion]


class FeedbackResponse(BaseModel):
    success: bool


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
