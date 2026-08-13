"""Finding schemas — only redacted evidence is ever exposed."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class FindingOut(BaseModel):
    id: str
    run_id: str
    target_id: str
    title: str
    category: str
    owasp_category: str
    mitre_atlas_id: str
    severity: str
    confidence: float
    redacted_evidence: dict[str, Any] = {}
    remediation_guidance: str = ""
    status: str
    detector: str = ""
    created_at: datetime | None = None

    model_config = {"from_attributes": True}
