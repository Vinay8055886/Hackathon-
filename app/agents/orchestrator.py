"""The orchestration loop.

    Attacker → interaction layer → target response → Judge
            → (success?) → Memory records finding + feedback → done
            → (else)     → Refiner mutates → repeat (≤ max_turns, ≤ token budget)

Every step emits an event (persisted to agent_events + streamed via SSE), so
runs are fully auditable and replayable.
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.attacker import AttackerAgent
from app.agents.base import JudgeVerdict, TurnRecord
from app.agents.judge import JudgeAgent
from app.agents.memory import MemoryAgent
from app.agents.refiner import RefinerAgent
from app.core.config import get_settings
from app.core.events import EventPublisher
from app.detection import DetectionContext
from app.interaction import build_connector
from app.interaction.base import ConnectorError, TargetConnector
from app.interaction.connectors.dryrun import DryRunConnector
from app.models import Run, Target
from app.safety import InteractionGuard, SafetyError
from app.safety.redaction import get_redactor

COST_PER_1K_TOKENS = 0.002  # USD, gpt-4o-mini-ish; configurable later


class OrchestrationError(Exception):
    pass


class AttackOrchestrator:
    def __init__(
        self,
        session: AsyncSession,
        run: Run,
        target: Target,
        payloads: list[dict[str, Any]],
        *,
        connector: TargetConnector | None = None,
        max_turns: int | None = None,
    ) -> None:
        self._session = session
        self.run = run
        self.target = target
        self.payloads = payloads
        self.max_turns = max_turns or run.max_turns or get_settings().default_max_turns
        self._events = EventPublisher(session)
        self._guard = InteractionGuard(session)
        self._connector = connector
        self._redactor = get_redactor()

        self._attacker = AttackerAgent()
        self._judge = JudgeAgent()
        self._refiner = RefinerAgent()
        self._memory = MemoryAgent(session)

    # ── public API ──────────────────────────────────────────────────────────
    async def execute(self) -> Run:
        self.run.status = "running"
        self.run.started_at = datetime.now(timezone.utc)
        await self._session.flush()
        await self._emit("orchestrator", "run_started", {"max_turns": self.max_turns})

        attempted: set[str] = set()
        refined: set[str] = set()
        resolved: set[str] = set()
        used_strategies: set[str] = set()
        recorded_categories: set[str] = set()
        total_tokens = 0
        start = time.monotonic()

        try:
            turn = 0
            while turn < self.max_turns:
                # ── Attacker ─────────────────────────────────────────────────
                payload = await self._attacker.select_next(
                    self.payloads, attempted, refined, resolved
                )
                if payload is None:
                    await self._emit("attacker", "no_payloads_left", {})
                    break

                turn += 1
                await self._emit(
                    "attacker",
                    "payload_selected",
                    {
                        "turn": turn,
                        "slug": payload.get("slug", ""),
                        "risk": payload.get("risk", "medium"),
                        "owasp_category": payload.get("owasp_category", ""),
                        "refinement": payload.get("refinement"),
                    },
                )

                # ── Interaction layer (guarded) ─────────────────────────────
                try:
                    response = await self._connector_for_run().exchange(payload["messages"])
                except SafetyError as exc:
                    await self._emit(
                        "orchestrator",
                        "safety_blocked",
                        {"code": exc.code, "message": str(exc)},
                    )
                    self.run.status = "failed"
                    self.run.error = f"Safety layer blocked interaction: {exc}"
                    await self._session.flush()
                    await self._emit("orchestrator", "run_failed", {"error": self.run.error})
                    return self.run
                except ConnectorError as exc:
                    await self._emit("interaction", "connector_error", {"error": str(exc)})
                    self.run.status = "failed"
                    self.run.error = f"Connector error: {exc}"
                    await self._session.flush()
                    await self._emit("orchestrator", "run_failed", {"error": self.run.error})
                    return self.run

                total_tokens += response.tokens
                snippet = self._redactor.redact(response.body[:500])
                await self._emit(
                    "interaction",
                    "target_response",
                    {
                        "turn": turn,
                        "status_code": response.status_code,
                        "tokens": response.tokens,
                        "duration_ms": response.duration_ms,
                        "response_snippet": snippet,
                    },
                )

                # ── Judge ───────────────────────────────────────────────────
                context = DetectionContext(
                    payload=payload,
                    messages=payload["messages"],
                    response_text=response.body,
                    status_code=response.status_code,
                    duration_ms=response.duration_ms,
                    target=self.target.config,
                )
                verdict = await self._judge.evaluate(context)
                await self._emit(
                    "judge",
                    "verdict",
                    {
                        "turn": turn,
                        "success": verdict.success,
                        "severity": verdict.severity,
                        "confidence": verdict.confidence,
                        "summary": verdict.summary,
                        "detection_count": len(verdict.detections),
                    },
                )

                turn_record = TurnRecord(
                    payload=payload,
                    messages=payload["messages"],
                    response_text=response.body,
                    status_code=response.status_code,
                    duration_ms=response.duration_ms,
                    tokens=response.tokens,
                    audit_ref=None,
                    verdict=verdict,
                    mutation_strategy=payload.get("refinement", {}).get("strategy"),
                )
                await self._memory.record_turn(self.run, turn_record, turn)

                # ── Success path: record, then keep probing remaining payloads ──
                if verdict.success:
                    for detection in verdict.detections:
                        category = detection.get("category", "other")
                        if category in recorded_categories:
                            continue
                        recorded_categories.add(category)
                        finding = await self._memory.record_finding(
                            self.run, self.target, turn_record, verdict, detection, None
                        )
                        await self._emit(
                            "memory",
                            "finding_recorded",
                            {
                                "finding_id": finding.id,
                                "category": category,
                                "severity": finding.severity,
                                "confidence": finding.confidence,
                                "title": finding.title,
                            },
                        )
                        await self._memory.record_success_feedback(
                            self.run, self.target, finding, turn_record
                        )
                    await self._emit("orchestrator", "attack_resolved", {"turn": turn})
                    attempted.add(payload.get("slug", ""))
                    resolved.add(payload.get("slug", ""))
                    continue

                # ── Refiner ─────────────────────────────────────────────────
                refined_payload = await self._refiner.refine(
                    payload, used_strategies=used_strategies
                )
                if refined_payload is None:
                    await self._emit("refiner", "exhausted", {"slug": payload.get("slug", "")})
                    attempted.add(payload.get("slug", ""))
                    continue
                strategy = refined_payload["refinement"]["strategy"]
                used_strategies.add(strategy)
                refined.add(payload.get("slug", ""))
                await self._emit(
                    "refiner",
                    "mutation",
                    {
                        "turn": turn,
                        "slug": payload.get("slug", ""),
                        "strategy": strategy,
                        "attempted_strategies": sorted(used_strategies),
                    },
                )
                self.payloads = [refined_payload, *self.payloads]

            # ── Wrap up ─────────────────────────────────────────────────────
            self.run.status = "completed"
            self.run.tokens_used = total_tokens
            self.run.cost_estimate_usd = round(
                total_tokens / 1000 * COST_PER_1K_TOKENS, 4
            )
        except Exception as exc:  # noqa: BLE001 — run must not die silently
            self.run.status = "failed"
            self.run.error = f"{type(exc).__name__}: {exc}"
            await self._emit("orchestrator", "run_failed", {"error": self.run.error})
        finally:
            self.run.finished_at = datetime.now(timezone.utc)
            self.run.tokens_used = total_tokens
            self.run.cost_estimate_usd = round(total_tokens / 1000 * COST_PER_1K_TOKENS, 4)
            await self._session.flush()
            await self._emit(
                "orchestrator",
                "run_finished",
                {
                    "status": self.run.status,
                    "findings": self.run.findings_count,
                    "tokens": self.run.tokens_used,
                    "cost_usd": self.run.cost_estimate_usd,
                    "elapsed_seconds": round(time.monotonic() - start, 2),
                },
            )
        return self.run

    # ── helpers ─────────────────────────────────────────────────────────────
    def _connector_for_run(self) -> TargetConnector:
        if self._connector is not None:
            return self._connector
        if self.run.dry_run:
            return DryRunConnector(
                self.target, self._guard, run_id=self.run.id, actor=self.run.started_by
            )
        return build_connector(
            self.target,
            self._guard,
            run_id=self.run.id,
            actor=self.run.started_by,
        )

    async def _emit(self, agent: str, event_type: str, payload: dict[str, Any]) -> None:
        await self._events.emit(
            run_id=self.run.id, agent=agent, event_type=event_type, payload=payload
        )


async def materialize_payloads(
    session: AsyncSession, pack_ids: list[str]
) -> list[dict[str, Any]]:
    """Load payloads from DB for the given packs, ordered by priority."""
    from sqlalchemy import select

    from app.models import Payload

    stmt = (
        select(Payload)
        .where(Payload.pack_id.in_(pack_ids))
        .order_by(Payload.priority.desc())
    )
    rows = (await session.execute(stmt)).scalars().all()
    return [
        {
            "id": p.id,
            "db_id": p.id,
            "slug": p.slug,
            "name": p.name,
            "risk": p.risk,
            "attack_vector": p.attack_vector,
            "owasp_category": p.owasp_category,
            "mitre_atlas_id": p.mitre_atlas_id,
            "messages": p.messages,
            "expected_behaviors": p.expected_behaviors,
            "priority": p.priority,
        }
        for p in rows
    ]
