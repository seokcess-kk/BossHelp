"""Admin Crawl API endpoints for BossHelp.

수동 크롤링 트리거 및 상태 조회를 위한 Admin API.
"""

import os
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, HTTPException, Header, BackgroundTasks
from pydantic import BaseModel

from app.config import get_settings

router = APIRouter()


class CrawlRequest(BaseModel):
    """크롤링 요청."""
    game_ids: list[str] | None = None
    sources: list[Literal["reddit", "wiki"]] | None = None
    mode: Literal["initial", "update"] = "update"
    reddit_limit: int = 100
    wiki_limit: int = 50


class CrawlStatus(BaseModel):
    """크롤링 상태."""
    game_id: str
    source_type: str
    status: str
    pages_crawled: int
    chunks_created: int
    error_message: str | None
    started_at: datetime
    completed_at: datetime | None


class CrawlResponse(BaseModel):
    """크롤링 응답."""
    job_id: str
    status: str
    message: str


class ChunkStats(BaseModel):
    """청크 통계."""
    game_id: str
    total_chunks: int
    by_category: dict[str, int]
    by_source: dict[str, int]
    avg_quality_score: float


# 간단한 인메모리 작업 상태 (실제 운영에서는 Redis 등 사용)
_crawl_jobs: dict[str, dict] = {}


def verify_admin_key(x_admin_key: str = Header(...)) -> bool:
    """Admin API 키 검증."""
    settings = get_settings()
    expected_key = getattr(settings, "ADMIN_API_KEY", None)

    if not expected_key:
        raise HTTPException(
            status_code=500,
            detail="Admin API key not configured",
        )

    if x_admin_key != expected_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid admin API key",
        )

    return True


@router.post("/crawl", response_model=CrawlResponse)
async def trigger_crawl(
    request: CrawlRequest,
    background_tasks: BackgroundTasks,
    x_admin_key: str = Header(...),
):
    """
    크롤링 작업 트리거.

    백그라운드에서 크롤링을 실행하고 job_id를 반환합니다.
    """
    verify_admin_key(x_admin_key)

    # Job ID 생성
    job_id = f"crawl_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    # 작업 상태 초기화
    _crawl_jobs[job_id] = {
        "status": "queued",
        "request": request.model_dump(),
        "started_at": datetime.now(timezone.utc).isoformat(),
        "results": [],
    }

    # 백그라운드 작업 등록
    background_tasks.add_task(
        run_crawl_job,
        job_id,
        request,
    )

    return CrawlResponse(
        job_id=job_id,
        status="queued",
        message=f"Crawl job {job_id} queued",
    )


async def run_crawl_job(job_id: str, request: CrawlRequest):
    """백그라운드 크롤링 작업 실행."""
    try:
        _crawl_jobs[job_id]["status"] = "running"

        # 실제 크롤링 파이프라인 호출
        # 주의: crawler 패키지가 설치되어 있어야 함
        try:
            from crawler.pipeline import get_pipeline
            from crawler.models import SourceType

            pipeline = get_pipeline()

            sources = None
            if request.sources:
                sources = [
                    SourceType.REDDIT if s == "reddit" else SourceType.WIKI
                    for s in request.sources
                ]

            if request.mode == "initial":
                results = pipeline.run_initial(
                    game_ids=request.game_ids,
                    sources=sources,
                    reddit_limit=request.reddit_limit,
                    wiki_limit_per_category=request.wiki_limit,
                )
            else:
                results = pipeline.run_update(
                    game_ids=request.game_ids,
                    reddit_limit=request.reddit_limit,
                )

            # 결과 저장
            _crawl_jobs[job_id]["results"] = [
                {
                    "key": key,
                    "status": r.status,
                    "pages_crawled": r.pages_crawled,
                    "chunks_created": r.chunks_created,
                    "error": r.error_message,
                }
                for key, r in results.items()
            ]
            _crawl_jobs[job_id]["status"] = "completed"

        except ImportError:
            # Crawler 패키지가 없는 경우 (개발 환경)
            _crawl_jobs[job_id]["status"] = "completed"
            _crawl_jobs[job_id]["results"] = [
                {
                    "message": "Crawler package not installed. "
                               "Run: pip install -e ../crawler",
                }
            ]

    except Exception as e:
        _crawl_jobs[job_id]["status"] = "failed"
        _crawl_jobs[job_id]["error"] = str(e)

    finally:
        _crawl_jobs[job_id]["completed_at"] = (
            datetime.now(timezone.utc).isoformat()
        )


@router.get("/crawl/{job_id}")
async def get_crawl_status(
    job_id: str,
    x_admin_key: str = Header(...),
):
    """크롤링 작업 상태 조회."""
    verify_admin_key(x_admin_key)

    if job_id not in _crawl_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    return _crawl_jobs[job_id]


@router.get("/crawl")
async def list_crawl_jobs(
    x_admin_key: str = Header(...),
    limit: int = 10,
):
    """최근 크롤링 작업 목록."""
    verify_admin_key(x_admin_key)

    # 최근 작업 반환
    jobs = list(_crawl_jobs.items())[-limit:]
    return {"jobs": [{"job_id": k, **v} for k, v in jobs]}


@router.get("/stats/{game_id}", response_model=ChunkStats)
async def get_chunk_stats(
    game_id: str,
    x_admin_key: str = Header(...),
):
    """게임별 청크 통계."""
    verify_admin_key(x_admin_key)

    # Supabase에서 통계 조회
    try:
        from app.db.supabase import get_supabase_client

        client = get_supabase_client()

        # 총 청크 수
        total_result = (
            client.table("chunks")
            .select("id", count="exact")
            .eq("game_id", game_id)
            .eq("is_active", True)
            .execute()
        )
        total_chunks = total_result.count or 0

        # 카테고리별 집계
        chunks_data = (
            client.table("chunks")
            .select("category, source_type, quality_score")
            .eq("game_id", game_id)
            .eq("is_active", True)
            .execute()
        )

        by_category: dict[str, int] = {}
        by_source: dict[str, int] = {}
        quality_scores: list[float] = []

        for chunk in chunks_data.data or []:
            cat = chunk.get("category", "unknown")
            src = chunk.get("source_type", "unknown")
            score = chunk.get("quality_score", 0.5)

            by_category[cat] = by_category.get(cat, 0) + 1
            by_source[src] = by_source.get(src, 0) + 1
            quality_scores.append(score)

        avg_quality = (
            sum(quality_scores) / len(quality_scores)
            if quality_scores
            else 0.0
        )

        return ChunkStats(
            game_id=game_id,
            total_chunks=total_chunks,
            by_category=by_category,
            by_source=by_source,
            avg_quality_score=round(avg_quality, 3),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get stats: {e}",
        )
