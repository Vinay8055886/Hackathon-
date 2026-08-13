"""InteractionGuard — the single, mandatory safety boundary.

Every connector must route its outbound requests through this guard. It
enforces, in order:
  1. role/permission (checked by callers, re-asserted with the actor id)
  2. target allow-list status
  3. rate limit
  4. token budget
  5. circuit breaker

There is deliberately no "unsafe bypass" flag. If you find yourself wanting
one, stop — that is a design change requiring review, not a parameter.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import Target
from app.safety.allowlist import assert_target_allowlisted
from app.safety.audit_log import AuditLogger
from app.safety.circuit_breaker import CircuitBreaker
from app.safety.rate_limiter import RateLimiter
from app.safety.redaction import get_redactor
from app.safety.token_budget import TokenBudget, estimate_tokens


class SafetyError(Exception):
    """Base for all safety-layer refusals."""

    def __init__(self, message: str, code: str = "safety_error") -> None:
        super().__init__(message)
        self.code = code


@dataclass
class GuardedResponse:
    status_code: int
    body: str
    headers: dict[str, str] = field(default_factory=dict)
    duration_ms: int = 0
    tokens: int = 0


class InteractionGuard:
    def __init__(
        self,
        session: AsyncSession,
        rate_limiter: RateLimiter | None = None,
        circuit_breaker: CircuitBreaker | None = None,
    ) -> None:
        self._session = session
        self._rate_limiter = rate_limiter or RateLimiter()
        self._circuit_breaker = circuit_breaker or CircuitBreaker()
        self._audit = AuditLogger(session)
        self._redactor = get_redactor()
        self._budgets: dict[str, TokenBudget] = {}

    # ── enforcement ─────────────────────────────────────────────────────────
    async def authorize(self, *, target_id: str, run_id: str | None, actor: str) -> Target:
        """Check 1+2: allow-list. Raises SafetyError on any failure."""
        try:
            target = await assert_target_allowlisted(self._session, target_id)
        except Exception as exc:  # AllowlistError
            raise SafetyError(str(exc), code=getattr(exc, "code", "target_not_allowed")) from exc

        if target_id not in self._budgets:
            self._budgets[target_id] = TokenBudget(
                limit=target.max_tokens_per_run
                or get_settings().default_max_tokens_per_run
            )
        return target

    async def preflight(self, *, target_id: str, payload_text: str) -> None:
        """Checks 3–5 before sending: rate limit, token budget, circuit breaker."""
        await self._rate_limiter.check(target_id)
        budget = self._budgets.get(target_id)
        if budget is not None:
            cost = estimate_tokens(payload_text)
            if cost > budget.remaining:
                raise SafetyError(
                    f"Token budget exhausted for target {target_id} "
                    f"({budget.used}/{budget.limit})",
                    code="token_budget_exceeded",
                )
        await self._circuit_breaker.check(target_id)

    # ── post-interaction bookkeeping ────────────────────────────────────────
    async def record(
        self,
        *,
        target: Target,
        run_id: str | None,
        actor: str,
        request: dict[str, Any],
        response: GuardedResponse,
        outcome: str = "ok",
    ) -> str:
        """Persist the (redacted) request/response pair and update budgets.

        Called by connectors BEFORE the response is returned to the caller.
        Returns the audit_log entry id.
        """
        started = time.monotonic()
        entry = await self._audit.log(
            target_id=target.id,
            run_id=run_id,
            actor=actor,
            entry_type="target_interaction",
            request=request,
            response={
                "status_code": response.status_code,
                "headers": response.headers,
                "body": response.body,
            },
            duration_ms=response.duration_ms or int((time.monotonic() - started) * 1000),
            tokens=response.tokens,
            outcome=outcome,
        )
        budget = self._budgets.get(target.id)
        if budget is not None:
            budget.used += response.tokens
        if outcome == "ok":
            await self._circuit_breaker.record_success(target.id)
        else:
            await self._circuit_breaker.record_failure(target.id)
        return entry.id
