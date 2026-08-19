"""Run schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class RunCreate(BaseModel):
    target_id: str = Field(min_length=1, max_length=36)
    payload_pack_ids: list[str] = Field(min_length=1, max_length=20)
    dry_run: bool | None = None  # None → server default (AEGIS_DRY_RUN_DEFAULT)
    run_origin: str = Field(default="real", pattern=r"^(real|demo|test)$")
    max_turns: int | None = Field(default=None, ge=1, le=200)
    token_budget: int | None = Field(default=None, ge=1, le=10_000_000)

    @field_validator("payload_pack_ids")
    @classmethod
    def _packs(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("at least one payload pack is required")
        return v


class RunOut(BaseModel):
    id: str
    target_id: str
    payload_pack_ids: list[str] = []
    status: str
    dry_run: bool
    run_origin: str = "real"  # real | demo | test
    started_by: str
    max_turns: int
    token_budget: int
    tokens_used: int = 0
    cost_estimate_usd: float = 0.0
    findings_count: int = 0
    error: str | None = None
    created_at: datetime | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None

    model_config = {"from_attributes": True}


class RunEventOut(BaseModel):
    sequence: int
    run_id: str
    agent: str
    event_type: str
    payload: dict[str, Any]
