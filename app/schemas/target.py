"""Target registration schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.interaction import CONNECTOR_TYPES


class TargetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str = ""
    connector_type: str
    endpoint: str
    config: dict[str, Any] = Field(default_factory=dict)
    auth_ref: str | None = None
    rate_limit_per_minute: int | None = None
    max_tokens_per_run: int | None = None

    @field_validator("connector_type")
    @classmethod
    def _connector(cls, v: str) -> str:
        if v not in CONNECTOR_TYPES:
            raise ValueError(f"connector_type must be one of {CONNECTOR_TYPES}")
        return v

    @field_validator("endpoint")
    @classmethod
    def _endpoint(cls, v: str) -> str:
        if not v.startswith(("http://", "https://", "ws://", "wss://")):
            raise ValueError("endpoint must be an absolute http(s)/ws(s) URL")
        return v


class AllowlistRequest(BaseModel):
    allowlisted: bool = True
    approved_by: str = Field(min_length=1)
    approval_note: str = ""


class TargetOut(BaseModel):
    id: str
    name: str
    description: str = ""
    connector_type: str
    endpoint: str
    config: dict[str, Any] = Field(default_factory=dict)
    allowlisted: bool
    approved_by: str | None = None
    approval_note: str = ""
    owner_id: str
    auth_ref: str | None = None
    rate_limit_per_minute: int | None = None
    max_tokens_per_run: int | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
