"""Automatic redaction of secrets/PII.

Applied to every request/response pair BEFORE it is persisted to audit_log or
streamed to a client. Never disable redaction in a code path that touches
storage or the wire — if you think you need raw data, you need a different
path, not a redaction bypass.
"""

from __future__ import annotations

import re
from typing import Any

# Ordered so more specific patterns win.
PATTERNS: list[tuple[str, str]] = [
    ("openai_api_key", r"\bsk-[A-Za-z0-9_\-]{16,}\b"),
    ("anthropic_api_key", r"\bsk-ant-[A-Za-z0-9_\-]{16,}\b"),
    ("aws_access_key", r"\bAKIA[0-9A-Z]{16}\b"),
    ("aws_secret_key", r"(?i)\baws.{0,20}(secret|access)[^\n]{0,60}\b"),
    ("google_api_key", r"\bAIza[0-9A-Za-z_\-]{35}\b"),
    ("github_token", r"\bgh[pousr]_[0-9A-Za-z]{30,}\b"),
    ("jwt", r"\beyJ[A-Za-z0-9_\-]{10,}\.eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\b"),
    ("private_key", r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"),
    ("bearer_token", r"(?i)\bBearer\s+[A-Za-z0-9._~+/\-=]{16,}\b"),
    ("generic_token", r"(?i)\b(?:token|secret|password|passwd|apikey|api_key)\s*[:=]\s*['\"]?[^\s'\"&,;]{8,}"),
    ("email", r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"),
    ("phone", r"(?:\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b|\b\d{3}[-.\s]\d{4}\b)"),
    ("ssn", r"\b\d{3}-\d{2}-\d{4}\b"),
    ("credit_card", r"\b(?:\d[ -]?){13,16}\b"),
    ("ip_address", r"\b(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(?:\.(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}\b"),
]

# JSON keys whose values are always redacted regardless of content.
SENSITIVE_KEYS = frozenset(
    {
        "authorization",
        "cookie",
        "x-api-key",
        "api_key",
        "apikey",
        "password",
        "passwd",
        "secret",
        "token",
        "access_token",
        "refresh_token",
        "client_secret",
        "private_key",
    }
)


class Redactor:
    """Deterministic redactor. Redacts secrets and PII to placeholders."""

    def __init__(self) -> None:
        self._compiled: list[tuple[str, re.Pattern]] = [
            (name, re.compile(pattern, re.IGNORECASE)) for name, pattern in PATTERNS
        ]

    def redact_text(self, text: str) -> tuple[str, int]:
        count = 0
        for name, pattern in self._compiled:
            def _repl(match: re.Match) -> str:
                nonlocal count
                count += 1
                return f"[REDACTED:{name}]"

            text = pattern.sub(_repl, text)
        return text, count

    def redact_json(self, obj: Any, _path: str = "") -> tuple[Any, int]:
        count = 0
        if isinstance(obj, dict):
            out: dict[str, Any] = {}
            for key, value in obj.items():
                if str(key).lower() in SENSITIVE_KEYS:
                    out[str(key)] = "[REDACTED:key]"
                    count += 1
                else:
                    redacted, n = self.redact_json(value, f"{_path}.{key}")
                    out[str(key)] = redacted
                    count += n
            return out, count
        if isinstance(obj, list):
            out_list: list[Any] = []
            for item in obj:
                redacted, n = self.redact_json(item, _path)
                out_list.append(redacted)
                count += n
            return out_list, count
        if isinstance(obj, str):
            redacted, n = self.redact_text(obj)
            return redacted, count + n
        return obj, count

    def redact(self, obj: Any) -> Any:
        """Redact in place of a copy — returns the redacted copy."""
        redacted, _ = self.redact_json(obj)
        return redacted


_default = Redactor()


def get_redactor() -> Redactor:
    return _default
