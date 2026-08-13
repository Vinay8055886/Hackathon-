"""Findings query routes — evidence is always served redacted."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from app.api.deps import SessionDep, require_roles
from app.auth.rbac import ROLE_OPERATOR, ROLE_VIEWER
from app.models import Finding, User
from app.schemas import FindingOut

router = APIRouter(prefix="/findings", tags=["findings"])

SEVERITIES = ("low", "medium", "high", "critical")
CATEGORIES = (
    "prompt_injection", "system_prompt_leak", "pii_leak", "secret_leak",
    "guardrail_bypass", "tool_abuse", "hallucination", "resource_exhaustion",
    "other",
)


@router.get("", response_model=list[FindingOut])
async def list_findings(
    session: SessionDep,
    user: User = Depends(require_roles(ROLE_VIEWER)),
    severity: str | None = None,
    owasp_category: str | None = None,
    mitre_atlas_id: str | None = None,
    run_id: str | None = None,
    category: str | None = None,
    status: str | None = None,
) -> list[FindingOut]:
    stmt = select(Finding).order_by(Finding.created_at.desc()).limit(500)
    if severity:
        stmt = stmt.where(Finding.severity == severity.lower())
    if owasp_category:
        stmt = stmt.where(Finding.owasp_category == owasp_category.upper())
    if mitre_atlas_id:
        stmt = stmt.where(Finding.mitre_atlas_id == mitre_atlas_id)
    if run_id:
        stmt = stmt.where(Finding.run_id == run_id)
    if category:
        stmt = stmt.where(Finding.category == category)
    if status:
        stmt = stmt.where(Finding.status == status)
    rows = (await session.execute(stmt)).scalars().all()
    return [_out(f) for f in rows]


@router.get("/{finding_id}", response_model=FindingOut)
async def get_finding(
    finding_id: str, session: SessionDep, user: User = Depends(require_roles(ROLE_VIEWER))
) -> FindingOut:
    finding = await session.get(Finding, finding_id)
    if finding is None:
        raise HTTPException(status_code=404, detail=f"finding {finding_id} not found")
    return _out(finding)


@router.patch("/{finding_id}/status", response_model=FindingOut)
async def update_finding_status(
    finding_id: str,
    status: str,
    session: SessionDep,
    user: User = Depends(require_roles(ROLE_OPERATOR)),
) -> FindingOut:
    finding = await session.get(Finding, finding_id)
    if finding is None:
        raise HTTPException(status_code=404, detail=f"finding {finding_id} not found")
    if status not in {"open", "confirmed", "triaged", "accepted", "fixed"}:
        raise HTTPException(status_code=422, detail=f"unknown status {status!r}")
    finding.status = status
    await session.commit()
    await session.refresh(finding)
    return _out(finding)


def _out(f: Finding) -> FindingOut:
    return FindingOut(
        id=f.id, run_id=f.run_id, target_id=f.target_id, title=f.title,
        category=f.category, owasp_category=f.owasp_category,
        mitre_atlas_id=f.mitre_atlas_id, severity=f.severity,
        confidence=f.confidence, redacted_evidence=f.redacted_evidence or {},
        remediation_guidance=f.remediation_guidance, status=f.status,
        detector=f.detector, created_at=f.created_at,
    )
