"""Dry-run connector.

In dry-run mode the full pipeline (allow-list, budgets, attacker→judge→refiner
loop, audit logging) executes, but NO request ever reaches the real target.
The connector returns a deterministic simulated response so operators can
validate configuration and preview behaviour safely.
"""

from __future__ import annotations

from app.interaction.base import TargetConnector
from app.safety import GuardedResponse, estimate_tokens

DRY_RUN_BODY = (
    "[DRY-RUN] This is a simulated target response. No request was sent to the "
    "real target. The pipeline (payload selection, budgets, judge loop) ran "
    "normally."
)


class DryRunConnector(TargetConnector):
    connector_type = "dry_run"

    async def _perform(self, messages: list[dict[str, str]]) -> GuardedResponse:
        body = DRY_RUN_BODY
        return GuardedResponse(
            status_code=200,
            body=body,
            headers={"x-aegis-dry-run": "true"},
            duration_ms=0,
            tokens=estimate_tokens(body),
        )
