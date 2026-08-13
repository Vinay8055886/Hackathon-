"""Rate limiter — Redis-backed, with an in-process fallback.

Keyed per target so a single noisy run cannot hammer one endpoint while
leaving other targets untouched.
"""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict, deque

from app.core.config import get_settings


class RateLimitExceeded(Exception):
    def __init__(self, target_id: str, retry_after: float) -> None:
        super().__init__(f"Rate limit exceeded for target {target_id}")
        self.target_id = target_id
        self.retry_after = retry_after


class _MemoryCounter:
    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def hit(self, key: str, limit: int, window_seconds: int) -> tuple[bool, float]:
        now = time.monotonic()
        async with self._lock:
            window_start = now - window_seconds
            q = self._hits[key]
            while q and q[0] < window_start:
                q.popleft()
            if len(q) >= limit:
                retry_after = q[0] + window_seconds - now if q else 0.0
                return False, max(retry_after, 0.0)
            q.append(now)
            return True, 0.0


class RateLimiter:
    """Sliding-window limiter. Redis when available, else in-process."""

    def __init__(self, redis=None) -> None:
        self._redis = redis
        self._memory = _MemoryCounter()

    async def check(
        self, target_id: str, limit_per_minute: int | None = None
    ) -> None:
        limit = limit_per_minute or get_settings().rate_limit_per_minute
        key = f"aegis:ratelimit:{target_id}"
        if self._redis is not None:
            pipe = self._redis.pipeline()
            now_ms = int(time.time() * 1000)
            window_ms = 60_000
            pipe.zremrangebyscore(key, 0, now_ms - window_ms)
            pipe.zcard(key)
            pipe.zadd(key, {f"{now_ms}-{asyncio.get_event_loop().time()}": now_ms})
            pipe.expire(key, 120)
            results = await pipe.execute()
            count = int(results[1])
            if count >= limit:
                raise RateLimitExceeded(target_id, retry_after=1.0)
            return
        allowed, retry_after = await self._memory.hit(key, limit, 60)
        if not allowed:
            raise RateLimitExceeded(target_id, retry_after=retry_after)
