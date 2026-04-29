"""approval editing logs

Revision ID: 20260429_0003
Revises: 20260429_0002
Create Date: 2026-04-29
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260429_0003"
down_revision: Union[str, None] = "20260429_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("approvals", sa.Column("agent_id", sa.String(), nullable=True))
    op.add_column("approvals", sa.Column("original_input", sa.JSON(), nullable=True))
    op.add_column("approvals", sa.Column("current_input", sa.JSON(), nullable=True))
    op.add_column("approvals", sa.Column("approved_at", sa.DateTime(), nullable=True))
    op.add_column("approvals", sa.Column("rejected_at", sa.DateTime(), nullable=True))
    op.add_column("approvals", sa.Column("execution_result", sa.JSON(), nullable=True))

    op.add_column("audit_logs", sa.Column("original_input", sa.JSON(), nullable=True))
    op.add_column("audit_logs", sa.Column("final_input", sa.JSON(), nullable=True))
    op.add_column("audit_logs", sa.Column("execution_result", sa.JSON(), nullable=True))
    op.add_column("audit_logs", sa.Column("approved_at", sa.DateTime(), nullable=True))
    op.add_column("audit_logs", sa.Column("rejected_at", sa.DateTime(), nullable=True))

    op.execute(
        """
        UPDATE approvals
        SET
            agent_id = (
                SELECT tool_calls.agent_id
                FROM tool_calls
                WHERE tool_calls.id = approvals.tool_call_id
            ),
            original_input = COALESCE(action_input, (
                SELECT tool_calls.input
                FROM tool_calls
                WHERE tool_calls.id = approvals.tool_call_id
            )),
            current_input = COALESCE(action_input, (
                SELECT tool_calls.input
                FROM tool_calls
                WHERE tool_calls.id = approvals.tool_call_id
            ))
        """
    )
    op.execute("UPDATE audit_logs SET original_input = input, final_input = input")


def downgrade() -> None:
    op.drop_column("audit_logs", "rejected_at")
    op.drop_column("audit_logs", "approved_at")
    op.drop_column("audit_logs", "execution_result")
    op.drop_column("audit_logs", "final_input")
    op.drop_column("audit_logs", "original_input")

    op.drop_column("approvals", "execution_result")
    op.drop_column("approvals", "rejected_at")
    op.drop_column("approvals", "approved_at")
    op.drop_column("approvals", "current_input")
    op.drop_column("approvals", "original_input")
    op.drop_column("approvals", "agent_id")
