"""ARQ background task implementations."""

from __future__ import annotations

from typing import Any

from app.core.config import get_settings


async def run_attack_run(ctx: dict[str, Any], run_id: str) -> str:
    """Execute an attack run. Enqueued by the API when AEGIS_RUNNER=arq."""
    from app.services.runner import execute_run

    if not run_id:
        raise ValueError("run_id is required")
    await execute_run(run_id)
    return f"completed:{run_id}"


async def generate_run_reports(ctx: dict[str, Any], run_id: str, formats: list[str]) -> dict:
    """Generate report artifacts for a run (used by CI integrations)."""
    from app.core.db import get_session_factory
    from app.reporting.report_service import generate_report

    session = get_session_factory()()
    try:
        produced = {}
        for fmt in formats:
            report = await generate_report(session, run_id, fmt, generated_by="worker")
            produced[fmt] = report.storage_path
        await session.commit()
        return produced
    finally:
        await session.close()


def worker_settings() -> dict[str, Any]:
    from arq.connections import RedisSettings

    settings = get_settings()
    return {
        "functions": [run_attack_run, generate_run_reports],
        "redis_settings": RedisSettings.from_dsn(settings.redis_url),
        "max_jobs": 8,
        "job_timeout": 3600,
        "keep_result": 3600,
    }
