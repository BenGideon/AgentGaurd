"""gmail connectors

Revision ID: 20260429_0002
Revises: 20260429_0001
Create Date: 2026-04-29
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260429_0002"
down_revision: Union[str, None] = "20260429_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "connectors",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("workspace_id", sa.String(), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("access_token", sa.Text(), nullable=False),
        sa.Column("refresh_token", sa.Text(), nullable=True),
        sa.Column("scopes", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("connected_email", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workspace_id", "provider", name="uq_connectors_workspace_provider"),
    )
    op.create_index(op.f("ix_connectors_id"), "connectors", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_connectors_id"), table_name="connectors")
    op.drop_table("connectors")
