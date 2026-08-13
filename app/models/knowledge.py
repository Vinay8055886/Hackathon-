"""Intelligence store models: knowledge entries (embeddings) + knowledge-graph edges."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.helpers import new_id, utcnow


class KnowledgeEntry(Base):
    """One historical attack transcript / weakness pattern with an embedding.

    ``embedding`` stores a JSON-encoded float vector (default store) or a
    pgvector column (when AEGIS_VECTOR_STORE=pgvector; see alembic migration
    which creates the column as VECTOR(1536) on PostgreSQL).
    """

    __tablename__ = "knowledge_entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    kind: Mapped[str] = mapped_column(String(32), index=True)  # attack_transcript|weakness_pattern
    target_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    run_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    text: Mapped[str] = mapped_column(Text)
    embedding: Mapped[str] = mapped_column(Text)  # JSON list; pgvector in PG mode
    meta: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class KGEdge(Base):
    """Lightweight knowledge-graph edge (works without Neo4j).

    Relationship triples like (technique:T1566.002) -[affects]-> (target:acme-chat).
    A Neo4j adapter is provided in app/intelligence/knowledge_graph.py.
    """

    __tablename__ = "kg_edges"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    source: Mapped[str] = mapped_column(String(255), index=True)
    relation: Mapped[str] = mapped_column(String(64), index=True)
    target: Mapped[str] = mapped_column(String(255), index=True)
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    meta: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
