"""Citation-accuracy / hallucination detector (heuristic).

Flags responses that cite URLs or reference numbers that never appeared in the
provided context/messages. A real deployment should pair this with a
groundedness judge (see app/agents/llm.py).
"""

from __future__ import annotations

import re

from app.detection.base import Detection, DetectionContext, Detector, _severity_for

URL_RE = re.compile(r"https?://[^\s)\]]+")
CLAIM_RE = re.compile(r"(?:according to|source|citation|reference)\s*[:#]?\s*(\S+)", re.IGNORECASE)


class HallucinationDetector(Detector):
    name = "hallucination"

    def detect(self, context: DetectionContext) -> list[Detection]:
        text = context.response_text
        provided = "\n".join(m.get("content", "") for m in context.messages)

        cited_urls = set(URL_RE.findall(text))
        provided_urls = set(URL_RE.findall(provided))
        uncited = sorted(cited_urls - provided_urls)

        claims = CLAIM_RE.findall(text)
        unsupported_claims = [c for c in claims if c not in provided]

        if not uncited and not unsupported_claims:
            return []
        confidence = min(0.75, 0.45 + 0.1 * (len(uncited) + len(unsupported_claims)))
        return [
            Detection(
                category="hallucination",
                owasp_category="LLM09",
                mitre_atlas_id="AML.T0051",
                severity=_severity_for("LLM09"),
                confidence=round(confidence, 2),
                title="Unsupported citation or claim in model output",
                evidence={
                    "uncited_urls": uncited,
                    "unsupported_claims": unsupported_claims[:10],
                    "response_snippet": text[:500],
                },
                remediation_guidance=(
                    "Require grounded generation: only cite sources present in the "
                    "retrieval context, and verify citations with a groundedness judge "
                    "before surfacing to users."
                ),
                detector=self.name,
            )
        ]
