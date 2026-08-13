"""Safety module — the mandatory enforcement layer.

Nothing interacts with a target without passing through InteractionGuard.
"""

from app.safety.allowlist import AllowlistError, assert_target_allowlisted
from app.safety.audit_log import AuditLogger
from app.safety.circuit_breaker import CircuitBreaker, CircuitOpen
from app.safety.guard import GuardedResponse, InteractionGuard, SafetyError
from app.safety.rate_limiter import RateLimiter, RateLimitExceeded
from app.safety.redaction import Redactor, get_redactor
from app.safety.token_budget import TokenBudget, estimate_tokens

__all__ = [
    "AllowlistError",
    "AuditLogger",
    "CircuitBreaker",
    "CircuitOpen",
    "GuardedResponse",
    "InteractionGuard",
    "RateLimiter",
    "RateLimitExceeded",
    "Redactor",
    "SafetyError",
    "TokenBudget",
    "assert_target_allowlisted",
    "estimate_tokens",
    "get_redactor",
]
