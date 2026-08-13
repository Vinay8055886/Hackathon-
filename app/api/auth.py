"""Auth routes: password login, user management, OIDC, /me."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select

from app.api.deps import CurrentUser, SessionDep, require_roles
from app.auth.oidc import oidc_authorize, oidc_callback as _oidc_callback
from app.auth.rbac import ROLE_ADMIN, ROLE_OPERATOR, ROLE_VIEWER
from app.auth.security import create_access_token, hash_password, verify_password
from app.core.config import get_settings
from app.models import Role, User
from app.schemas import LoginRequest, TokenResponse, UserCreate, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, session: SessionDep) -> TokenResponse:
    user = (
        await session.execute(select(User).where(User.username == body.username))
    ).scalar_one_or_none()
    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")
    from datetime import datetime, timezone

    user.last_login_at = datetime.now(timezone.utc)
    await session.commit()
    settings = get_settings()
    token = create_access_token(user.id, user.role_name)
    return TokenResponse(
        access_token=token,
        expires_in=settings.jwt_expires_minutes * 60,
    )


@router.get("/me", response_model=UserOut)
async def me(user: CurrentUser) -> UserOut:
    return UserOut(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role_name,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.post("/users", response_model=UserOut, status_code=201)
async def create_user(
    body: UserCreate, session: SessionDep, admin: User = Depends(require_roles(ROLE_ADMIN))
) -> UserOut:
    if body.role not in {ROLE_VIEWER, ROLE_OPERATOR, ROLE_ADMIN}:
        raise HTTPException(status_code=400, detail=f"role must be one of viewer/operator/admin")
    dup = (
        await session.execute(
            select(User).where(
                (User.username == body.username) | (User.email == body.email)
            )
        )
    ).scalar_one_or_none()
    if dup is not None:
        raise HTTPException(status_code=409, detail="username or email already exists")
    role = (await session.execute(select(Role).where(Role.name == body.role))).scalar_one_or_none()
    user = User(
        username=body.username,
        email=body.email,
        hashed_password=hash_password(body.password),
        role_id=role.id if role else None,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return UserOut(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role_name,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.get("/oidc/login")
async def oidc_login(request: Request):
    return await oidc_authorize(request)


@router.get("/oidc/callback", name="oidc_callback")
async def oidc_callback_route(request: Request):
    return await _oidc_callback(request)
