"""Target allow-list.

No connector may interact with a target unless it is BOTH registered AND
allow-listed AND approved. This is enforced inside the interaction guard so
that no code path — API, CLI, worker, agent — can bypass it.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Target


class AllowlistError(Exception):
    """Raised when a target is not allowed to be interacted with."""

    def __init__(self, message: str, code: str = "target_not_allowed") -> None:
        super().__init__(message)
        self.code = code


async def fetch_target(session: AsyncSession, target_id: str) -> Target | None:
    return await session.get(Target, target_id)


async def assert_target_allowlisted(session: AsyncSession, target_id: str) -> Target:
    """Return the target or raise AllowlistError with a precise reason."""
    target = await fetch_target(session, target_id)
    if target is None:
        raise AllowlistError(
            f"Target {target_id!r} is not registered. Register it before any interaction.",
            code="target_not_registered",
        )
    if not target.allowlisted:
        raise AllowlistError(
            f"Target {target.name!r} is not allow-listed. "
            "An approved operator must PATCH /targets/{id}/allowlist first.",
            code="target_not_allowlisted",
        )
    if not target.approved_by:
        raise AllowlistError(
            f"Target {target.name!r} is allow-listed but has no approval record. "
            "Set approved_by/approval_note via the allowlist endpoint.",
            code="target_not_approved",
        )
    return target
