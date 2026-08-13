"""Payload pack schema (Pydantic v2)."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class PayloadMessage(BaseModel):
    role: str = "user"
    content: str

    @field_validator("role")
    @classmethod
    def _role(cls, v: str) -> str:
        if v not in {"system", "user", "assistant"}:
            raise ValueError("role must be system|user|assistant")
        return v


class PayloadDef(BaseModel):
    slug: str
    name: str
    description: str = ""
    risk: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    attack_vector: str = Field(
        default="direct", pattern="^(direct|indirect|multi_turn)$"
    )
    owasp_category: str
    mitre_atlas_id: str
    tags: list[str] = []
    messages: list[PayloadMessage]
    expected_behaviors: list[str] = []
    plugin: str | None = None

    @field_validator("owasp_category")
    @classmethod
    def _owasp(cls, v: str) -> str:
        if not v.upper().startswith("LLM"):
            raise ValueError("owasp_category must be an OWASP LLM Top 10 id like LLM01")
        return v.upper()


class PayloadPackDef(BaseModel):
    name: str
    version: str = "1.0.0"
    description: str = ""
    owasp_categories: list[str] = []
    mitre_atlas_ids: list[str] = []
    tags: list[str] = []
    payloads: list[PayloadDef]
