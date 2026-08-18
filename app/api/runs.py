"""Attack run routes + live SSE stream."""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from app.api.deps import SessionDep, require_roles
from app.auth.rbac import ROLE_OPERATOR, ROLE_VIEWER
from app.core.config import get_settings
from app.core.events import subscribe_run
from app.models import AgentEvent, Run, Target, User
from app.schemas import RunCreate, RunEventOut, RunOut
from app.services.runner import launch_run

router = APIRouter(prefix="/runs", tags=["runs"])


@router.post("", response_model=RunOut, status_code=201)
async def create_run(
    body: RunCreate,
    session: SessionDep,
    user: User = Depends(require_roles(ROLE_OPERATOR)),
) -> RunOut:
    """Create and dispatch an attack run.

    Safety checks (in order): permission (role), target allow-list, budgets.
    A run against a non-allow-listed target is refused here AND at the
    interaction boundary.
    """
    target = await session.get(Target, body.target_id)
    if target is None:
        raise HTTPException(status_code=404, detail=f"target {body.target_id} not found")
    if not target.allowlisted:
        raise HTTPException(
            status_code=409,
            detail=(
                f"target {target.name!r} is not allow-listed — PATCH "
                f"/targets/{target.id}/allowlist first. Runs refuse non-allow-listed targets."
            ),
        )

    settings = get_settings()
    dry_run = body.dry_run if body.dry_run is not None else settings.dry_run_default
    run = Run(
        target_id=target.id,
        payload_pack_ids=body.payload_pack_ids,
        status="scheduled",
        dry_run=dry_run,
        run_origin=body.run_origin or "real",
        started_by=user.id,
        max_turns=body.max_turns or settings.default_max_turns,
        token_budget=body.token_budget or target.max_tokens_per_run
        or settings.default_max_tokens_per_run,
    )
    session.add(run)
    await session.commit()
    await session.refresh(run)

    dispatcher = await launch_run(session, run.id)
    await session.commit()
    return RunOut.model_validate(run)


@router.get("", response_model=list[RunOut])
async def list_runs(
    session: SessionDep,
    user: User = Depends(require_roles(ROLE_VIEWER)),
    status_filter: str | None = Query(default=None, alias="status", max_length=32),
    target_id: str | None = Query(default=None, max_length=36),
    run_origin: str | None = Query(default=None, max_length=16),
) -> list[RunOut]:
    RUN_STATUSES = ("scheduled", "running", "completed", "failed", "cancelled")
    RUN_ORIGINS = ("real", "demo", "test")
    stmt = select(Run).order_by(Run.created_at.desc()).limit(200)
    if status_filter:
        if status_filter not in RUN_STATUSES:
            raise HTTPException(status_code=422, detail=f"status must be one of {RUN_STATUSES}")
        stmt = stmt.where(Run.status == status_filter)
    if target_id:
        stmt = stmt.where(Run.target_id == target_id)
    if run_origin:
        if run_origin not in RUN_ORIGINS:
            raise HTTPException(status_code=422, detail=f"run_origin must be one of {RUN_ORIGINS}")
        stmt = stmt.where(Run.run_origin == run_origin)
    rows = (await session.execute(stmt)).scalars().all()
    return [RunOut.model_validate(r) for r in rows]


@router.get("/{run_id}", response_model=RunOut)
async def get_run(
    run_id: str, session: SessionDep, user: User = Depends(require_roles(ROLE_VIEWER))
) -> RunOut:
    run = await session.get(Run, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"run {run_id} not found")
    return RunOut.model_validate(run)


@router.patch("/{run_id}/cancel", response_model=RunOut)
async def cancel_run(
    run_id: str,
    session: SessionDep,
    user: User = Depends(require_roles(ROLE_OPERATOR)),
) -> RunOut:
    """Stop a scheduled/running run. The run is marked cancelled; already
    recorded interactions and findings remain in the audit trail."""
    run = await session.get(Run, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"run {run_id} not found")
    if run.status in {"scheduled", "running"}:
        from datetime import datetime, timezone

        run.status = "cancelled"
        run.finished_at = datetime.now(timezone.utc)
        await session.commit()
        await session.refresh(run)
    return RunOut.model_validate(run)


@router.get("/{run_id}/events", response_model=list[RunEventOut])
async def get_run_events(
    run_id: str, session: SessionDep, user: User = Depends(require_roles(ROLE_VIEWER))
) -> list[RunEventOut]:
    stmt = (
        select(AgentEvent)
        .where(AgentEvent.run_id == run_id)
        .order_by(AgentEvent.sequence)
    )
    rows = (await session.execute(stmt)).scalars().all()
    return [
        RunEventOut(
            sequence=e.sequence, run_id=e.run_id, agent=e.agent,
            event_type=e.event_type, payload=e.payload,
        )
        for e in rows
    ]


@router.get("/{run_id}/stream")
async def stream_run(
    run_id: str,
    request: Request,
    session: SessionDep,
    user: User = Depends(require_roles(ROLE_VIEWER)),
):
    """Server-Sent Events stream: live agent status, turns, findings.

    Historical events are replayed first, then live events are streamed until
    the run finishes.
    """
    run = await session.get(Run, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"run {run_id} not found")

    async def event_gen():
        # Replay history so late joiners see the full story.
        stmt = (
            select(AgentEvent).where(AgentEvent.run_id == run_id).order_by(AgentEvent.sequence)
        )
        history = (await session.execute(stmt)).scalars().all()
        for e in history:
            yield _sse(_event_payload(e))
        if run.status in {"completed", "failed", "cancelled"}:
            yield _sse(json.dumps({"event": "stream_end", "run_id": run_id}))
            return
        stream = await subscribe_run(run_id)
        try:
            async for message in stream:
                if await request.is_disconnected():
                    break
                yield _sse(message)
                if '"run_finished"' in message or '"stream_end"' in message:
                    break
        finally:
            await stream.aclose()
        yield _sse(json.dumps({"event": "stream_end", "run_id": run_id}))

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


def _event_payload(e: AgentEvent) -> str:
    return json.dumps(
        {
            "sequence": e.sequence,
            "run_id": e.run_id,
            "agent": e.agent,
            "event_type": e.event_type,
            "payload": e.payload,
        }
    )


def _sse(data: str) -> str:
    return f"data: {data}\n\n"
