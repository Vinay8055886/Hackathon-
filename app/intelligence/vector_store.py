"""Vector store over historical attack transcripts and weakness patterns.

Two backends behind one interface:
  * ``NumpyVectorStore`` (default) — embeddings stored as JSON, cosine
    similarity computed in-process with numpy. Works on SQLite (demo/tests)
    and Postgres.
  * ``PgVectorStore`` — native pgvector ``<=>`` operator on PostgreSQL.

Embeddings come from a configured embeddings API (OpenAI-compatible) or, when
unset, from a deterministic n-gram hash embedding so the platform is fully
functional offline.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import KnowledgeEntry

EMBED_DIM = 512


@dataclass
class ScoredEntry:
    id: str
    text: str
    score: float
    metadata: dict[str, Any]


def embed_text(text: str) -> list[float]:
    """Return an embedding vector for text.

    Uses the configured embeddings API when AEGIS_EMBEDDING_API_BASE is set,
    otherwise a deterministic n-gram hash embedding (stable, offline).
    """
    settings = get_settings()
    if settings.embedding_api_base and settings.embedding_api_key:
        try:
            return _embed_via_api(text)
        except Exception:
            pass  # fall through to deterministic hashing
    return _hash_embed(text)


def _hash_embed(text: str) -> list[float]:
    vec = [0.0] * EMBED_DIM
    lowered = text.lower()
    n = len(lowered)
    for i in range(max(1, n - 3)):
        gram = lowered[i : i + 4]
        digest = hashlib.sha256(gram.encode()).digest()
        idx = int.from_bytes(digest[:4], "big") % EMBED_DIM
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vec[idx] += sign
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [round(v / norm, 6) for v in vec]


def _embed_via_api(text: str) -> list[float]:
    import httpx

    settings = get_settings()
    resp = httpx.post(
        f"{settings.embedding_api_base.rstrip('/')}/embeddings",
        headers={"Authorization": f"Bearer {settings.embedding_api_key}"},
        json={"model": settings.embedding_model, "input": text},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["data"][0]["embedding"]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    import numpy as np

    va, vb = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    denom = float(np.linalg.norm(va) * np.linalg.norm(vb))
    if denom == 0:
        return 0.0
    return float(np.dot(va, vb) / denom)


class NumpyVectorStore:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(
        self,
        *,
        kind: str,
        text: str,
        metadata: dict[str, Any] | None = None,
        target_id: str | None = None,
        run_id: str | None = None,
    ) -> str:
        entry = KnowledgeEntry(
            kind=kind,
            target_id=target_id,
            run_id=run_id,
            text=text,
            embedding=json.dumps(embed_text(text)),
            meta=metadata or {},
        )
        self._session.add(entry)
        await self._session.flush()
        return entry.id

    async def search(self, query: str, k: int = 5, kind: str | None = None) -> list[ScoredEntry]:
        stmt = select(KnowledgeEntry)
        if kind:
            stmt = stmt.where(KnowledgeEntry.kind == kind)
        rows = (await self._session.execute(stmt)).scalars().all()
        q = embed_text(query)
        scored: list[ScoredEntry] = []
        for row in rows:
            try:
                vec = json.loads(row.embedding)
            except (json.JSONDecodeError, TypeError):
                continue
            score = cosine_similarity(q, vec)
            if score <= 0:
                continue
            scored.append(
                ScoredEntry(id=row.id, text=row.text, score=score, metadata=row.meta)
            )
        scored.sort(key=lambda e: e.score, reverse=True)
        return scored[:k]


class PgVectorStore:
    """Native pgvector backend. Requires the knowledge_entries.embedding column
    to be VECTOR(1536) (created by the alembic migration on PostgreSQL)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(
        self,
        *,
        kind: str,
        text: str,
        metadata: dict[str, Any] | None = None,
        target_id: str | None = None,
        run_id: str | None = None,
    ) -> str:
        entry = KnowledgeEntry(
            kind=kind,
            target_id=target_id,
            run_id=run_id,
            text=text,
            embedding=json.dumps(embed_text(text)),
            meta=metadata or {},
        )
        self._session.add(entry)
        await self._session.flush()
        return entry.id

    async def search(self, query: str, k: int = 5, kind: str | None = None) -> list[ScoredEntry]:
        vec = json.dumps(embed_text(query))
        sql = (
            "SELECT id, text, meta, embedding <=> CAST(:vec AS vector) AS distance "
            "FROM knowledge_entries"
        )
        params: dict[str, Any] = {"vec": vec}
        if kind:
            sql += " WHERE kind = :kind"
            params["kind"] = kind
        sql += " ORDER BY distance LIMIT :k"
        params["k"] = k
        result = await self._session.execute(text(sql), params)
        rows = result.all()
        return [
            ScoredEntry(id=r[0], text=r[1], score=round(1.0 - float(r[3]), 6), metadata=r[2])
            for r in rows
        ]


def build_vector_store(session: AsyncSession) -> NumpyVectorStore | PgVectorStore:
    if get_settings().vector_store == "pgvector":
        return PgVectorStore(session)
    return NumpyVectorStore(session)
