"""User + auth schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=1024)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class RoleOut(BaseModel):
    id: str
    name: str
    description: str = ""

    model_config = {"from_attributes": True}


class UserOut(BaseModel):
    id: str
    username: str
    email: str
    role: str
    is_active: bool = True
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=128, pattern=r"^[a-zA-Z0-9_.-]+$")
    email: str = Field(min_length=5, max_length=320)
    password: str = Field(min_length=8, max_length=1024)
    role: str = Field(default="viewer", pattern=r"^(viewer|operator|admin)$")
