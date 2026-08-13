"""Target model — every system under test must be registered and allow-listed."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.helpers import new_id, utcnow


class Target(Base):
    __tablename__ = "targets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    connector_type: Mapped[str] = mapped_column(String(32), index=True)  # rest|browser|websocket
    endpoint: Mapped[str] = mapped_column(String(1024))
    # Connector-specific configuration (headers, JSON body template, selectors…)
    config: Mapped[dict] = mapped_column(JSON, default=dict)

    # Safety posture
    allowlisted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    approved_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    approval_note: Mapped[str] = mapped_column(Text, default="")

    owner_id: Mapped[str] = mapped_column(String(36), index=True)
    auth_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    rate_limit_per_minute: Mapped[int | None] = mapped_column(nullable=True)
    max_tokens_per_run: Mapped[int | None] = mapped_column(nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
