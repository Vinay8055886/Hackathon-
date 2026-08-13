"""User + auth schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str
    password: str


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
    username: str = Field(min_length=3, max_length=128)
    email: str
    password: str = Field(min_length=8)
    role: str = "viewer"
