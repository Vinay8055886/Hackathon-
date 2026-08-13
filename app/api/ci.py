"""CI policy-gate: policy-as-code build gate with SARIF output.

Fail a PR when findings meet/exceed a configured severity threshold at a
minimum confidence. Returns pass/fail plus the SARIF payload for native code
scanning integration.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from app.api.deps import SessionDep, require_roles
from app.auth.rbac import ROLE_VIEWER
from app.models import Finding, Run, Target, User
from app.reporting.sarif_report import build_sarif
from app.schemas import CiGateRequest, CiGateResponse
from app.schemas.report import SEVERITY_RANK

router = APIRouter(prefix="/ci", tags=["ci"])


@router.post("/gate", response_model=CiGateResponse)
async def ci_gate(
    body: CiGateRequest,
    session: SessionDep,
    user: User = Depends(require_roles(ROLE_VIEWER)),
) -> CiGateResponse:
    threshold = SEVERITY_RANK[body.severity_threshold]

    findings: list[dict] = []
    if body.findings is not None:
        findings = body.findings
    elif body.run_id:
        run = await session.get(Run, body.run_id)
        if run is None:
            raise HTTPException(status_code=404, detail=f"run {body.run_id} not found")
        target = await session.get(Target, run.target_id)
        stmt = select(Finding).where(Finding.run_id == run.id)
        rows = (await session.execute(stmt)).scalars().all()
        findings = [
            {
                "severity": f.severity,
                "confidence": f.confidence,
                "category": f.category,
                "owasp_category": f.owasp_category,
                "mitre_atlas_id": f.mitre_atlas_id,
                "title": f.title,
                "redacted_evidence": f.redacted_evidence,
            }
            for f in rows
        ]
        if target is not None:
            sarif = build_sarif(run, target, rows)
    else:
        raise HTTPException(status_code=422, detail="provide run_id or findings")

    blocking = [
        f
        for f in findings
        if SEVERITY_RANK.get(str(f.get("severity", "low")).lower(), 0) >= threshold
        and float(f.get("confidence", 0)) >= body.min_confidence
        and (not body.block_categories or f.get("category") in body.block_categories)
    ]
    passed = not blocking
    return CiGateResponse(
        passed=passed,
        blocking_findings=blocking,
        total_findings=len(findings),
        threshold=body.severity_threshold,
        message=(
            f"CI gate {'PASSED' if passed else 'BLOCKED'}: {len(blocking)} finding(s) "
            f"at or above {body.severity_threshold} severity (min confidence "
            f"{body.min_confidence})."
        ),
        sarif=sarif if body.sarif and body.run_id else None,
    )
