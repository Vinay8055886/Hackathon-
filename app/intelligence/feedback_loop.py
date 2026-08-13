"""Continuous-learning feedback loop.

When an attack succeeds:
  * the winning payload's priority is boosted (so similar targets are tested
    with it first),
  * the transcript is embedded into the vector store,
  * technique → target → weakness edges are written to the knowledge graph.

This is the memory that makes future runs cheaper and smarter.
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.intelligence.knowledge_graph import KnowledgeGraph
from app.intelligence.vector_store import build_vector_store
from app.models import Finding, Payload, Run, Target


class FeedbackLoop:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._vector_store = build_vector_store(session)
        self._graph = KnowledgeGraph(session)

    async def store_transcript(
        self,
        *,
        run_id: str | None,
        target_id: str | None,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        return await self._vector_store.add(
            kind="attack_transcript",
            text=text,
            metadata=metadata or {},
            target_id=target_id,
            run_id=run_id,
        )

    async def record_success(
        self,
        *,
        run: Run,
        target: Target,
        finding: Finding,
        transcript: str,
    ) -> None:
        # 1) boost priority of the winning payload
        if finding.payload_id:
            await self._session.execute(
                update(Payload)
                .where(Payload.id == finding.payload_id)
                .values(priority=Payload.priority * 1.2)
            )
        # 2) embed the transcript for future similarity search
        await self._vector_store.add(
            kind="attack_transcript",
            text=transcript,
            metadata={
                "category": finding.category,
                "severity": finding.severity,
                "owasp_category": finding.owasp_category,
                "mitre_atlas_id": finding.mitre_atlas_id,
                "target_id": target.id,
                "target_name": target.name,
            },
            target_id=target.id,
            run_id=run.id,
        )
        # 3) knowledge-graph edges
        await self._graph.add_edge(
            f"technique:{finding.mitre_atlas_id}",
            "compromises",
            f"target:{target.id}",
            weight=1.0,
            metadata={"finding_id": finding.id},
        )
        await self._graph.add_edge(
            f"target:{target.id}",
            "exhibits",
            f"weakness:{finding.category}",
            weight=1.0,
            metadata={"finding_id": finding.id},
        )

    async def similar_historical(self, text: str, k: int = 5) -> list[dict[str, Any]]:
        results = await self._vector_store.search(text, k=k)
        return [
            {"id": r.id, "text": r.text, "score": round(r.score, 4), "metadata": r.metadata}
            for r in results
        ]

    async def boosted_payload_ids(self, category: str | None = None) -> dict[str, float]:
        """payload_id -> priority for payloads whose category has historical wins."""
        stmt = select(Payload.id, Payload.priority).where(Payload.priority > 1.0)
        if category:
            stmt = stmt.where(Payload.owasp_category == category)
        rows = (await self._session.execute(stmt)).all()
        return {str(r[0]): float(r[1]) for r in rows}
