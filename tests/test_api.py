"""API smoke tests — allow-list enforcement at the HTTP boundary."""

from __future__ import annotations

import httpx
import pytest

from app.auth.rbac import ROLE_ADMIN
from app.auth.security import hash_password
from app.core.db import get_session
from app.main import create_app
from app.models import Role, User


@pytest.fixture
async def api_client(db_session):
    from app.api.deps import get_current_user

    app = create_app()

    role = Role(name=ROLE_ADMIN, description="test admin")
    db_session.add(role)
    await db_session.flush()
    user = User(
        username="admin",
        email="admin@test.invalid",
        hashed_password=hash_password("test-password-123"),
        role_id=role.id,
    )
    db_session.add(user)
    await db_session.flush()

    async def _get_session():
        yield db_session

    def _current_user():
        return user

    app.dependency_overrides[get_session] = _get_session
    app.dependency_overrides[get_current_user] = _current_user

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        yield client


async def test_healthz(api_client):
    resp = await api_client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


async def test_register_target_is_closed_and_can_be_allowlisted(api_client):
    resp = await api_client.post(
        "/targets",
        json={
            "name": "acme-chat",
            "connector_type": "rest",
            "endpoint": "http://127.0.0.1:9999/chat",
            "config": {"response_path": "reply"},
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["allowlisted"] is False
    target_id = body["id"]

    resp = await api_client.patch(
        f"/targets/{target_id}/allowlist",
        json={"allowlisted": True, "approved_by": "admin", "approval_note": "own target"},
    )
    assert resp.status_code == 200
    assert resp.json()["allowlisted"] is True
    assert resp.json()["approved_by"] == "admin"


async def test_allowlist_requires_approver(api_client):
    resp = await api_client.post(
        "/targets",
        json={
            "name": "no-approver",
            "connector_type": "rest",
            "endpoint": "http://127.0.0.1:9999/chat",
        },
    )
    target_id = resp.json()["id"]
    resp = await api_client.patch(
        f"/targets/{target_id}/allowlist",
        json={"allowlisted": True, "approved_by": "", "approval_note": ""},
    )
    assert resp.status_code == 422


async def test_run_refuses_non_allowlisted_target(api_client):
    resp = await api_client.post(
        "/targets",
        json={
            "name": "blocked-target",
            "connector_type": "rest",
            "endpoint": "http://127.0.0.1:9999/chat",
        },
    )
    target_id = resp.json()["id"]

    resp = await api_client.post(
        "/runs",
        json={
            "target_id": target_id,
            "payload_pack_ids": ["pack-1"],
            "dry_run": True,
        },
    )
    assert resp.status_code == 409
    assert "allow-listed" in resp.json()["detail"]


async def test_ci_gate_blocks_high_severity_findings(api_client):
    resp = await api_client.post(
        "/ci/gate",
        json={
            "findings": [
                {
                    "severity": "critical",
                    "confidence": 0.95,
                    "category": "secret_leak",
                    "title": "API key leaked",
                },
                {
                    "severity": "low",
                    "confidence": 0.7,
                    "category": "other",
                    "title": "noise",
                },
            ],
            "severity_threshold": "high",
            "min_confidence": 0.6,
            "sarif": False,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["passed"] is False
    assert len(body["blocking_findings"]) == 1
    assert body["blocking_findings"][0]["category"] == "secret_leak"


async def test_ci_gate_passes_when_below_threshold(api_client):
    resp = await api_client.post(
        "/ci/gate",
        json={
            "findings": [
                {
                    "severity": "medium",
                    "confidence": 0.9,
                    "category": "hallucination",
                    "title": "citation issue",
                }
            ],
            "severity_threshold": "critical",
            "min_confidence": 0.5,
            "sarif": False,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["passed"] is True
