"""BossHelp Data Pipeline.

Data collection and processing pipeline for game guides.
"""

from .pipeline import DataPipeline, get_pipeline
from .models import (
    SourceType,
    Category,
    SpoilerLevel,
    RawDocument,
    EmbeddedChunk,
    CrawlResult,
)

__all__ = [
    "DataPipeline",
    "get_pipeline",
    "SourceType",
    "Category",
    "SpoilerLevel",
    "RawDocument",
    "EmbeddedChunk",
    "CrawlResult",
]

__version__ = "1.0.0"
