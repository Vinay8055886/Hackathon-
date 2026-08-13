"""Model registry — import order matters (FKs resolved at metadata build time)."""

from app.models.base import Base
from app.models.user import Role, User
from app.models.target import Target
from app.models.payload import Payload, PayloadPack
from app.models.run import AgentEvent, Run
from app.models.finding import Finding
from app.models.audit import AuditLogEntry
from app.models.report import Report
from app.models.knowledge import KGEdge, KnowledgeEntry

__all__ = [
    "AgentEvent",
    "AuditLogEntry",
    "Base",
    "Finding",
    "KGEdge",
    "KnowledgeEntry",
    "Payload",
    "PayloadPack",
    "Report",
    "Role",
    "Run",
    "Target",
    "User",
]
