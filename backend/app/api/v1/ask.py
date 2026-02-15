"""Ask API endpoint for BossHelp."""

import os
import uuid
import time
from fastapi import APIRouter, HTTPException

from app.db.models import AskRequest, AskResponse, Source
from app.config import get_settings

router = APIRouter()

# Check if RAG is available (API keys configured)
def is_rag_available() -> bool:
    """Check if RAG pipeline dependencies are available."""
    settings = get_settings()
    return bool(
        getattr(settings, "ANTHROPIC_API_KEY", None) and
        getattr(settings, "OPENAI_API_KEY", None) and
        getattr(settings, "SUPABASE_URL", None)
    )


# Mock responses for development (fallback when RAG not available)
MOCK_RESPONSES = {
    "elden-ring": {
        "default": "엘든 링에 대한 질문이시군요! 아직 백엔드 RAG 파이프라인이 연결되지 않았습니다. 실제 서비스에서는 Reddit, Wiki 등의 검증된 데이터를 기반으로 정확한 답변을 제공합니다.",
        "말레니아": "말레니아(Malenia)는 출혈 빌드가 효과적입니다. 리버스 오브 블러드나 강타의 물든 피 같은 무기를 추천합니다. 1페이즈에서는 물흐름검을 조심하세요 - 굴러서 피하거나, 패링으로 대응할 수 있습니다. 2페이즈에서는 꽃 폭발 패턴에 주의하고, 거리를 유지하면서 기회를 노리세요.",
    },
    "sekiro": {
        "default": "세키로에 대한 질문이시군요! 아직 백엔드가 연결되지 않았습니다.",
        "겐이치로": "겐이치로 아시나는 튕겨내기가 핵심입니다. 그의 연속 공격을 침착하게 튕겨내고, 번개 반사를 활용하세요. 3페이즈에서 번개 공격이 나오면 점프 후 공격 버튼으로 반사할 수 있습니다.",
    },
}

VALID_GAMES = ["elden-ring", "sekiro", "hollow-knight", "silksong", "lies-of-p"]


@router.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    """
    Ask a question and get an AI-powered answer.

    Uses RAG pipeline when available, falls back to mock responses otherwise.
    """
    # Validate game exists
    if request.game_id not in VALID_GAMES:
        raise HTTPException(status_code=400, detail="Invalid game_id")

    # Try RAG pipeline if available
    if is_rag_available():
        try:
            return await _ask_with_rag(request)
        except Exception as e:
            # Log error and fall back to mock
            print(f"RAG pipeline error: {e}")
            return await _ask_with_mock(request)
    else:
        return await _ask_with_mock(request)


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
    )


async def _ask_with_mock(request: AskRequest) -> AskResponse:
    """Process question using mock responses (development mode)."""
    start_time = time.time()

    game_responses = MOCK_RESPONSES.get(
        request.game_id,
        {"default": "해당 게임에 대한 정보가 준비 중입니다."}
    )

    # Simple keyword matching for demo
    answer = game_responses["default"]
    for keyword, response in game_responses.items():
        if keyword != "default" and keyword in request.question:
            answer = response
            break

    # Add development mode notice
    answer = f"[개발 모드] {answer}"

    # Mock sources
    sources = [
        Source(
            url=f"https://reddit.com/r/{request.game_id.replace('-', '')}/example",
            title="Community Guide",
            source_type="reddit",
            quality_score=0.85,
        ),
        Source(
            url=f"https://{request.game_id.replace('-', '')}.wiki.fextralife.com",
            title="Wiki Guide",
            source_type="wiki",
            quality_score=0.90,
        ),
    ]

    latency_ms = int((time.time() - start_time) * 1000)

    return AskResponse(
        answer=answer,
        sources=sources,
        conversation_id=str(uuid.uuid4()),
        has_detail=True,
        is_early_data=False,
        latency_ms=latency_ms,
    )
