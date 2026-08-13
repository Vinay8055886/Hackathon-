"""Connector registry."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.interaction.base import ConnectorError, TargetConnector
from app.interaction.connectors import BrowserConnector, RestConnector, WebSocketConnector

if TYPE_CHECKING:
    from app.models import Target
    from app.safety import InteractionGuard

_REGISTRY: dict[str, type[TargetConnector]] = {
    cls.connector_type: cls
    for cls in (RestConnector, BrowserConnector, WebSocketConnector)
}

CONNECTOR_TYPES = tuple(_REGISTRY)


def build_connector(
    target: "Target",
    guard: "InteractionGuard",
    *,
    run_id: str | None = None,
    actor: str = "system",
) -> TargetConnector:
    cls = _REGISTRY.get(target.connector_type)
    if cls is None:
        raise ConnectorError(
            f"Unknown connector type {target.connector_type!r}. "
            f"Available: {', '.join(CONNECTOR_TYPES)}"
        )
    return cls(target, guard, run_id=run_id, actor=actor)
