"""Event bus for live run streaming.

Every agent action is emitted as an event: it is persisted as an
``agent_events`` row (audit + replay) and fanned out to the run's SSE channel
(Redis pub/sub, or the in-process pub/sub when Redis is absent).
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_pubsub, get_redis
from app.models import AgentEvent


class EventPublisher:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._sequence = 0

    async def emit(
        self,
        *,
        run_id: str,
        agent: str,
        event_type: str,
        payload: dict[str, Any],
    ) -> AgentEvent:
        self._sequence += 1
        row = AgentEvent(
            run_id=run_id,
            sequence=self._sequence,
            agent=agent,
            event_type=event_type,
            payload=payload,
        )
        self._session.add(row)
        await self._session.flush()

        message = json.dumps(
            {
                "sequence": self._sequence,
                "run_id": run_id,
                "agent": agent,
                "event_type": event_type,
                "payload": payload,
            }
        )
        redis = await get_redis()
        if redis is not None:
            try:
                await redis.publish(f"aegis:events:{run_id}", message)
                return row
            except Exception:
                pass
        await get_pubsub().publish(f"aegis:events:{run_id}", message)
        return row


async def subscribe_run(run_id: str):
    """Return an async iterator of raw event strings for a run's SSE stream."""
    redis = await get_redis()
    if redis is not None:
        try:
            pubsub = redis.pubsub()
            await pubsub.subscribe(f"aegis:events:{run_id}")
            return _RedisStream(pubsub)
        except Exception:
            pass
    return _InProcStream(await get_pubsub().subscribe(f"aegis:events:{run_id}"))


class _RedisStream:
    def __init__(self, pubsub) -> None:
        self._pubsub = pubsub

    async def __aiter__(self):
        async for message in self._pubsub.listen():
            if message.get("type") == "message":
                yield message["data"]

    async def aclose(self) -> None:
        try:
            await self._pubsub.unsubscribe()
            await self._pubsub.aclose()
        except Exception:
            pass


class _InProcStream:
    def __init__(self, queue) -> None:
        self._queue = queue

    async def __aiter__(self):
        while True:
            yield await self._queue.get()

    async def aclose(self) -> None:
        pass
