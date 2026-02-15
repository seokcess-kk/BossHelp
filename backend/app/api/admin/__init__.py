"""Admin API endpoints."""

from fastapi import APIRouter

from .crawl import router as crawl_router

router = APIRouter(prefix="/admin", tags=["admin"])
router.include_router(crawl_router)
