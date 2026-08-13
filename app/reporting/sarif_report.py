"""SARIF 2.1.0 output for CI tooling (GitHub code scanning, etc.)."""

from __future__ import annotations

import json
from typing import Any

from app.models import Finding, Run, Target

SARIF_SCHEMA = (
    "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/"
    "Schemata/sarif-schema-2.1.0.json"
)

SARIF_LEVEL = {"critical": "error", "high": "error", "medium": "warning", "low": "note"}


def build_sarif(run: Run, target: Target, findings: list[Finding]) -> dict[str, Any]:
    rules: list[dict[str, Any]] = []
    results: list[dict[str, Any]] = []
    seen_rules: set[str] = set()

    for finding in findings:
        rule_id = f"{finding.category.upper()}-{finding.owasp_category}-{finding.mitre_atlas_id}"
        if rule_id not in seen_rules:
            seen_rules.add(rule_id)
            rules.append(
                {
                    "id": rule_id,
                    "name": finding.title,
                    "shortDescription": {"text": finding.title},
                    "fullDescription": {
                        "text": (
                            f"{finding.title}. OWASP LLM Top 10: {finding.owasp_category}. "
                            f"MITRE ATLAS: {finding.mitre_atlas_id}. "
                            f"Remediation: {finding.remediation_guidance}"
                        )
                    },
                    "defaultConfiguration": {
                        "level": SARIF_LEVEL.get(finding.severity, "warning")
                    },
                    "properties": {
                        "severity": finding.severity,
                        "owasp_category": finding.owasp_category,
                        "mitre_atlas_id": finding.mitre_atlas_id,
                        "confidence": finding.confidence,
                        "category": finding.category,
                    },
                }
            )
        results.append(
            {
                "ruleId": rule_id,
                "level": SARIF_LEVEL.get(finding.severity, "warning"),
                "message": {"text": finding.title},
                "locations": [
                    {
                        "logicalLocations": [
                            {
                                "fullyQualifiedName": (
                                    f"{target.name}:{finding.category}"
                                ),
                                "kind": "target",
                            }
                        ]
                    }
                ],
                "properties": {
                    "severity": finding.severity,
                    "confidence": finding.confidence,
                    "category": finding.category,
                    "owasp_category": finding.owasp_category,
                    "mitre_atlas_id": finding.mitre_atlas_id,
                    "remediation": finding.remediation_guidance,
                    "evidence": finding.redacted_evidence,
                },
            }
        )

    return {
        "$schema": SARIF_SCHEMA,
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "Aegis-LLM",
                        "version": "0.1.0",
                        "informationUri": "https://example.invalid/aegis-llm",
                        "rules": rules,
                    }
                },
                "results": results,
                "properties": {
                    "run_id": run.id,
                    "run_status": run.status,
                    "dry_run": run.dry_run,
                    "target_id": target.id,
                    "target_name": target.name,
                    "tokens_used": run.tokens_used,
                    "cost_estimate_usd": run.cost_estimate_usd,
                },
            }
        ],
    }


def sarif_to_json(sarif: dict[str, Any]) -> str:
    return json.dumps(sarif, indent=2)
