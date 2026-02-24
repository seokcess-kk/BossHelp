"""Streaming Ask API endpoint for BossHelp."""

import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.db.models import AskRequest
from app.db.supabase import get_supabase_client

router = APIRouter()


async def validate_game_id(game_id: str) -> bool:
    """Validate game_id exists in database."""
    client = get_supabase_client()
    result = client.table("games").select("id").eq("id", game_id).eq("is_active", True).execute()
    return len(result.data) > 0


@router.post("/ask/stream")
async def ask_stream(request: AskRequest):
    """
    Ask a question and get a streaming AI-powered answer using RAG pipeline.

    Returns Server-Sent Events (SSE) with:
    - type: "sources" - Retrieved sources metadata
    - type: "text" - Answer text chunks
    - type: "meta" - Metadata (confidence, latency)
    - type: "done" - Completion signal
    - type: "error" - Error message
    """
    # Validate game exists in DB
    if not await validate_game_id(request.game_id):
        raise HTTPException(status_code=400, detail=f"Invalid game_id: {request.game_id}")

    async def generate():
        from app.core.rag.pipeline import get_rag_pipeline

        pipeline = get_rag_pipeline()

        try:
            # Step 1: Prepare context (sources)
            context = pipeline.prepare_context(
                question=request.question,
                game_id=request.game_id,
                spoiler_level=request.spoiler_level,
                category=request.category,
            )

            # Send sources first
            sources_data = [
                {
                    "url": s.get("source_url", ""),
                    "title": s.get("title", ""),
                    "source_type": s.get("source_type", "unknown"),
                    "quality_score": s.get("quality_score", 0.5),
                }
                for s in context["chunks"][:5]
            ]
            yield f"data: {json.dumps({'type': 'sources', 'data': sources_data})}\n\n"

            # Send confidence level
            yield f"data: {json.dumps({'type': 'meta', 'data': {'confidence': context['confidence']}})}\n\n"

            # Step 2: Stream answer
            for text_chunk in pipeline.run_stream(
                question=request.question,
                game_id=request.game_id,
                spoiler_level=request.spoiler_level,
                chunks=context["chunks"],
                expanded=request.expand,
            ):
                yield f"data: {json.dumps({'type': 'text', 'data': text_chunk})}\n\n"

            # Step 3: Send completion with metadata
            yield f"data: {json.dumps({'type': 'meta', 'data': {'latency_ms': context.get('latency_ms', 0)}})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            # Send error event
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
