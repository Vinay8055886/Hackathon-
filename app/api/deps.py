"""FastAPI dependencies: session, current user, RBAC."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.rbac import ensure_role
from app.auth.security import decode_token
from app.core.db import get_session
from app.models import User

SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_current_user(
    request: Request, session: SessionDep
) -> User:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = auth.removeprefix("Bearer ").strip()
    try:
        claims = decode_token(token)
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    user = await session.get(User, claims.get("sub"))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(required: str):
    """Dependency factory: require a minimum role on a route."""

    async def _dep(user: CurrentUser) -> User:
        ensure_role(user.role_name, required)
        return user

    return _dep


def not_found(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
