"""Shared agent types."""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from typing import Any


class Agent(ABC):
    """Base class for swarm agents. Concrete agents implement ``name`` and
    their specific run methods (kept role-specific rather than a single
    generic interface so each role's contract stays explicit)."""

    name: str = "agent"


@dataclass
class JudgeVerdict:
    success: bool
    detections: list[dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.0
    severity: str = "none"
    summary: str = ""


@dataclass
class TurnRecord:
    """One attacker→target→judge cycle."""

    payload: dict[str, Any]
    messages: list[dict[str, str]]
    response_text: str
    status_code: int = 200
    duration_ms: int = 0
    tokens: int = 0
    audit_ref: str | None = None
    verdict: JudgeVerdict | None = None
    mutation_strategy: str | None = None


SEVERITY_RANK = {"none": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
