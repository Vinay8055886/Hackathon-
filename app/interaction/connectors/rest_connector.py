"""REST/API target connector (httpx).

Config keys (Target.config):
  method            HTTP method, default "POST"
  headers           extra headers, default {}
  body_template     optional JSON template; "{messages}" is substituted with
                    the message list. Defaults to an OpenAI-compatible shape:
                    {"messages": [...], "max_tokens": 512}
  timeout_seconds   default 30
  response_path     dotted path into the JSON response to extract the reply
                    text (e.g. "choices.0.message.content"). If unset, the
                    raw JSON body is used.
"""

from __future__ import annotations

import json
import time
from typing import Any

import httpx

from app.interaction.base import ConnectorError, TargetConnector
from app.safety import GuardedResponse, estimate_tokens


class RestConnector(TargetConnector):
    connector_type = "rest"

    async def _perform(self, messages: list[dict[str, str]]) -> GuardedResponse:
        cfg = self.target.config or {}
        url = self.target.endpoint
        method = str(cfg.get("method", "POST")).upper()
        headers = cfg.get("headers") or {}
        timeout = float(cfg.get("timeout_seconds", 30))

        template = cfg.get("body_template")
        if template is not None:
            body: Any = json.loads(json.dumps(template).replace("{messages}", json.dumps(messages)))
        else:
            body = {
                "messages": messages,
                "max_tokens": int(cfg.get("max_tokens", 512)),
            }

        started = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.request(method, url, json=body, headers=headers)
        except httpx.HTTPError as exc:
            raise ConnectorError(f"Target request failed: {exc}") from exc

        duration_ms = int((time.monotonic() - started) * 1000)
        body_text = resp.text
        # Extract the reply text if a response path is configured.
        if cfg.get("response_path") and resp.headers.get("content-type", "").startswith("application/json"):
            try:
                data = resp.json()
                for part in str(cfg["response_path"]).split("."):
                    data = data[int(part)] if part.isdigit() else data[part]
                if isinstance(data, str):
                    body_text = data
                else:
                    body_text = json.dumps(data)
            except (KeyError, IndexError, ValueError, TypeError):
                pass

        return GuardedResponse(
            status_code=resp.status_code,
            body=body_text[: 200_000],  # hard cap on what we persist/analyze
            headers=dict(resp.headers),
            duration_ms=duration_ms,
            tokens=estimate_tokens(body_text),
        )
