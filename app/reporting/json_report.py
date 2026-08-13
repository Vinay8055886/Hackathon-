"""Structured JSON report."""

from __future__ import annotations

import json
from typing import Any

from app.models import Finding, Run, Target


def build_json_report(run: Run, target: Target, findings: list[Finding]) -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "tool": "Aegis-LLM",
        "run": {
            "id": run.id,
            "status": run.status,
            "dry_run": run.dry_run,
            "started_by": run.started_by,
            "max_turns": run.max_turns,
            "tokens_used": run.tokens_used,
            "cost_estimate_usd": run.cost_estimate_usd,
            "created_at": run.created_at.isoformat() if run.created_at else None,
            "finished_at": run.finished_at.isoformat() if run.finished_at else None,
        },
        "target": {
            "id": target.id,
            "name": target.name,
            "connector_type": target.connector_type,
            "endpoint": target.endpoint,
        },
        "summary": {
            "total_findings": len(findings),
            "by_severity": _count_by(findings, lambda f: f.severity),
            "by_category": _count_by(findings, lambda f: f.category),
            "by_owasp": _count_by(findings, lambda f: f.owasp_category),
        },
        "findings": [
            {
                "id": f.id,
                "title": f.title,
                "category": f.category,
                "owasp_category": f.owasp_category,
                "mitre_atlas_id": f.mitre_atlas_id,
                "severity": f.severity,
                "confidence": f.confidence,
                "status": f.status,
                "detector": f.detector,
                "evidence": f.redacted_evidence,
                "remediation_guidance": f.remediation_guidance,
            }
            for f in findings
        ],
    }


def _count_by(findings: list[Finding], key) -> dict[str, int]:
    out: dict[str, int] = {}
    for f in findings:
        out[key(f)] = out.get(key(f), 0) + 1
    return out


def json_report_to_string(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2)
