"""Attacker agent — selects and sequences candidate payloads.

Selection policy:
  1. payloads whose category/technique historically succeeded (feedback-loop
     priority) go first,
  2. within a priority band, higher risk first,
  3. a payload already attempted (and not refined) in this run is skipped.
"""

from __future__ import annotations

from typing import Any

from app.agents.base import Agent

RISK_RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}


class AttackerAgent(Agent):
    name = "attacker"

    async def select_next(
        self,
        payloads: list[dict[str, Any]],
        attempted_slugs: set[str],
        refined_slugs: set[str],
        resolved_slugs: set[str] | None = None,
    ) -> dict[str, Any] | None:
        resolved = resolved_slugs or set()
        candidates = [
            p
            for p in payloads
            if p["slug"] not in resolved
            and (p["slug"] not in attempted_slugs or p["slug"] in refined_slugs)
        ]
        if not candidates:
            return None
        # Order: feedback priority desc → risk desc → name (deterministic tiebreak)
        candidates.sort(
            key=lambda p: (
                -float(p.get("priority", 1.0)),
                -RISK_RANK.get(p.get("risk", "medium"), 1),
                p.get("slug", ""),
            )
        )
        return candidates[0]
