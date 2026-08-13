"""WebSocket chat target connector.

Config keys (Target.config):
  receive_timeout_seconds  default 20
  path_prefix              optional: when a server expects a text/JSON envelope
                           like {"type":"chat","message":...}, set to "chat"
  headers                  optional dict of headers for the WS handshake

Sends one message per frame and awaits a reply frame. The connection is
opened per exchange to keep lifetime simple and bounded.
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any

from app.interaction.base import ConnectorError, TargetConnector
from app.safety import GuardedResponse, estimate_tokens


class WebSocketConnector(TargetConnector):
    connector_type = "websocket"

    async def _perform(self, messages: list[dict[str, str]]) -> GuardedResponse:
        try:
            import websockets
        except ImportError as exc:  # pragma: no cover
            raise ConnectorError("The 'websockets' package is required") from exc

        cfg = self.target.config or {}
        receive_timeout = float(cfg.get("receive_timeout_seconds", 20))
        headers = cfg.get("headers") or {}
        path_prefix = cfg.get("path_prefix")

        started = time.monotonic()
        try:
            async with websockets.connect(self.target.endpoint, additional_headers=headers) as ws:
                replies: list[str] = []
                for message in messages:
                    if message.get("role") == "system":
                        continue
                    content = message.get("content", "")
                    if path_prefix:
                        frame = json.dumps({"type": path_prefix, "message": content})
                    else:
                        frame = content
                    await ws.send(frame)
                    try:
                        reply = await asyncio.wait_for(ws.recv(), timeout=receive_timeout)
                    except asyncio.TimeoutError:
                        replies.append("[TIMEOUT: no reply within receive_timeout]")
                        continue
                    if isinstance(reply, bytes):
                        reply = reply.decode("utf-8", errors="replace")
                    replies.append(reply)
                body = "\n".join(replies)
        except Exception as exc:
            raise ConnectorError(f"WebSocket interaction failed: {exc}") from exc

        duration_ms = int((time.monotonic() - started) * 1000)
        return GuardedResponse(
            status_code=200,
            body=body[: 200_000],
            headers={},
            duration_ms=duration_ms,
            tokens=estimate_tokens(body),
        )
