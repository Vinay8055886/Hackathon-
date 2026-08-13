"""Audit log model — immutable record of every request/response pair (redacted)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.helpers import new_id, utcnow


class AuditLogEntry(Base):
    __tablename__ = "audit_log"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    run_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    target_id: Mapped[str] = mapped_column(String(36), index=True)
    actor: Mapped[str] = mapped_column(String(128), default="system")
    # request | response | agent_action | run_control | auth
    entry_type: Mapped[str] = mapped_column(String(32), index=True)

    # Redaction applied BEFORE persist — these fields never contain secrets.
    request_redacted: Mapped[dict] = mapped_column(JSON, default=dict)
    response_redacted: Mapped[dict] = mapped_column(JSON, default=dict)

    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    tokens: Mapped[int] = mapped_column(Integer, default=0)
    outcome: Mapped[str] = mapped_column(String(32), default="ok")  # ok|error|blocked
    redaction_note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
