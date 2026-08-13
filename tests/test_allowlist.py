"""Allow-list enforcement tests — the core safety invariant."""

from __future__ import annotations

import pytest

from app.models import Target
from app.safety import InteractionGuard, SafetyError


async def _make_target(db_session, *, allowlisted: bool, approved_by: str | None = "admin") -> Target:
    target = Target(
        name="acme-chat",
        connector_type="rest",
        endpoint="http://127.0.0.1:9999/chat",
        allowlisted=allowlisted,
        approved_by=approved_by,
        approval_note="test approval" if allowlisted else "",
        owner_id="u1",
    )
    db_session.add(target)
    await db_session.flush()
    return target


async def test_guard_refuses_unregistered_target(db_session):
    guard = InteractionGuard(db_session)
    with pytest.raises(SafetyError) as exc:
        await guard.authorize(target_id="missing", run_id=None, actor="u1")
    assert exc.value.code == "target_not_registered"


async def test_guard_refuses_non_allowlisted_target(db_session):
    target = await _make_target(db_session, allowlisted=False)
    guard = InteractionGuard(db_session)
    with pytest.raises(SafetyError) as exc:
        await guard.authorize(target_id=target.id, run_id=None, actor="u1")
    assert exc.value.code == "target_not_allowlisted"


async def test_guard_refuses_unapproved_target(db_session):
    target = await _make_target(db_session, allowlisted=True, approved_by=None)
    guard = InteractionGuard(db_session)
    with pytest.raises(SafetyError) as exc:
        await guard.authorize(target_id=target.id, run_id=None, actor="u1")
    assert exc.value.code == "target_not_approved"


async def test_guard_allows_allowlisted_approved_target(db_session):
    target = await _make_target(db_session, allowlisted=True)
    guard = InteractionGuard(db_session)
    resolved = await guard.authorize(target_id=target.id, run_id=None, actor="u1")
    assert resolved.id == target.id


async def test_preflight_respects_token_budget(db_session):
    from app.core.config import get_settings

    target = Target(
        name="budgeted",
        connector_type="rest",
        endpoint="http://127.0.0.1:9999/chat",
        allowlisted=True,
        approved_by="admin",
        max_tokens_per_run=10,  # tiny budget
        owner_id="u1",
    )
    db_session.add(target)
    await db_session.flush()
    guard = InteractionGuard(db_session)
    await guard.authorize(target_id=target.id, run_id=None, actor="u1")
    with pytest.raises(SafetyError) as exc:
        await guard.preflight(target_id=target.id, payload_text="x" * 1000)
    assert exc.value.code == "token_budget_exceeded"
