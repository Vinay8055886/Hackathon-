"""Audit logging.

Every outbound request and inbound response passes through here. Redaction
runs BEFORE persistence — the stored record is guaranteed free of the
sensitive-data classes the Redactor knows about.
"""

from __future__ import annotations

import time
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLogEntry
from app.safety.redaction import get_redactor


class AuditLogger:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._redactor = get_redactor()

    async def log(
        self,
        *,
        target_id: str,
        run_id: str | None,
        actor: str,
        entry_type: str,
        request: dict[str, Any] | None = None,
        response: dict[str, Any] | None = None,
        duration_ms: int = 0,
        tokens: int = 0,
        outcome: str = "ok",
    ) -> AuditLogEntry:
        redacted_request, req_count = self._redactor.redact_json(request or {})
        redacted_response, res_count = self._redactor.redact_json(response or {})
        note_parts = []
        if req_count:
            note_parts.append(f"{req_count} sensitive value(s) redacted from request")
        if res_count:
            note_parts.append(f"{res_count} sensitive value(s) redacted from response")
        entry = AuditLogEntry(
            run_id=run_id,
            target_id=target_id,
            actor=actor,
            entry_type=entry_type,
            request_redacted=redacted_request,
            response_redacted=redacted_response,
            duration_ms=duration_ms,
            tokens=tokens,
            outcome=outcome,
            redaction_note="; ".join(note_parts),
        )
        self._session.add(entry)
        await self._session.flush()
        return entry
