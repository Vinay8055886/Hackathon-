"""Report generation routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from app.api.deps import SessionDep, require_roles
from app.auth.rbac import ROLE_VIEWER
from app.models import Report, User
from app.reporting.report_service import ReportNotFoundError, generate_report
from app.schemas import ReportOut

router = APIRouter(prefix="/runs", tags=["reports"])


@router.get("/{run_id}/report", response_model=ReportOut)
async def get_report(
    run_id: str,
    session: SessionDep,
    user: User = Depends(require_roles(ROLE_VIEWER)),
    format: str = Query(default="html", pattern="^(html|sarif|json)$"),
) -> ReportOut:
    """Generate (or reuse) a report artifact for a run."""
    report = await generate_report(session, run_id, format, generated_by=user.username)
    await session.commit()
    return ReportOut(
        id=report.id, run_id=report.run_id, format=report.format,
        storage_path=report.storage_path, size_bytes=report.size_bytes,
        generated_by=report.generated_by, created_at=report.created_at,
    )


@router.get("/{run_id}/report/download")
async def download_report(
    run_id: str,
    session: SessionDep,
    user: User = Depends(require_roles(ROLE_VIEWER)),
    format: str = Query(default="html", pattern="^(html|sarif|json)$"),
):
    report = await generate_report(session, run_id, format, generated_by=user.username)
    await session.commit()
    media_type = {
        "html": "text/html",
        "sarif": "application/json",
        "json": "application/json",
    }[format]
    return FileResponse(
        report.storage_path,
        media_type=media_type,
        filename=f"aegis-run-{run_id}.{format}",
    )


@router.get("/{run_id}/reports", response_model=list[ReportOut])
async def list_reports(
    run_id: str, session: SessionDep, user: User = Depends(require_roles(ROLE_VIEWER))
) -> list[ReportOut]:
    from sqlalchemy import select

    from app.models import Report

    stmt = select(Report).where(Report.run_id == run_id).order_by(Report.created_at.desc())
    rows = (await session.execute(stmt)).scalars().all()
    return [
        ReportOut(
            id=r.id, run_id=r.run_id, format=r.format, storage_path=r.storage_path,
            size_bytes=r.size_bytes, generated_by=r.generated_by, created_at=r.created_at,
        )
        for r in rows
    ]
