"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _embedding_column():
    """VECTOR(1536) on PostgreSQL (requires pgvector), JSON TEXT elsewhere.

    Keeps the demo/tests (SQLite) and production (Postgres+pgvector) on the
    same migration.
    """
    dialect = op.get_bind().dialect.name
    if dialect == "postgresql":
        try:
            from pgvector.sqlalchemy import Vector

            return sa.Column("embedding", Vector(1536), nullable=False)
        except ImportError:
            op.execute("CREATE EXTENSION IF NOT EXISTS vector")
            from pgvector.sqlalchemy import Vector

            return sa.Column("embedding", Vector(1536), nullable=False)
    return sa.Column("embedding", sa.Text(), nullable=False)


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(64), unique=True, nullable=False),
        sa.Column("description", sa.String(255), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_roles_name", "roles", ["name"])

    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("username", sa.String(128), unique=True, nullable=False),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("hashed_password", sa.String(512), nullable=False),
        sa.Column("role_id", sa.String(36), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_users_username", "users", ["username"])
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_role_id", "users", ["role_id"])

    op.create_table(
        "targets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("connector_type", sa.String(32), nullable=False),
        sa.Column("endpoint", sa.String(1024), nullable=False),
        sa.Column("config", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("allowlisted", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("approved_by", sa.String(128), nullable=True),
        sa.Column("approval_note", sa.Text(), nullable=False, server_default=""),
        sa.Column("owner_id", sa.String(36), nullable=False),
        sa.Column("auth_ref", sa.String(255), nullable=True),
        sa.Column("rate_limit_per_minute", sa.Integer(), nullable=True),
        sa.Column("max_tokens_per_run", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_targets_name", "targets", ["name"])
    op.create_index("ix_targets_allowlisted", "targets", ["allowlisted"])
    op.create_index("ix_targets_owner_id", "targets", ["owner_id"])

    op.create_table(
        "payload_packs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(128), unique=True, nullable=False),
        sa.Column("version", sa.String(32), nullable=False, server_default="1.0.0"),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("owasp_categories", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("mitre_atlas_ids", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("tags", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("source", sa.String(255), nullable=False, server_default="bundled"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_payload_packs_name", "payload_packs", ["name"])

    op.create_table(
        "payloads",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("pack_id", sa.String(36), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("risk", sa.String(16), nullable=False, server_default="medium"),
        sa.Column("attack_vector", sa.String(64), nullable=False, server_default="direct"),
        sa.Column("owasp_category", sa.String(16), nullable=False),
        sa.Column("mitre_atlas_id", sa.String(64), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("messages", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("expected_behaviors", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("priority", sa.Float(), nullable=False, server_default=sa.text("1.0")),
        sa.Column("plugin", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_payloads_pack_id", "payloads", ["pack_id"])
    op.create_index("ix_payloads_owasp_category", "payloads", ["owasp_category"])
    op.create_index("ix_payloads_mitre_atlas_id", "payloads", ["mitre_atlas_id"])

    op.create_table(
        "runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("target_id", sa.String(36), nullable=False),
        sa.Column("payload_pack_ids", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("status", sa.String(32), nullable=False, server_default="scheduled"),
        sa.Column("dry_run", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("started_by", sa.String(36), nullable=False),
        sa.Column("max_turns", sa.Integer(), nullable=False, server_default=sa.text("10")),
        sa.Column("token_budget", sa.Integer(), nullable=False, server_default=sa.text("200000")),
        sa.Column("tokens_used", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("cost_estimate_usd", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("findings_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_runs_target_id", "runs", ["target_id"])
    op.create_index("ix_runs_status", "runs", ["status"])
    op.create_index("ix_runs_dry_run", "runs", ["dry_run"])

    op.create_table(
        "agent_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("run_id", sa.String(36), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("agent", sa.String(32), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_agent_events_run_id", "agent_events", ["run_id"])
    op.create_index("ix_agent_events_agent", "agent_events", ["agent"])
    op.create_index("ix_agent_events_event_type", "agent_events", ["event_type"])

    op.create_table(
        "findings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("run_id", sa.String(36), nullable=False),
        sa.Column("target_id", sa.String(36), nullable=False),
        sa.Column("payload_id", sa.String(36), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("category", sa.String(64), nullable=False),
        sa.Column("owasp_category", sa.String(16), nullable=False),
        sa.Column("mitre_atlas_id", sa.String(64), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default=sa.text("0.5")),
        sa.Column("evidence", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("redacted_evidence", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("transcript_refs", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("remediation_guidance", sa.Text(), nullable=False, server_default=""),
        sa.Column("false_positive", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("status", sa.String(32), nullable=False, server_default="open"),
        sa.Column("detector", sa.String(64), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_findings_run_id", "findings", ["run_id"])
    op.create_index("ix_findings_target_id", "findings", ["target_id"])
    op.create_index("ix_findings_category", "findings", ["category"])
    op.create_index("ix_findings_severity", "findings", ["severity"])
    op.create_index("ix_findings_status", "findings", ["status"])

    op.create_table(
        "audit_log",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("run_id", sa.String(36), nullable=True),
        sa.Column("target_id", sa.String(36), nullable=False),
        sa.Column("actor", sa.String(128), nullable=False, server_default="system"),
        sa.Column("entry_type", sa.String(32), nullable=False),
        sa.Column("request_redacted", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("response_redacted", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("duration_ms", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("tokens", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("outcome", sa.String(32), nullable=False, server_default="ok"),
        sa.Column("redaction_note", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_log_run_id", "audit_log", ["run_id"])
    op.create_index("ix_audit_log_target_id", "audit_log", ["target_id"])
    op.create_index("ix_audit_log_entry_type", "audit_log", ["entry_type"])

    op.create_table(
        "reports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("run_id", sa.String(36), nullable=False),
        sa.Column("format", sa.String(16), nullable=False),
        sa.Column("storage_path", sa.String(1024), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("generated_by", sa.String(128), nullable=False, server_default="system"),
        sa.Column("meta", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_reports_run_id", "reports", ["run_id"])
    op.create_index("ix_reports_format", "reports", ["format"])

    op.create_table(
        "knowledge_entries",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("target_id", sa.String(36), nullable=True),
        sa.Column("run_id", sa.String(36), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        _embedding_column(),
        sa.Column("meta", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_knowledge_entries_kind", "knowledge_entries", ["kind"])
    op.create_index("ix_knowledge_entries_target_id", "knowledge_entries", ["target_id"])
    op.create_index("ix_knowledge_entries_run_id", "knowledge_entries", ["run_id"])

    op.create_table(
        "kg_edges",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("source", sa.String(255), nullable=False),
        sa.Column("relation", sa.String(64), nullable=False),
        sa.Column("target", sa.String(255), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False, server_default=sa.text("1.0")),
        sa.Column("meta", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_kg_edges_source", "kg_edges", ["source"])
    op.create_index("ix_kg_edges_relation", "kg_edges", ["relation"])
    op.create_index("ix_kg_edges_target", "kg_edges", ["target"])


def downgrade() -> None:
    for table in (
        "kg_edges",
        "knowledge_entries",
        "reports",
        "audit_log",
        "findings",
        "agent_events",
        "runs",
        "payloads",
        "payload_packs",
        "targets",
        "users",
        "roles",
    ):
        op.drop_table(table)
