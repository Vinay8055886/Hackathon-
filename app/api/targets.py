"""Target registration + allow-listing routes.

The allow-list is the heart of the safety posture: a target is untouchable
until an operator explicitly allow-lists it with an approval record.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from app.api.deps import SessionDep, not_found, require_roles
from app.auth.rbac import ROLE_OPERATOR, ROLE_VIEWER
from app.models import Target, User
from app.schemas import AllowlistRequest, TargetCreate, TargetOut

router = APIRouter(prefix="/targets", tags=["targets"])


@router.post("", response_model=TargetOut, status_code=201)
async def create_target(
    body: TargetCreate,
    session: SessionDep,
    user: User = Depends(require_roles(ROLE_OPERATOR)),
) -> TargetOut:
    target = Target(
        name=body.name,
        description=body.description,
        connector_type=body.connector_type,
        endpoint=body.endpoint,
        config=body.config,
        auth_ref=body.auth_ref,
        rate_limit_per_minute=body.rate_limit_per_minute,
        max_tokens_per_run=body.max_tokens_per_run,
        owner_id=user.id,
        allowlisted=False,  # always registered closed
    )
    session.add(target)
    await session.commit()
    await session.refresh(target)
    return TargetOut.model_validate(target)


@router.get("", response_model=list[TargetOut])
async def list_targets(
    session: SessionDep,
    user: User = Depends(require_roles(ROLE_VIEWER)),
    allowlisted: bool | None = None,
) -> list[TargetOut]:
    stmt = select(Target).order_by(Target.created_at.desc())
    if allowlisted is not None:
        stmt = stmt.where(Target.allowlisted == allowlisted)
    rows = (await session.execute(stmt)).scalars().all()
    return [TargetOut.model_validate(t) for t in rows]


@router.get("/{target_id}", response_model=TargetOut)
async def get_target(
    target_id: str, session: SessionDep, user: User = Depends(require_roles(ROLE_VIEWER))
) -> TargetOut:
    target = await session.get(Target, target_id)
    if target is None:
        raise not_found(f"target {target_id} not found")
    return TargetOut.model_validate(target)


@router.patch("/{target_id}/allowlist", response_model=TargetOut)
async def set_allowlist(
    target_id: str,
    body: AllowlistRequest,
    session: SessionDep,
    user: User = Depends(require_roles(ROLE_OPERATOR)),
) -> TargetOut:
    """Allow-list (or de-list) a target. Requires an approver identity + note."""
    target = await session.get(Target, target_id)
    if target is None:
        raise not_found(f"target {target_id} not found")
    if body.allowlisted and not body.approved_by:
        raise HTTPException(status_code=422, detail="approved_by is required to allow-list")
    target.allowlisted = body.allowlisted
    target.approved_by = body.approved_by if body.allowlisted else None
    target.approval_note = body.approval_note
    await session.commit()
    await session.refresh(target)
    return TargetOut.model_validate(target)
