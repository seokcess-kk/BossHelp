from fastapi import APIRouter
from app.db.models import FeedbackRequest, FeedbackResponse

router = APIRouter()


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest):
    """Submit feedback for a conversation."""
    # TODO: Replace with actual DB call
    # await db.update_feedback(request.conversation_id, request.is_helpful)

    # For now, just return success
    return FeedbackResponse(success=True)
