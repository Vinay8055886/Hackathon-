"""Async SQLAlchemy engine, session factory, and declarative base.

Uses aiosqlite for tests/demo and asyncpg for PostgreSQL production. The
engine is created lazily so that importing the app never requires a live DB.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

_engine = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


class Base(DeclarativeBase):
    pass


def get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        engine_kwargs: dict[str, Any] = {"echo": False, "pool_pre_ping": True}
        if settings.database_url.startswith("sqlite"):
            engine_kwargs["connect_args"] = {"check_same_thread": False}
        _engine = create_async_engine(settings.database_url, **engine_kwargs)
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_engine(), class_=AsyncSession, expire_on_commit=False
        )
    return _session_factory


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding a scoped session."""
    async with get_session_factory()() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def init_db(create_all: bool = True) -> None:
    """Create tables (used by CLI/demo). Alembic is the canonical path."""
    from app import models  # noqa: F401  (register all models on Base)

    if create_all:
        async with get_engine().begin() as conn:
            await conn.run_sync(Base.metadata.create_all)


async def reset_db() -> None:
    """Drop and recreate all tables (dev/demo only)."""
    from app import models  # noqa: F401

    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
