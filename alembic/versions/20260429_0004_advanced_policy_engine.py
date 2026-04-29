"""advanced policy engine

Revision ID: 20260429_0004
Revises: 20260429_0003
Create Date: 2026-04-29
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260429_0004"
down_revision: Union[str, None] = "20260429_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("action_policies", sa.Column("priority", sa.Integer(), nullable=False, server_default="0"))
    op.add_column(
        "action_policies",
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.add_column("audit_logs", sa.Column("policy_match", sa.JSON(), nullable=True))
    op.add_column("audit_logs", sa.Column("policy_effect", sa.String(), nullable=True))
    op.add_column("audit_logs", sa.Column("matched_policy_id", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("audit_logs", "matched_policy_id")
    op.drop_column("audit_logs", "policy_effect")
    op.drop_column("audit_logs", "policy_match")

    op.drop_column("action_policies", "created_at")
    op.drop_column("action_policies", "priority")
