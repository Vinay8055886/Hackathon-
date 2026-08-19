"""Login rate limiter — per-IP sliding window.

Protects /auth/login (and any other sensitive endpoint) from brute-force
attacks.  Uses an in-process sliding window keyed by client IP.  In a
multi-worker deployment this should be swapped for a Redis-backed variant
(see rate_limiter.py for the pattern).
"""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque


class LoginRateLimitExceeded(Exception):
    """Raised when the IP has exceeded the login attempt limit."""

    def __init__(self, retry_after: float) -> None:
        super().__init__("Too many login attempts")
        self.retry_after = retry_after


class LoginRateLimiter:
    """Sliding-window rate limiter for login attempts.

    Parameters
    ----------
    max_attempts : int
        Maximum number of attempts allowed in the window (default 5).
    window_seconds : int
        Rolling window duration in seconds (default 900 = 15 minutes).
    """

    def __init__(
        self,
        max_attempts: int = 5,
        window_seconds: int = 15 * 60,
    ) -> None:
        self._max_attempts = max_attempts
        self._window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def check(self, ip: str) -> None:
        """Raise LoginRateLimitExceeded if the IP is over the limit."""
        now = time.monotonic()
        async with self._lock:
            window_start = now - self._window_seconds
            q = self._hits[ip]
            # Evict expired entries
            while q and q[0] < window_start:
                q.popleft()
            if len(q) >= self._max_attempts:
                retry_after = q[0] + self._window_seconds - now
                raise LoginRateLimitExceeded(retry_after=max(retry_after, 0.0))

    async def record(self, ip: str) -> None:
        """Record a login attempt for the given IP."""
        now = time.monotonic()
        async with self._lock:
            window_start = now - self._window_seconds
            q = self._hits[ip]
            while q and q[0] < window_start:
                q.popleft()
            q.append(now)


# Module-level singleton
_login_limiter = LoginRateLimiter()


def get_login_limiter() -> LoginRateLimiter:
    return _login_limiter
