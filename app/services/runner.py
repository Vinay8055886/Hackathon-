"""Run execution dispatch.

``AEGIS_RUNNER=arq`` enqueues the run on the Redis-backed ARQ queue (see
app/workers). ``AEGIS_RUNNER=inproc`` (default; demo/tests) executes the run
as an asyncio background task in the API process — one command, no worker.
"""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings

logger = logging.getLogger("aegis.runner")


async def execute_run(run_id: str) -> None:
    """Run an attack run to completion in its own DB session."""
    from app.agents.orchestrator import AttackOrchestrator, materialize_payloads
    from app.core.db import get_session_factory
    from app.models import Run, Target

    session: AsyncSession = get_session_factory()()
    try:
        run = await session.get(Run, run_id)
        if run is None:
            logger.error("run %s not found", run_id)
            return
        target = await session.get(Target, run.target_id)
        if target is None:
            run.status = "failed"
            run.error = "target not found"
            await session.commit()
            return
        payloads = await materialize_payloads(session, run.payload_pack_ids)
        if not payloads:
            run.status = "failed"
            run.error = "no payloads materialized from the selected packs"
            await session.commit()
            return
        orchestrator = AttackOrchestrator(session, run, target, payloads)
        await orchestrator.execute()
        await session.commit()
    except Exception:
        logger.exception("run %s crashed", run_id)
        await session.rollback()
    finally:
        await session.close()


async def launch_run(session: AsyncSession, run_id: str) -> str:
    """Dispatch a run: enqueue on ARQ or execute in-process. Returns dispatcher."""
    settings = get_settings()
    if settings.runner == "arq":
        try:
            from arq import create_pool
            from arq.connections import RedisSettings

            pool = await create_pool(
                RedisSettings.from_dsn(settings.redis_url), retry=1, retry_jobs=False
            )
            await pool.enqueue_job("run_attack_run", run_id)
            await pool.aclose()
            return "arq"
        except Exception as exc:  # pragma: no cover - depends on Redis
            logger.warning("ARQ unavailable (%s); falling back to in-process", exc)
    asyncio.create_task(execute_run(run_id))
    return "inproc"
