"""Payload pack schemas for the API."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PayloadMessageIn(BaseModel):
    role: str = Field(default="user", pattern=r"^(user|assistant|system|developer)$")
    content: str = Field(max_length=50000)


class PayloadIn(BaseModel):
    slug: str = Field(min_length=1, max_length=128, pattern=r"^[a-z0-9_.\-]+$")
    name: str = Field(min_length=1, max_length=255)
    description: str = Field(default="", max_length=2048)
    risk: str = Field(default="medium", pattern=r"^(low|medium|high|critical)$")
    attack_vector: str = Field(default="direct", pattern=r"^(direct|indirect)$")
    owasp_category: str = Field(max_length=16)
    mitre_atlas_id: str = Field(max_length=64)
    tags: list[str] = Field(default_factory=list, max_length=20)
    messages: list[PayloadMessageIn] = Field(min_length=1, max_length=50)
    expected_behaviors: list[str] = Field(default_factory=list, max_length=20)


class PayloadPackUpload(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    version: str = Field(default="1.0.0", max_length=32)
    description: str = Field(default="", max_length=2048)
    owasp_categories: list[str] = Field(default_factory=list, max_length=20)
    mitre_atlas_ids: list[str] = Field(default_factory=list, max_length=20)
    tags: list[str] = Field(default_factory=list, max_length=20)
    payloads: list[PayloadIn] = Field(min_length=1, max_length=500)


class PayloadOut(BaseModel):
    id: str
    pack_id: str
    slug: str
    name: str
    risk: str
    attack_vector: str
    owasp_category: str
    mitre_atlas_id: str
    priority: float
    tags: list[str] = []
    messages: list[dict[str, Any]] = []
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class PayloadPackOut(BaseModel):
    id: str
    name: str
    version: str
    description: str = ""
    owasp_categories: list[str] = []
    mitre_atlas_ids: list[str] = []
    tags: list[str] = []
    source: str = "bundled"
    payload_count: int = 0
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
