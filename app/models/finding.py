"""Finding model — confirmed or suspected vulnerability."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.helpers import new_id, utcnow


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    run_id: Mapped[str] = mapped_column(String(36), index=True)
    target_id: Mapped[str] = mapped_column(String(36), index=True)
    payload_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)

    title: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(64), index=True)
    # prompt_injection | system_prompt_leak | pii_leak | secret_leak |
    # guardrail_bypass | tool_abuse | hallucination | resource_exhaustion | other
    owasp_category: Mapped[str] = mapped_column(String(16), index=True)
    mitre_atlas_id: Mapped[str] = mapped_column(String(64), index=True)
    severity: Mapped[str] = mapped_column(String(16), index=True)  # low|medium|high|critical
    confidence: Mapped[float] = mapped_column(Float, default=0.5)

    # Evidence: raw (kept internally, redacted before display) + redacted copy
    evidence: Mapped[dict] = mapped_column(JSON, default=dict)
    redacted_evidence: Mapped[dict] = mapped_column(JSON, default=dict)
    transcript_refs: Mapped[list] = mapped_column(JSON, default=list)  # audit_log entry ids

    remediation_guidance: Mapped[str] = mapped_column(Text, default="")
    false_positive: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(32), default="open", index=True)
    # open | confirmed | triaged | accepted | fixed
    detector: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
