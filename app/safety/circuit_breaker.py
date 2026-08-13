"""Circuit breaker — per target.

If a target starts failing (timeouts, 5xx, malformed responses) the breaker
trips open and refuses further traffic until the cooldown elapses. This
protects both the target and the platform.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field

from app.core.config import get_settings


class CircuitOpen(Exception):
    def __init__(self, target_id: str, retry_after: float) -> None:
        super().__init__(f"Circuit open for target {target_id}")
        self.target_id = target_id
        self.retry_after = retry_after


@dataclass
class _BreakerState:
    consecutive_failures: int = 0
    open_until: float = 0.0
    half_open_probe_in_flight: bool = False


class CircuitBreaker:
    """In-process breaker. (A Redis-shared variant can be added for multi-worker.)"""

    def __init__(
        self,
        failure_threshold: int | None = None,
        cooldown_seconds: int | None = None,
    ) -> None:
        settings = get_settings()
        self.failure_threshold = (
            failure_threshold or settings.circuit_breaker_failure_threshold
        )
        self.cooldown_seconds = (
            cooldown_seconds or settings.circuit_breaker_cooldown_seconds
        )
        self._states: dict[str, _BreakerState] = {}
        self._lock = asyncio.Lock()

    async def check(self, target_id: str) -> None:
        async with self._lock:
            state = self._states.setdefault(target_id, _BreakerState())
            now = time.monotonic()
            if state.open_until > now:
                raise CircuitOpen(target_id, retry_after=state.open_until - now)

    async def record_success(self, target_id: str) -> None:
        async with self._lock:
            state = self._states.setdefault(target_id, _BreakerState())
            state.consecutive_failures = 0
            state.open_until = 0.0
            state.half_open_probe_in_flight = False

    async def record_failure(self, target_id: str) -> None:
        async with self._lock:
            state = self._states.setdefault(target_id, _BreakerState())
            state.consecutive_failures += 1
            if state.consecutive_failures >= self.failure_threshold:
                state.open_until = time.monotonic() + self.cooldown_seconds
