"""Target connector interface.

Every connector must route its outbound traffic through InteractionGuard.
The shared ``exchange`` flow below guarantees that:
  1. allow-list check
  2. rate limit / token budget / circuit breaker preflight
  3. raw request (``_perform``)
  4. audit-log persistence of the REDACTED pair
  5. post-interaction bookkeeping

Happens in that order for every single request — no code path can bypass it.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.core.config import get_settings
from app.models import Target
from app.safety import GuardedResponse, InteractionGuard, SafetyError


class ConnectorError(Exception):
    pass


class TargetConnector(ABC):
    connector_type: str = "base"

    def __init__(
        self,
        target: Target,
        guard: InteractionGuard,
        *,
        run_id: str | None = None,
        actor: str = "system",
    ) -> None:
        self.target = target
        self.guard = guard
        self.run_id = run_id
        self.actor = actor
        self._closed = False

    async def exchange(self, messages: list[dict[str, str]]) -> GuardedResponse:
        """Send a message list to the target through the guard."""
        if self._closed:
            raise ConnectorError("Connector is closed")
        payload_text = "\n".join(
            f"{m.get('role', 'user')}: {m.get('content', '')}" for m in messages
        )
        # 1. allow-list + budget init
        target = await self.guard.authorize(
            target_id=self.target.id, run_id=self.run_id, actor=self.actor
        )
        # 2. preflight (rate limit, token budget, circuit breaker)
        await self.guard.preflight(target_id=target.id, payload_text=payload_text)
        # 3. raw request
        response = await self._perform(messages)
        # 4. audit + 5. bookkeeping BEFORE returning to caller
        await self.guard.record(
            target=target,
            run_id=self.run_id,
            actor=self.actor,
            request={"messages": messages},
            response=response,
            outcome="ok" if 200 <= response.status_code < 500 else "error",
        )
        return response

    @abstractmethod
    async def _perform(self, messages: list[dict[str, str]]) -> GuardedResponse:
        """The raw interaction. Subclasses implement this only."""

    async def close(self) -> None:
        self._closed = True

    async def __aenter__(self) -> "TargetConnector":
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.close()
