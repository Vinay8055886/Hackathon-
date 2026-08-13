"""Knowledge graph of attack techniques ↔ targets ↔ weaknesses.

Default implementation stores edges in the ``kg_edges`` table (portable).
When NEO4J_URI is configured a ``Neo4jKnowledgeGraph`` adapter (raw driver,
no ORM) is used instead — see the enterprise extra.
"""

from __future__ import annotations

import os
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import KGEdge


class KnowledgeGraph:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_edge(
        self,
        source: str,
        relation: str,
        target: str,
        weight: float = 1.0,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        edge = KGEdge(
            source=source,
            relation=relation,
            target=target,
            weight=weight,
            metadata=metadata or {},
        )
        self._session.add(edge)
        await self._session.flush()
        return edge.id

    async def neighbors(self, node: str, relation: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        stmt = select(KGEdge).where(
            (KGEdge.source == node) | (KGEdge.target == node)
        )
        if relation:
            stmt = stmt.where(KGEdge.relation == relation)
        stmt = stmt.limit(limit)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [
            {
                "source": r.source,
                "relation": r.relation,
                "target": r.target,
                "weight": r.weight,
                "metadata": r.metadata,
            }
            for r in rows
        ]

    async def paths(self, start: str, end: str, max_depth: int = 3) -> list[list[str]]:
        """BFS over stored edges — a tiny graph walk for local mode."""
        frontier = [[start]]
        for _ in range(max_depth):
            next_frontier: list[list[str]] = []
            for path in frontier:
                last = path[-1]
                stmt = select(KGEdge).where(KGEdge.source == last)
                rows = (await self._session.execute(stmt)).scalars().all()
                for row in rows:
                    new_path = path + [row.target]
                    if row.target == end:
                        return [new_path]
                    next_frontier.append(new_path)
            frontier = next_frontier
        return []


class Neo4jKnowledgeGraph:
    """Adapter for Neo4j (enterprise extra). Replace the default graph by
    constructing this class directly when NEO4J_URI is set."""

    def __init__(self, uri: str, user: str, password: str) -> None:
        self._uri = uri
        self._user = user
        self._password = password
        self._driver = None

    def _connect(self):
        if self._driver is None:
            from neo4j import GraphDatabase

            self._driver = GraphDatabase.driver(self._uri, auth=(self._user, self._password))
        return self._driver

    def add_edge(self, source: str, relation: str, target: str, weight: float = 1.0) -> None:
        with self._connect().session() as session:
            session.run(
                "MERGE (a:Node {name: $s}) MERGE (b:Node {name: $t}) "
                "MERGE (a)-[r:REL {relation: $rel}]->(b) "
                "SET r.weight = $w",
                s=source, t=target, rel=relation, w=weight,
            )

    def neighbors(self, node: str, relation: str | None = None) -> list[dict[str, Any]]:
        query = "MATCH (n:Node {name: $node})-[r]->(m:Node) RETURN m.name AS target, r.relation AS relation, r.weight AS weight"
        with self._connect().session() as session:
            rows = session.run(query, node=node).data()
        return rows

    def close(self) -> None:
        if self._driver is not None:
            self._driver.close()
            self._driver = None
