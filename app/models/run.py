"""Attack run + agent event models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.helpers import new_id, utcnow


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    target_id: Mapped[str] = mapped_column(String(36), index=True)
    payload_pack_ids: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(32), default="scheduled", index=True)
    # scheduled | running | completed | failed | cancelled
    dry_run: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    started_by: Mapped[str] = mapped_column(String(36), index=True)
    max_turns: Mapped[int] = mapped_column(Integer, default=10)
    token_budget: Mapped[int] = mapped_column(Integer, default=200_000)
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    cost_estimate_usd: Mapped[float] = mapped_column(Float, default=0.0)
    findings_count: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AgentEvent(Base):
    """Turn-by-turn log of Attacker/Judge/Refiner/Memory actions.

    This is the audit + replay trail for a run.
    """

    __tablename__ = "agent_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    run_id: Mapped[str] = mapped_column(String(36), index=True)
    sequence: Mapped[int] = mapped_column(Integer, default=0)
    agent: Mapped[str] = mapped_column(String(32), index=True)  # attacker|judge|refiner|memory
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    # turn, payload, message, verdict, mutation, state, error, finding
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
