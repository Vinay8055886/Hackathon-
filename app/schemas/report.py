"""Report and CI policy-gate schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

SEVERITIES = ("low", "medium", "high", "critical")
SEVERITY_RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}


class ReportOut(BaseModel):
    id: str
    run_id: str
    format: str
    storage_path: str
    size_bytes: int
    generated_by: str = "system"
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class CiGateRequest(BaseModel):
    run_id: str | None = Field(default=None, max_length=36)
    findings: list[dict[str, Any]] | None = Field(default=None, max_length=1000)
    severity_threshold: str = "high"
    min_confidence: float = Field(default=0.6, ge=0.0, le=1.0)
    block_categories: list[str] = Field(default_factory=list, max_length=50)
    sarif: bool = True

    @field_validator("severity_threshold")
    @classmethod
    def _severity(cls, v: str) -> str:
        v = v.lower()
        if v not in SEVERITIES:
            raise ValueError(f"severity_threshold must be one of {SEVERITIES}")
        return v


class CiGateResponse(BaseModel):
    passed: bool
    blocking_findings: list[dict[str, Any]]
    total_findings: int
    threshold: str
    message: str
    sarif: dict[str, Any] | None = None
