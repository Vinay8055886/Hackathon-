"""Bootstrap: roles, default admin user, bundled payload packs."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import hash_password
from app.core.config import get_settings
from app.models import Payload, PayloadPack, Role, User
from app.payloads import load_all_packs


async def ensure_roles(session: AsyncSession) -> dict[str, str]:
    """Create the three RBAC roles; returns {role_name: role_id}."""
    names = [
        ("admin", "Full platform administration"),
        ("operator", "Register/allow-list targets and launch runs"),
        ("viewer", "Read-only: targets, runs, findings, reports"),
    ]
    ids: dict[str, str] = {}
    for name, desc in names:
        role = (await session.execute(select(Role).where(Role.name == name))).scalar_one_or_none()
        if role is None:
            role = Role(name=name, description=desc)
            session.add(role)
            await session.flush()
        ids[name] = role.id
    return ids


async def ensure_admin_user(session: AsyncSession, role_ids: dict[str, str]) -> None:
    settings = get_settings()
    existing = (
        await session.execute(
            select(User).where(User.username == settings.admin_username)
        )
    ).scalar_one_or_none()
    if existing is not None:
        return
    session.add(
        User(
            username=settings.admin_username,
            email=f"{settings.admin_username}@local.invalid",
            hashed_password=hash_password(settings.admin_password),
            role_id=role_ids["admin"],
        )
    )


async def sync_payload_packs(session: AsyncSession) -> tuple[int, int]:
    """Upsert bundled payload packs into the DB. Returns (packs, payloads) counts."""
    packs_loaded = 0
    payloads_loaded = 0
    for pack_def in load_all_packs():
        existing = (
            await session.execute(
                select(PayloadPack).where(PayloadPack.name == pack_def.name)
            )
        ).scalar_one_or_none()
        if existing is None:
            existing = PayloadPack(
                name=pack_def.name,
                version=pack_def.version,
                description=pack_def.description,
                owasp_categories=list(pack_def.owasp_categories),
                mitre_atlas_ids=list(pack_def.mitre_atlas_ids),
                tags=list(pack_def.tags),
                source="bundled",
            )
            session.add(existing)
            await session.flush()
            packs_loaded += 1
        for p in pack_def.payloads:
            dup = (
                await session.execute(
                    select(Payload).where(
                        Payload.pack_id == existing.id, Payload.slug == p.slug
                    )
                )
            ).scalar_one_or_none()
            if dup is not None:
                continue
            session.add(
                Payload(
                    pack_id=existing.id,
                    slug=p.slug,
                    name=p.name,
                    description=p.description,
                    risk=p.risk,
                    attack_vector=p.attack_vector,
                    owasp_category=p.owasp_category,
                    mitre_atlas_id=p.mitre_atlas_id,
                    tags=list(p.tags),
                    messages=[m.model_dump() for m in p.messages],
                    expected_behaviors=list(p.expected_behaviors),
                    plugin=p.plugin,
                )
            )
            payloads_loaded += 1
    await session.flush()
    return packs_loaded, payloads_loaded


async def bootstrap(session: AsyncSession) -> None:
    role_ids = await ensure_roles(session)
    await ensure_admin_user(session, role_ids)
    await sync_payload_packs(session)
    await session.commit()
