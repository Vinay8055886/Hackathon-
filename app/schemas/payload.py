"""Payload pack schemas for the API."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class PayloadMessageIn(BaseModel):
    role: str = "user"
    content: str


class PayloadIn(BaseModel):
    slug: str
    name: str
    description: str = ""
    risk: str = "medium"
    attack_vector: str = "direct"
    owasp_category: str
    mitre_atlas_id: str
    tags: list[str] = []
    messages: list[PayloadMessageIn]
    expected_behaviors: list[str] = []


class PayloadPackUpload(BaseModel):
    name: str
    version: str = "1.0.0"
    description: str = ""
    owasp_categories: list[str] = []
    mitre_atlas_ids: list[str] = []
    tags: list[str] = []
    payloads: list[PayloadIn]


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
