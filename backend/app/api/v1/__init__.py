from fastapi import APIRouter
from app.api.v1 import ask, games, feedback

router = APIRouter(prefix="/api/v1")

router.include_router(ask.router, tags=["ask"])
router.include_router(games.router, tags=["games"])
router.include_router(feedback.router, tags=["feedback"])
