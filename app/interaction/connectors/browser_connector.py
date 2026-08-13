"""Browser chat-UI target connector (Playwright).

Config keys (Target.config):
  url               page to open (defaults to target.endpoint)
  input_selector    text input, default "textarea, input[type=text]"
  send_selector     send button, default "[data-testid*=send], button[type=submit], .send-button"
  response_selector element holding the latest assistant reply, default ".assistant, .message, [class*=response]"
  timeout_seconds   default 30

Playwright browsers must be installed (`playwright install chromium`). The
import is lazy so the rest of the platform runs without Playwright installed.
"""

from __future__ import annotations

import time
from typing import Any

from app.interaction.base import ConnectorError, TargetConnector
from app.safety import GuardedResponse, estimate_tokens


class BrowserConnector(TargetConnector):
    connector_type = "browser"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._playwright = None
        self._browser = None
        self._page = None

    async def _ensure_browser(self):
        if self._browser is not None:
            return
        try:
            from playwright.async_api import async_playwright
        except ImportError as exc:  # pragma: no cover - env-dependent
            raise ConnectorError(
                "Playwright is not installed. Run: pip install playwright && playwright install chromium"
            ) from exc
        self._playwright = await async_playwright().start()
        try:
            self._browser = await self._playwright.chromium.launch(headless=True)
        except Exception as exc:  # pragma: no cover - env-dependent
            await self._playwright.stop()
            raise ConnectorError(
                "Could not launch Chromium. Run: playwright install chromium"
            ) from exc
        self._page = await self._browser.new_page()

    async def _perform(self, messages: list[dict[str, str]]) -> GuardedResponse:
        cfg = self.target.config or {}
        url = cfg.get("url") or self.target.endpoint
        input_sel = cfg.get("input_selector", "textarea, input[type=text]")
        send_sel = cfg.get(
            "send_selector",
            "[data-testid*=send], button[type=submit], .send-button, button",
        )
        response_sel = cfg.get(
            "response_selector", ".assistant, .message, [class*=response]"
        )
        timeout = float(cfg.get("timeout_seconds", 30)) * 1000

        await self._ensure_browser()
        assert self._page is not None

        started = time.monotonic()
        try:
            await self._page.goto(url, wait_until="domcontentloaded", timeout=timeout)
            for message in messages:
                if message.get("role") == "system":
                    continue  # system prompts can't be injected via chat UI
                await self._page.fill(input_sel, message.get("content", ""))
                await self._page.click(send_sel)
                await self._page.wait_for_selector(
                    response_sel, state="visible", timeout=timeout
                )
            # Give the UI a beat to finish streaming, then read the last reply.
            await self._page.wait_for_timeout(1500)
            elements = await self._page.query_selector_all(response_sel)
            if not elements:
                raise ConnectorError("No response element matched the configured selector")
            last = elements[-1]
            body = (await last.inner_text()) or ""
        except Exception as exc:
            if isinstance(exc, ConnectorError):
                raise
            raise ConnectorError(f"Browser interaction failed: {exc}") from exc

        duration_ms = int((time.monotonic() - started) * 1000)
        return GuardedResponse(
            status_code=200,
            body=body[: 200_000],
            headers={},
            duration_ms=duration_ms,
            tokens=estimate_tokens(body),
        )

    async def close(self) -> None:
        await super().close()
        for closer, attr in (
            (getattr(self, "_browser", None) and self._browser.close, "_browser"),
            (getattr(self, "_playwright", None) and self._playwright.stop, "_playwright"),
        ):
            try:
                if closer:
                    await closer()
            except Exception:
                pass
            setattr(self, attr, None)
