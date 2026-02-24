"""Ask API endpoint for BossHelp."""

import uuid
from fastapi import APIRouter, HTTPException

from app.db.models import AskRequest, AskResponse, Source
from app.db.supabase import get_supabase_client

router = APIRouter()


async def validate_game_id(game_id: str) -> bool:
    """Validate game_id exists in database."""
    client = get_supabase_client()
    result = client.table("games").select("id").eq("id", game_id).eq("is_active", True).execute()
    return len(result.data) > 0


@router.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    """
    Ask a question and get an AI-powered answer using RAG pipeline.
    """
    # Validate game exists in DB
    if not await validate_game_id(request.game_id):
        raise HTTPException(status_code=400, detail=f"Invalid game_id: {request.game_id}")

    # Use RAG pipeline
    return await _ask_with_rag(request)


async def _ask_with_rag(request: AskRequest) -> AskResponse:
    """Process question using RAG pipeline."""
    from app.core.rag.pipeline import get_rag_pipeline

    pipeline = get_rag_pipeline()

    result = pipeline.run(
        question=request.question,
        game_id=request.game_id,
        spoiler_level=request.spoiler_level,
        category=request.category,
        expanded=request.expand,
    )

    # Convert sources to response format
    sources = [
        Source(
            url=s["url"],
            title=s["title"],
            source_type=s["source_type"],
            quality_score=s["quality_score"],
        )
        for s in result.sources
    ]

    # TODO: Save conversation to database
    conversation_id = str(uuid.uuid4())

    return AskResponse(
        answer=result.answer,
        sources=sources,
        conversation_id=conversation_id,
        has_detail=result.has_detail,
        is_early_data=result.is_early_data,
        latency_ms=result.latency_ms,
        confidence=result.confidence,
        cached=result.cached,
    )
