"""Report service — generates and persists HTML/SARIF/JSON artifacts."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import Finding, Report, Run, Target
from app.reporting.html_report import build_html_report
from app.reporting.json_report import build_json_report, json_report_to_string
from app.reporting.sarif_report import build_sarif, sarif_to_json


class ReportNotFoundError(Exception):
    pass


async def generate_report(
    session: AsyncSession,
    run_id: str,
    fmt: str,
    *,
    generated_by: str = "system",
) -> Report:
    if fmt not in {"html", "sarif", "json"}:
        raise ValueError(f"Unsupported report format: {fmt}")

    run = await session.get(Run, run_id)
    if run is None:
        raise ReportNotFoundError(f"Run {run_id} not found")
    target = await session.get(Target, run.target_id)
    if target is None:
        raise ReportNotFoundError(f"Target {run.target_id} not found")

    stmt = select(Finding).where(Finding.run_id == run_id).order_by(Finding.severity)
    findings = list((await session.execute(stmt)).scalars().all())

    if fmt == "html":
        content = build_html_report(run, target, findings)
    elif fmt == "sarif":
        content = sarif_to_json(build_sarif(run, target, findings))
    else:
        content = json_report_to_string(build_json_report(run, target, findings))

    report_dir = get_settings().report_dir
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / f"run-{run_id}.{fmt}"
    path.write_text(content, encoding="utf-8")

    report = Report(
        run_id=run_id,
        format=fmt,
        storage_path=str(path),
        size_bytes=path.stat().st_size,
        generated_by=generated_by,
        meta={"findings": len(findings), "target": target.name},
    )
    session.add(report)
    await session.flush()
    return report
