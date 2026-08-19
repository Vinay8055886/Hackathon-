"""add run_origin to runs

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "runs",
        sa.Column(
            "run_origin",
            sa.String(16),
            nullable=False,
            server_default="real",
        ),
    )
    op.create_index("ix_runs_run_origin", "runs", ["run_origin"])


def downgrade() -> None:
    op.drop_index("ix_runs_run_origin", table_name="runs")
    op.drop_column("runs", "run_origin")
