"""Redis client (lazy) with graceful degradation.

Redis backs rate limiting, the job queue, and cross-process event fan-out.
When Redis is unreachable the app degrades to in-process substitutes so the
demo and test suite run without external services — safety controls still
enforce their invariants, they just don't share state across processes.
"""

from __future__ import annotations

import asyncio
from functools import lru_cache
from typing import Any

from app.core.config import get_settings


@lru_cache
def get_redis_url() -> str:
    return get_settings().redis_url


def _redis_available() -> bool:
    try:
        import redis.asyncio as aioredis  # noqa: F401
        return True
    except Exception:
        return False


async def get_redis() -> Any:
    """Return an async redis client or None if unavailable.

    Callers must handle None (degrade to in-process behaviour).
    """
    if not _redis_available():
        return None
    try:
        import redis.asyncio as aioredis

        client = aioredis.from_url(get_redis_url(), decode_responses=True)
        await client.ping()
        return client
    except Exception:
        return None


async def close_redis() -> None:
    pass


class InProcessPubSub:
    """Minimal in-process pub/sub used when Redis is absent (single-process)."""

    def __init__(self) -> None:
        self._subscribers: dict[str, set[asyncio.Queue]] = {}

    async def publish(self, channel: str, message: str) -> None:
        for queue in list(self._subscribers.get(channel, ())):
            if queue.full():
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            await queue.put(message)

    async def subscribe(self, channel: str) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue(maxsize=500)
        self._subscribers.setdefault(channel, set()).add(queue)
        return queue

    async def unsubscribe(self, channel: str, queue: asyncio.Queue) -> None:
        self._subscribers.get(channel, set()).discard(queue)


@lru_cache
def get_pubsub() -> InProcessPubSub:
    return InProcessPubSub()
