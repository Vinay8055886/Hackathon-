"""Detector interface and shared types."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Detection:
    category: str  # e.g. "pii_leak", "system_prompt_leak"
    owasp_category: str
    mitre_atlas_id: str
    severity: str  # low|medium|high|critical
    confidence: float  # 0..1
    title: str
    evidence: dict[str, Any] = field(default_factory=dict)
    remediation_guidance: str = ""
    detector: str = ""


@dataclass
class DetectionContext:
    """Everything a detector may need about a single turn."""

    payload: dict[str, Any]
    messages: list[dict[str, str]]
    response_text: str
    status_code: int = 200
    duration_ms: int = 0
    target: dict[str, Any] | None = None
    history: list[dict[str, Any]] = field(default_factory=list)


class Detector(ABC):
    name: str = "base"

    @abstractmethod
    def detect(self, context: DetectionContext) -> list[Detection]:
        """Return zero or more detections for this turn."""


def _severity_for(owasp: str) -> str:
    return {
        "LLM01": "high",
        "LLM02": "high",
        "LLM06": "high",
        "LLM07": "medium",
        "LLM10": "medium",
    }.get(owasp, "medium")
