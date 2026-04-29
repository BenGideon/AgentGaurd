"""initial schema

Revision ID: 20260429_0001
Revises:
Create Date: 2026-04-29
"""
from typing import Sequence, Union
from datetime import datetime

from alembic import op
import sqlalchemy as sa


revision: str = "20260429_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "workspaces",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_workspaces_id"), "workspaces", ["id"], unique=False)

    op.create_table(
        "users",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)

    op.create_table(
        "actions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("workspace_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("input_schema", sa.JSON(), nullable=True),
        sa.Column("executor_type", sa.String(), nullable=False),
        sa.Column("risk_level", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_actions_id"), "actions", ["id"], unique=False)
    op.create_index(op.f("ix_actions_name"), "actions", ["name"], unique=False)

    op.create_table(
        "agents",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("workspace_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("api_key", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_agents_api_key"), "agents", ["api_key"], unique=True)
    op.create_index(op.f("ix_agents_id"), "agents", ["id"], unique=False)

    op.create_table(
        "tools",
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("workspace_id", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("input_schema", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.PrimaryKeyConstraint("name"),
    )
    op.create_index(op.f("ix_tools_name"), "tools", ["name"], unique=False)

    op.create_table(
        "workspace_memberships",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("workspace_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_workspace_memberships_id"), "workspace_memberships", ["id"], unique=False)

    op.create_table(
        "action_policies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("workspace_id", sa.String(), nullable=False),
        sa.Column("agent_id", sa.String(), nullable=False),
        sa.Column("action_name", sa.String(), nullable=False),
        sa.Column("effect", sa.String(), nullable=False),
        sa.Column("conditions", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"]),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_action_policies_id"), "action_policies", ["id"], unique=False)

    op.create_table(
        "action_secret_policies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("workspace_id", sa.String(), nullable=False),
        sa.Column("agent_id", sa.String(), nullable=False),
        sa.Column("action_name", sa.String(), nullable=False),
        sa.Column("allowed_secrets", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"]),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_action_secret_policies_id"), "action_secret_policies", ["id"], unique=False)

    op.create_table(
        "policies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("workspace_id", sa.String(), nullable=False),
        sa.Column("agent_id", sa.String(), nullable=False),
        sa.Column("allowed_tools", sa.JSON(), nullable=False),
        sa.Column("approval_required_tools", sa.JSON(), nullable=False),
        sa.Column("blocked_tools", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"]),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("agent_id"),
    )
    op.create_index(op.f("ix_policies_id"), "policies", ["id"], unique=False)

    op.create_table(
        "secrets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("workspace_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("value", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_secrets_id"), "secrets", ["id"], unique=False)
    op.create_index(op.f("ix_secrets_name"), "secrets", ["name"], unique=False)

    op.create_table(
        "tool_calls",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("workspace_id", sa.String(), nullable=False),
        sa.Column("agent_id", sa.String(), nullable=False),
        sa.Column("tool", sa.String(), nullable=False),
        sa.Column("input", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"]),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tool_calls_id"), "tool_calls", ["id"], unique=False)

    op.create_table(
        "approvals",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("workspace_id", sa.String(), nullable=False),
        sa.Column("tool_call_id", sa.Integer(), nullable=False),
        sa.Column("approval_type", sa.String(), nullable=False),
        sa.Column("action_name", sa.String(), nullable=True),
        sa.Column("action_input", sa.JSON(), nullable=True),
        sa.Column("risk_level", sa.String(), nullable=True),
        sa.Column("approved_by_user_id", sa.String(), nullable=True),
        sa.Column("rejected_by_user_id", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("decided_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["tool_call_id"], ["tool_calls.id"]),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tool_call_id"),
    )
    op.create_index(op.f("ix_approvals_id"), "approvals", ["id"], unique=False)

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("workspace_id", sa.String(), nullable=False),
        sa.Column("agent_id", sa.String(), nullable=False),
        sa.Column("tool", sa.String(), nullable=False),
        sa.Column("action_name", sa.String(), nullable=True),
        sa.Column("input", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("risk_level", sa.String(), nullable=True),
        sa.Column("approved_by_user_id", sa.String(), nullable=True),
        sa.Column("rejected_by_user_id", sa.String(), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_logs_id"), "audit_logs", ["id"], unique=False)

    workspaces = sa.table(
        "workspaces",
        sa.column("id", sa.String()),
        sa.column("name", sa.String()),
        sa.column("created_at", sa.DateTime()),
    )
    op.bulk_insert(
        workspaces,
        [{"id": "default", "name": "Default Workspace", "created_at": datetime.utcnow()}],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_audit_logs_id"), table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index(op.f("ix_approvals_id"), table_name="approvals")
    op.drop_table("approvals")
    op.drop_index(op.f("ix_tool_calls_id"), table_name="tool_calls")
    op.drop_table("tool_calls")
    op.drop_index(op.f("ix_secrets_name"), table_name="secrets")
    op.drop_index(op.f("ix_secrets_id"), table_name="secrets")
    op.drop_table("secrets")
    op.drop_index(op.f("ix_policies_id"), table_name="policies")
    op.drop_table("policies")
    op.drop_index(op.f("ix_action_secret_policies_id"), table_name="action_secret_policies")
    op.drop_table("action_secret_policies")
    op.drop_index(op.f("ix_action_policies_id"), table_name="action_policies")
    op.drop_table("action_policies")
    op.drop_index(op.f("ix_workspace_memberships_id"), table_name="workspace_memberships")
    op.drop_table("workspace_memberships")
    op.drop_index(op.f("ix_tools_name"), table_name="tools")
    op.drop_table("tools")
    op.drop_index(op.f("ix_agents_id"), table_name="agents")
    op.drop_index(op.f("ix_agents_api_key"), table_name="agents")
    op.drop_table("agents")
    op.drop_index(op.f("ix_actions_name"), table_name="actions")
    op.drop_index(op.f("ix_actions_id"), table_name="actions")
    op.drop_table("actions")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_table("users")
    op.drop_index(op.f("ix_workspaces_id"), table_name="workspaces")
    op.drop_table("workspaces")
