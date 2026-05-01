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
    bind = op.get_bind()
    existing_action_policy_columns = {
        column["name"] for column in sa.inspect(bind).get_columns("action_policies")
    }
    existing_audit_log_columns = {
        column["name"] for column in sa.inspect(bind).get_columns("audit_logs")
    }

    if "priority" not in existing_action_policy_columns:
        op.add_column("action_policies", sa.Column("priority", sa.Integer(), nullable=False, server_default="0"))

    if "created_at" not in existing_action_policy_columns:
        if bind.dialect.name == "sqlite":
            op.add_column("action_policies", sa.Column("created_at", sa.DateTime(), nullable=True))
            op.execute("UPDATE action_policies SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL")
        else:
            op.add_column(
                "action_policies",
                sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            )

    if "policy_match" not in existing_audit_log_columns:
        op.add_column("audit_logs", sa.Column("policy_match", sa.JSON(), nullable=True))
    if "policy_effect" not in existing_audit_log_columns:
        op.add_column("audit_logs", sa.Column("policy_effect", sa.String(), nullable=True))
    if "matched_policy_id" not in existing_audit_log_columns:
        op.add_column("audit_logs", sa.Column("matched_policy_id", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("audit_logs", "matched_policy_id")
    op.drop_column("audit_logs", "policy_effect")
    op.drop_column("audit_logs", "policy_match")

    op.drop_column("action_policies", "created_at")
    op.drop_column("action_policies", "priority")
