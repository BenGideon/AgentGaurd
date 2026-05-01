"""alerts config

Revision ID: 20260429_0006
Revises: 20260429_0005
Create Date: 2026-04-29
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260429_0006"
down_revision: Union[str, None] = "20260429_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "alerts_config",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("workspace_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("events", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_alerts_config_id"), "alerts_config", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_alerts_config_id"), table_name="alerts_config")
    op.drop_table("alerts_config")
