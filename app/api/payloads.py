"""Payload pack management routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select

from app.api.deps import SessionDep, require_roles
from app.auth.rbac import ROLE_OPERATOR, ROLE_VIEWER
from app.models import Payload, PayloadPack, User
from app.schemas import PayloadOut, PayloadPackOut, PayloadPackUpload
from app.services.bootstrap import sync_payload_packs

router = APIRouter(prefix="/payload-packs", tags=["payloads"])


@router.get("", response_model=list[PayloadPackOut])
async def list_packs(
    session: SessionDep, user: User = Depends(require_roles(ROLE_VIEWER))
) -> list[PayloadPackOut]:
    stmt = select(PayloadPack).order_by(PayloadPack.name)
    packs = (await session.execute(stmt)).scalars().all()
    counts: dict[str, int] = dict(
        (await session.execute(
            select(Payload.pack_id, func.count(Payload.id)).group_by(Payload.pack_id)
        )).all()
    )
    return [
        PayloadPackOut(
            id=p.id, name=p.name, version=p.version, description=p.description,
            owasp_categories=p.owasp_categories or [],
            mitre_atlas_ids=p.mitre_atlas_ids or [],
            tags=p.tags or [], source=p.source, payload_count=counts.get(p.id, 0),
            created_at=p.created_at,
        )
        for p in packs
    ]


@router.post("", response_model=PayloadPackOut, status_code=201)
async def upsert_pack(
    body: PayloadPackUpload,
    session: SessionDep,
    user: User = Depends(require_roles(ROLE_OPERATOR)),
) -> PayloadPackOut:
    """Upload a new pack (or bump an existing one) from JSON."""
    existing = (
        await session.execute(select(PayloadPack).where(PayloadPack.name == body.name))
    ).scalar_one_or_none()
    if existing is None:
        pack = PayloadPack(
            name=body.name,
            version=body.version,
            description=body.description,
            owasp_categories=list(body.owasp_categories),
            mitre_atlas_ids=list(body.mitre_atlas_ids),
            tags=list(body.tags),
            source="uploaded",
        )
        session.add(pack)
        await session.flush()
    else:
        pack = existing
        pack.version = body.version
        pack.description = body.description

    for p in body.payloads:
        dup = (
            await session.execute(
                select(Payload).where(Payload.pack_id == pack.id, Payload.slug == p.slug)
            )
        ).scalar_one_or_none()
        if dup is None:
            session.add(
                Payload(
                    pack_id=pack.id,
                    slug=p.slug, name=p.name, description=p.description,
                    risk=p.risk, attack_vector=p.attack_vector,
                    owasp_category=p.owasp_category, mitre_atlas_id=p.mitre_atlas_id,
                    tags=list(p.tags),
                    messages=[m.model_dump() for m in p.messages],
                    expected_behaviors=list(p.expected_behaviors),
                )
            )
    await session.commit()
    await session.refresh(pack)
    return PayloadPackOut(
        id=pack.id, name=pack.name, version=pack.version, description=pack.description,
        owasp_categories=pack.owasp_categories, mitre_atlas_ids=pack.mitre_atlas_ids,
        tags=pack.tags, source=pack.source, payload_count=len(body.payloads),
        created_at=pack.created_at,
    )


@router.get("/{pack_id}/payloads", response_model=list[PayloadOut])
async def list_pack_payloads(
    pack_id: str,
    session: SessionDep,
    user: User = Depends(require_roles(ROLE_VIEWER)),
) -> list[PayloadOut]:
    """Individual payloads within a pack (for the pack detail view)."""
    pack = await session.get(PayloadPack, pack_id)
    if pack is None:
        raise HTTPException(status_code=404, detail=f"payload pack {pack_id} not found")
    stmt = select(Payload).where(Payload.pack_id == pack_id).order_by(Payload.priority.desc())
    rows = (await session.execute(stmt)).scalars().all()
    return [PayloadOut.model_validate(p) for p in rows]


@router.post("/sync")
async def sync_bundled(
    session: SessionDep, user: User = Depends(require_roles(ROLE_OPERATOR))
) -> dict:
    packs, payloads = await sync_payload_packs(session)
    await session.commit()
    return {"synced_packs": packs, "synced_payloads": payloads}
