"""Security middleware — body size limits, security headers, CORS hardening.

Applied to all routes.  Body size is capped at 1 MB by default to prevent
DoS via oversized payloads.  Security headers follow OWASP recommendations.
"""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add standard security headers to every response."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        # Strict-Transport-Security only when served over HTTPS
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        return response


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject requests with bodies exceeding the configured size limit.

    Only applies to methods that typically carry a body (POST, PUT, PATCH).
    """

    def __init__(self, app, max_body_bytes: int = 1_048_576) -> None:  # 1 MB
        super().__init__(app)
        self._max_body_bytes = max_body_bytes

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.method in ("POST", "PUT", "PATCH"):
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > self._max_body_bytes:
                return JSONResponse(
                    status_code=413,
                    content={
                        "detail": f"Request body too large (max {self._max_body_bytes} bytes)"
                    },
                )
            # Also check the actual body for streaming requests
            try:
                body = await request.body()
                if len(body) > self._max_body_bytes:
                    return JSONResponse(
                        status_code=413,
                        content={
                            "detail": f"Request body too large (max {self._max_body_bytes} bytes)"
                        },
                    )
            except Exception:
                pass
        return await call_next(request)
