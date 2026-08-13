"""Role-based access control.

Roles: admin (everything), operator (manage targets + launch runs),
viewer (read-only). Enforcement happens in FastAPI dependencies (see
app/api/deps.py) AND at the interaction boundary (the guard receives the
acting user id).
"""

from __future__ import annotations

ROLE_ADMIN = "admin"
ROLE_OPERATOR = "operator"
ROLE_VIEWER = "viewer"

ROLE_RANK = {ROLE_VIEWER: 0, ROLE_OPERATOR: 1, ROLE_ADMIN: 2}

ALL_ROLES = (ROLE_VIEWER, ROLE_OPERATOR, ROLE_ADMIN)


class PermissionDenied(Exception):
    def __init__(self, required: str, actual: str) -> None:
        super().__init__(f"Requires role {required!r}, user has {actual!r}")
        self.required = required
        self.actual = actual


def has_role(actual: str, required: str) -> bool:
    return ROLE_RANK.get(actual, -1) >= ROLE_RANK.get(required, 0)


def ensure_role(actual: str, required: str) -> None:
    """Raise PermissionDenied unless the user's role clears the requirement."""
    if not has_role(actual, required):
        raise PermissionDenied(required, actual)


# Action → minimum role
ACTION_ROLES = {
    "create_target": ROLE_OPERATOR,
    "allowlist_target": ROLE_OPERATOR,
    "launch_run": ROLE_OPERATOR,
    "view_targets": ROLE_VIEWER,
    "view_runs": ROLE_VIEWER,
    "view_findings": ROLE_VIEWER,
    "generate_report": ROLE_VIEWER,
    "admin": ROLE_ADMIN,
}
