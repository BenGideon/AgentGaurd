"""make tool names workspace scoped

Revision ID: 20260429_0005
Revises: 20260429_0004
Create Date: 2026-04-29
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260429_0005"
down_revision: Union[str, None] = "20260429_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _recreate_tools_sqlite(primary_key_columns: list[str], unique_workspace_name: bool) -> None:
    constraints = [
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.PrimaryKeyConstraint(*primary_key_columns),
    ]
    if unique_workspace_name:
        constraints.append(sa.UniqueConstraint("workspace_id", "name", name="uq_tools_workspace_name"))

    op.create_table(
        "tools_new",
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("workspace_id", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("input_schema", sa.JSON(), nullable=True),
        *constraints,
    )
    op.execute(
        """
        INSERT INTO tools_new (name, workspace_id, description, input_schema)
        SELECT name, workspace_id, description, input_schema
        FROM tools
        """
    )
    op.drop_index(op.f("ix_tools_name"), table_name="tools")
    op.drop_table("tools")
    op.rename_table("tools_new", "tools")
    op.create_index(op.f("ix_tools_name"), "tools", ["name"], unique=False)


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        _recreate_tools_sqlite(["workspace_id", "name"], unique_workspace_name=True)
        return

    op.drop_constraint("tools_pkey", "tools", type_="primary")
    op.create_primary_key("pk_tools", "tools", ["workspace_id", "name"])
    op.create_unique_constraint("uq_tools_workspace_name", "tools", ["workspace_id", "name"])


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        _recreate_tools_sqlite(["name"], unique_workspace_name=False)
        return

    op.drop_constraint("uq_tools_workspace_name", "tools", type_="unique")
    op.drop_constraint("pk_tools", "tools", type_="primary")
    op.create_primary_key("tools_pkey", "tools", ["name"])
