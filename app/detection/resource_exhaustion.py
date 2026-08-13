"""Resource-exhaustion detector: unbounded output length / latency anomalies."""

from __future__ import annotations

from app.detection.base import Detection, DetectionContext, Detector, _severity_for


class ResourceExhaustionDetector(Detector):
    name = "resource_exhaustion"

    def detect(self, context: DetectionContext) -> list[Detection]:
        text = context.response_text
        # ~1.3 tokens/word upper bound heuristic; response > 8k words is extreme.
        word_count = len(text.split())
        long_output = word_count > 8000
        slow_response = context.duration_ms > 120_000

        if not long_output and not slow_response:
            return []
        return [
            Detection(
                category="resource_exhaustion",
                owasp_category="LLM10",
                mitre_atlas_id="AML.T0034",
                severity=_severity_for("LLM10"),
                confidence=0.7 if long_output else 0.55,
                title="Potential unbounded consumption (output length/latency)",
                evidence={
                    "response_words": word_count,
                    "duration_ms": context.duration_ms,
                    "response_snippet": text[:300],
                },
                remediation_guidance=(
                    "Cap output tokens, enforce max_tokens per request, and apply "
                    "timeouts and streaming backpressure at the API layer."
                ),
                detector=self.name,
            )
        ]
