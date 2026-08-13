"""Token budgets.

A rough, dependency-free token estimator (≈4 chars/token) keeps budgets
enforceable even without a tokenizer. Budgets are enforced at the interaction
boundary before any request is sent.
"""

from __future__ import annotations

from dataclasses import dataclass


def estimate_tokens(text: str) -> int:
    """≈4 characters per token; stable and cheap."""
    if not text:
        return 0
    return max(1, len(text) // 4)


@dataclass
class TokenBudget:
    limit: int
    used: int = 0

    @property
    def remaining(self) -> int:
        return max(0, self.limit - self.used)

    @property
    def exhausted(self) -> bool:
        return self.used >= self.limit

    def consume(self, tokens: int) -> bool:
        """Consume tokens; returns False (and consumes nothing) if over budget."""
        if tokens > self.remaining:
            return False
        self.used += tokens
        return True


class BudgetExceeded(Exception):
    pass
