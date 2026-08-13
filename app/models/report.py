"""Report model — generated artifacts linked to a run."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.helpers import new_id, utcnow


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    run_id: Mapped[str] = mapped_column(String(36), index=True)
    format: Mapped[str] = mapped_column(String(16), index=True)  # html|sarif|json
    storage_path: Mapped[str] = mapped_column(String(1024))
    size_bytes: Mapped[int] = mapped_column(default=0)
    generated_by: Mapped[str] = mapped_column(String(128), default="system")
    meta: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
