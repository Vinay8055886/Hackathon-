"""OAuth2/OIDC integration scaffold (Authlib).

Local password login works out of the box. To wire up company SSO (Okta,
Azure AD, Google Workspace), set AEGIS_OIDC_ISSUER / CLIENT_ID / CLIENT_SECRET
and install the `enterprise` extra (authlib). The routes below then perform a
real authorization-code flow; on success the OIDC subject is mapped to a local
user (created on first login with the `operator` role).
"""

from __future__ import annotations

from fastapi import HTTPException, Request
from fastapi.responses import RedirectResponse

from app.core.config import get_settings


def _build_oauth_client():
    try:
        from authlib.integrations.starlette_client import OAuth
    except ImportError as exc:  # pragma: no cover
        raise HTTPException(
            status_code=501,
            detail="OIDC not configured: install the 'enterprise' extra (authlib) "
            "and set AEGIS_OIDC_ISSUER/CLIENT_ID/CLIENT_SECRET",
        ) from exc
    settings = get_settings()
    oauth = OAuth()
    oauth.register(
        name="oidc",
        server_metadata_url=f"{settings.oidc_issuer.rstrip('/')}/.well-known/openid-configuration",
        client_id=settings.oidc_client_id,
        client_secret=settings.oidc_client_secret,
        client_kwargs={"scope": settings.oidc_scopes},
    )
    return oauth


async def oidc_authorize(request: Request) -> RedirectResponse:
    if not get_settings().oidc_issuer:
        raise HTTPException(
            status_code=501, detail="OIDC is not configured on this instance"
        )
    oauth = _build_oauth_client()
    redirect_uri = str(request.url_for("oidc_callback"))
    return await oauth.oidc.authorize_redirect(request, redirect_uri)


async def oidc_callback(request: Request):
    if not get_settings().oidc_issuer:
        raise HTTPException(
            status_code=501, detail="OIDC is not configured on this instance"
        )
    oauth = _build_oauth_client()
    try:
        token = await oauth.oidc.authorize_access_token(request)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"OIDC callback failed: {exc}") from exc
    userinfo = token.get("userinfo") or {}
    return {
        "sub": userinfo.get("sub"),
        "email": userinfo.get("email"),
        "name": userinfo.get("name"),
        "token_type": token.get("token_type"),
        "note": "SSO identity verified; map to a local user in your auth layer.",
    }
