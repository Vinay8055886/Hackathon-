"""SARIF 2.1.0 output shape tests."""

from __future__ import annotations

import json

from app.models import Finding, Run, Target
from app.reporting.sarif_report import build_sarif, sarif_to_json


def _fixture() -> tuple[Run, Target, list[Finding]]:
    run = Run(
        id="run-1",
        target_id="t-1",
        status="completed",
        dry_run=False,
        started_by="u1",
        max_turns=10,
        token_budget=1000,
        tokens_used=42,
        cost_estimate_usd=0.001,
    )
    target = Target(
        id="t-1",
        name="acme-chat",
        connector_type="rest",
        endpoint="http://acme/chat",
        allowlisted=True,
        owner_id="u1",
    )
    findings = [
        Finding(
            id="f-1",
            run_id="run-1",
            target_id="t-1",
            title="System prompt leakage suspected",
            category="system_prompt_leak",
            owasp_category="LLM07",
            mitre_atlas_id="AML.T0040",
            severity="high",
            confidence=0.9,
            redacted_evidence={"response_snippet": "[REDACTED]"},
            remediation_guidance="Treat the system prompt as confidential.",
            status="open",
            detector="prompt_leak",
        ),
        Finding(
            id="f-2",
            run_id="run-1",
            target_id="t-1",
            title="Unbounded output",
            category="resource_exhaustion",
            owasp_category="LLM10",
            mitre_atlas_id="AML.T0034",
            severity="medium",
            confidence=0.7,
            redacted_evidence={"response_snippet": "[REDACTED]"},
            remediation_guidance="Cap output tokens.",
            status="open",
            detector="resource_exhaustion",
        ),
    ]
    return run, target, findings


def test_sarif_structure():
    run, target, findings = _fixture()
    sarif = build_sarif(run, target, findings)
    assert sarif["version"] == "2.1.0"
    assert sarif["$schema"].endswith("sarif-schema-2.1.0.json")
    runs = sarif["runs"]
    assert len(runs) == 1
    run_block = runs[0]
    assert run_block["tool"]["driver"]["name"] == "Aegis-LLM"
    assert run_block["properties"]["run_id"] == "run-1"
    assert run_block["properties"]["target_name"] == "acme-chat"


def test_sarif_severity_maps_to_levels():
    run, target, findings = _fixture()
    sarif = build_sarif(run, target, findings)
    by_level = {}
    for result in sarif["runs"][0]["results"]:
        by_level[result["properties"]["category"]] = result["level"]
    assert by_level["system_prompt_leak"] == "error"  # high → error
    assert by_level["resource_exhaustion"] == "warning"  # medium → warning


def test_sarif_rules_and_results_shape():
    run, target, findings = _fixture()
    sarif = build_sarif(run, target, findings)
    rules = sarif["runs"][0]["tool"]["driver"]["rules"]
    results = sarif["runs"][0]["results"]
    assert len(rules) == 2
    assert len(results) == 2
    for rule in rules:
        assert rule["id"]
        assert rule["properties"]["severity"] in {"low", "medium", "high", "critical"}
        assert rule["properties"]["confidence"] > 0
    for result in results:
        assert result["ruleId"]
        assert result["message"]["text"]
        assert result["locations"][0]["logicalLocations"][0]["fullyQualifiedName"]
        assert "remediation" in result["properties"]
        # evidence must be the redacted copy
        assert "response_snippet" in result["properties"]["evidence"]


def test_sarif_serializes_to_json():
    run, target, findings = _fixture()
    text = sarif_to_json(build_sarif(run, target, findings))
    parsed = json.loads(text)
    assert parsed["version"] == "2.1.0"
