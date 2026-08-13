"""Memory/State agent.

Persists turn-by-turn state, records findings for confirmed attacks, and
feeds the continuous-learning loop (vector store + knowledge graph + payload
priority boosts). Nothing about a run is ephemeral: every turn is replayable.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import Agent, JudgeVerdict, TurnRecord
from app.intelligence.feedback_loop import FeedbackLoop
from app.models import Finding, Run, Target
from app.safety.redaction import get_redactor

# Severity-aware remediation by category (augmented by detector guidance).
REMEDIATION_BY_CATEGORY = {
    "prompt_injection": (
        "Apply input classification with separate instruction/data channels; "
        "never concatenate untrusted content into system instructions; validate "
        "output against expected behaviour."
    ),
    "system_prompt_leak": (
        "Treat the system prompt as confidential; add explicit refusal for "
        "prompt-extraction; rotate prompt content if exposed."
    ),
    "pii_leak": (
        "Restrict data access with least-privilege retrieval; add output-side "
        "PII filtering; enforce data classification on context assembly."
    ),
    "secret_leak": (
        "Secrets must never enter model context; rotate any leaked credential; "
        "add output secret-scanning with blocking."
    ),
    "guardrail_bypass": (
        "Track refusal state across turns; re-evaluate the full conversation "
        "before complying; add consistency checks on follow-ups."
    ),
    "tool_abuse": (
        "Apply allow-list policies to tool calls; require confirmation for "
        "destructive actions; validate tool arguments against policy."
    ),
    "hallucination": (
        "Require grounded generation; verify citations against retrieval "
        "context before surfacing answers."
    ),
    "resource_exhaustion": (
        "Cap input/output tokens; enforce timeouts, rate limits and per-run "
        "budgets at the API boundary."
    ),
}


class MemoryAgent(Agent):
    name = "memory"

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._feedback = FeedbackLoop(session)
        self._redactor = get_redactor()

    async def record_turn(self, run: Run, turn: TurnRecord, sequence: int) -> None:
        """Persist a turn to the knowledge store (replayable history)."""
        await self._feedback.store_transcript(
            run_id=run.id,
            target_id=run.target_id,
            text=(
                f"PAYLOAD: {turn.payload.get('slug', '')}\n"
                f"REQUEST: {turn.messages}\nRESPONSE: {turn.response_text}"
            ),
            metadata={
                "run_id": run.id,
                "payload_slug": turn.payload.get("slug", ""),
                "verdict": "success" if turn.verdict and turn.verdict.success else "failed",
                "severity": turn.verdict.severity if turn.verdict else "none",
            },
        )

    async def record_finding(
        self,
        run: Run,
        target: Target,
        turn: TurnRecord,
        verdict: JudgeVerdict,
        detection: dict[str, Any] | None,
        audit_ref: str | None,
    ) -> Finding:
        # The specific detection being recorded shapes the finding.
        primary = detection or (verdict.detections[0] if verdict.detections else {})
        category = primary.get("category", "other")
        evidence = {
            "payload": turn.payload,
            "messages": turn.messages,
            "response": turn.response_text,
            "detections": verdict.detections,
        }
        redacted_evidence = self._redactor.redact(evidence)
        finding = Finding(
            run_id=run.id,
            target_id=target.id,
            payload_id=turn.payload.get("id") or turn.payload.get("db_id"),
            title=primary.get("title", f"{category} detected"),
            category=category,
            owasp_category=primary.get("owasp_category", "LLM01"),
            mitre_atlas_id=primary.get("mitre_atlas_id", "AML.T0051"),
            severity=primary.get("severity", "medium"),
            confidence=primary.get("confidence", verdict.confidence),
            evidence=evidence,
            redacted_evidence=redacted_evidence,
            transcript_refs=[audit_ref] if audit_ref else [],
            remediation_guidance=(
                primary.get("remediation_guidance")
                or REMEDIATION_BY_CATEGORY.get(category, "")
            ),
            detector=primary.get("detector", "ensemble"),
        )
        self._session.add(finding)
        await self._session.flush()
        run.findings_count += 1
        return finding

    async def record_success_feedback(
        self, run: Run, target: Target, finding: Finding, turn: TurnRecord
    ) -> None:
        transcript = (
            f"SUCCESSFUL ATTACK ({finding.category})\n"
            f"payload={turn.payload.get('slug', '')}\n"
            f"messages={turn.messages}\nresponse={turn.response_text[:2000]}"
        )
        await self._feedback.record_success(
            run=run, target=target, finding=finding, transcript=transcript
        )
