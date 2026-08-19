"""Target registration + allow-listing routes.

The allow-list is the heart of the safety posture: a target is untouchable
until an operator explicitly allow-lists it with an approval record.
"""

from __future__ import annotations

import time
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
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


# ── Connection test ──────────────────────────────────────────────────────────
class ConnectionTestRequest(BaseModel):
    """Quick connection test against an external LLM endpoint."""
    endpoint: str = Field(min_length=1)
    connector_type: str = Field(default="rest")
    config: dict[str, Any] = Field(default_factory=dict)
    timeout: float = Field(default=15.0, ge=1, le=60)


class ConnectionTestResult(BaseModel):
    connected: bool
    status_code: int | None = None
    latency_ms: int = 0
    response_preview: str = ""
    target_type_detected: str = "unknown"
    error: str | None = None
    tls_verified: bool = True
    auth_configured: bool = False


@router.post("/test-connection")
async def test_connection(
    body: ConnectionTestRequest,
    session: SessionDep,
    user: User = Depends(require_roles(ROLE_OPERATOR)),
) -> ConnectionTestResult:
    """Test connectivity to an external LLM endpoint.

    Sends a minimal, safe probe (no adversarial content) to verify:
    - the endpoint is reachable
    - authentication works
    - the response can be parsed
    """
    cfg = body.config or {}
    headers = cfg.get("headers") or {}
    method = str(cfg.get("method", "POST")).upper()
    model_name = cfg.get("model", "test-model")

    # Determine if authentication is configured
    auth_configured = bool(headers.get("Authorization") or headers.get("X-API-Key"))

    # Build a harmless probe payload
    probe_messages = [{"role": "user", "content": "Hello, this is a connectivity test. Please respond with: OK"}]

    template = cfg.get("body_template")
    if template is not None:
        import json
        body_json: Any = json.loads(json.dumps(template).replace("{messages}", json.dumps(probe_messages)))
    else:
        body_json = {
            "model": model_name,
            "messages": probe_messages,
            "max_tokens": 50,
        }

    started = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=body.timeout, verify=True) as client:
            resp = await client.request(method, body.endpoint, json=body_json, headers=headers)
        latency_ms = int((time.monotonic() - started) * 1000)

        # Extract response preview
        response_preview = ""
        response_path = cfg.get("response_path")
        if response_path and resp.headers.get("content-type", "").startswith("application/json"):
            try:
                data = resp.json()
                for part in str(response_path).split("."):
                    data = data[int(part)] if part.isdigit() else data[part]
                if isinstance(data, str):
                    response_preview = data[:200]
                else:
                    response_preview = str(data)[:200]
            except Exception:
                response_preview = resp.text[:200]
        else:
            response_preview = resp.text[:200]

        # Detect target type based on response
        target_type = _detect_target_type(resp)

        return ConnectionTestResult(
            connected=200 <= resp.status_code < 500,
            status_code=resp.status_code,
            latency_ms=latency_ms,
            response_preview=response_preview,
            target_type_detected=target_type,
            tls_verified=True,
            auth_configured=auth_configured,
        )
    except httpx.ConnectError as exc:
        latency_ms = int((time.monotonic() - started) * 1000)
        return ConnectionTestResult(
            connected=False,
            latency_ms=latency_ms,
            error=f"Connection failed: {exc}",
            target_type_detected="unreachable",
            auth_configured=auth_configured,
        )
    except httpx.TimeoutException as exc:
        latency_ms = int((time.monotonic() - started) * 1000)
        return ConnectionTestResult(
            connected=False,
            latency_ms=latency_ms,
            error=f"Timeout after {body.timeout}s: {exc}",
            target_type_detected="timeout",
            auth_configured=auth_configured,
        )
    except Exception as exc:
        latency_ms = int((time.monotonic() - started) * 1000)
        return ConnectionTestResult(
            connected=False,
            latency_ms=latency_ms,
            error=f"Error: {exc}",
            target_type_detected="error",
            auth_configured=auth_configured,
        )


def _detect_target_type(resp: httpx.Response) -> str:
    """Detect target type from response headers and body structure."""
    try:
        if resp.headers.get("content-type", "").startswith("application/json"):
            data = resp.json()
            # OpenAI-compatible response detection
            if "choices" in data and isinstance(data["choices"], list):
                first = data["choices"][0] if data["choices"] else {}
                if "message" in first or "text" in first:
                    return "openai-compatible"
            # Generic chat response
            if "reply" in data or "response" in data or "message" in data:
                return "rest-api"
            # Health check response
            if "status" in data and data.get("status") in ("ok", "healthy"):
                return "rest-api"
    except Exception:
        pass
    return "unknown"
