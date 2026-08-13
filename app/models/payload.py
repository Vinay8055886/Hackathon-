"""Payload pack + payload models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.helpers import new_id, utcnow


class PayloadPack(Base):
    __tablename__ = "payload_packs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    version: Mapped[str] = mapped_column(String(32), default="1.0.0")
    description: Mapped[str] = mapped_column(Text, default="")
    owasp_categories: Mapped[list] = mapped_column(JSON, default=list)  # e.g. ["LLM01"]
    mitre_atlas_ids: Mapped[list] = mapped_column(JSON, default=list)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    source: Mapped[str] = mapped_column(String(255), default="bundled")  # bundled|uploaded
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Payload(Base):
    __tablename__ = "payloads"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    pack_id: Mapped[str] = mapped_column(String(36), index=True)
    slug: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    risk: Mapped[str] = mapped_column(String(16), default="medium")  # low|medium|high|critical
    attack_vector: Mapped[str] = mapped_column(String(64), default="direct")  # direct|indirect|multi_turn
    owasp_category: Mapped[str] = mapped_column(String(16), index=True)
    mitre_atlas_id: Mapped[str] = mapped_column(String(64), index=True)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    # Conversation to send: [{"role": "system"|"user", "content": "..."}]
    messages: Mapped[list] = mapped_column(JSON, default=list)
    expected_behaviors: Mapped[list] = mapped_column(JSON, default=list)
    priority: Mapped[float] = mapped_column(default=1.0)  # boosted by feedback loop
    plugin: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
