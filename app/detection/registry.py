"""Detector registry and batch runner."""

from __future__ import annotations

from app.detection.base import Detection, DetectionContext, Detector
from app.detection.guardrail_bypass import GuardrailBypassDetector
from app.detection.hallucination import HallucinationDetector
from app.detection.pii import PiiDetector
from app.detection.prompt_leak import PromptLeakDetector
from app.detection.resource_exhaustion import ResourceExhaustionDetector
from app.detection.secrets import SecretsDetector

REGISTRY: list[Detector] = [
    SecretsDetector(),
    PiiDetector(),
    PromptLeakDetector(),
    GuardrailBypassDetector(),
    HallucinationDetector(),
    ResourceExhaustionDetector(),
]

DETECTOR_NAMES = [d.name for d in REGISTRY]


def run_detectors(context: DetectionContext, names: list[str] | None = None) -> list[Detection]:
    detectors = REGISTRY
    if names:
        by_name = {d.name: d for d in REGISTRY}
        detectors = [by_name[n] for n in names if n in by_name]
    detections: list[Detection] = []
    for detector in detectors:
        try:
            detections.extend(detector.detect(context))
        except Exception:  # detectors must never break the loop
            continue
    return detections
