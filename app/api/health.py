"""Health and Prometheus metrics."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from app.core.config import get_settings
from app.core.redis import get_redis

router = APIRouter(tags=["health"])


@router.get("/healthz")
async def healthz() -> dict:
    settings = get_settings()
    redis = await get_redis()
    return {
        "status": "ok",
        "env": settings.env,
        "runner": settings.runner,
        "database": settings.database_url.split(":")[0],
        "redis": "connected" if redis is not None else "degraded (in-process)",
        "vector_store": settings.vector_store,
    }


@router.get("/metrics", response_class=PlainTextResponse)
async def metrics() -> str:
    from prometheus_client import CONTENT_TYPE_LATEST, generate_latest, REGISTRY

    return PlainTextResponse(content=generate_latest(REGISTRY).decode(), media_type=CONTENT_TYPE_LATEST)
