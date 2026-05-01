from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app_backend.core.database import Base


class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    email = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class WorkspaceMembership(Base):
    __tablename__ = "workspace_memberships"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    role = Column(String, nullable=False)


class Agent(Base):
    __tablename__ = "agents"

    id = Column(String, primary_key=True, index=True)
    workspace_id = Column(String, ForeignKey("workspaces.id"), default="default", nullable=False)
    name = Column(String, nullable=False)
    api_key = Column(String, unique=True, index=True, nullable=False)

    policy = relationship("Policy", back_populates="agent", uselist=False)
    tool_calls = relationship("ToolCall", back_populates="agent")


class Tool(Base):
    __tablename__ = "tools"
    __table_args__ = (UniqueConstraint("workspace_id", "name", name="uq_tools_workspace_name"),)

    name = Column(String, primary_key=True, index=True)
    workspace_id = Column(String, ForeignKey("workspaces.id"), primary_key=True, default="default", nullable=False)
    description = Column(String, nullable=False)
    input_schema = Column(JSON, nullable=True)


class Action(Base):
    __tablename__ = "actions"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(String, ForeignKey("workspaces.id"), default="default", nullable=False)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=False)
    input_schema = Column(JSON, nullable=True)
    executor_type = Column(String, nullable=False)
    risk_level = Column(String, default="medium", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ActionPolicy(Base):
    __tablename__ = "action_policies"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(String, ForeignKey("workspaces.id"), default="default", nullable=False)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False)
    action_name = Column(String, nullable=False)
    effect = Column(String, nullable=False)
    conditions = Column(JSON, nullable=True)
    priority = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ActionSecretPolicy(Base):
    __tablename__ = "action_secret_policies"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(String, ForeignKey("workspaces.id"), default="default", nullable=False)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False)
    action_name = Column(String, nullable=False)
    allowed_secrets = Column(JSON, default=list, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Secret(Base):
    __tablename__ = "secrets"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(String, ForeignKey("workspaces.id"), default="default", nullable=False)
    name = Column(String, index=True, nullable=False)
    value = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Connector(Base):
    __tablename__ = "connectors"
    __table_args__ = (UniqueConstraint("workspace_id", "provider", name="uq_connectors_workspace_provider"),)

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=False)
    provider = Column(String, nullable=False)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=True)
    scopes = Column(Text, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    connected_email = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class AlertConfig(Base):
    __tablename__ = "alerts_config"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(String, ForeignKey("workspaces.id"), default="default", nullable=False)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    events = Column(JSON, default=list, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Policy(Base):
    __tablename__ = "policies"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(String, ForeignKey("workspaces.id"), default="default", nullable=False)
    agent_id = Column(String, ForeignKey("agents.id"), unique=True, nullable=False)
    allowed_tools = Column(JSON, default=list, nullable=False)
    approval_required_tools = Column(JSON, default=list, nullable=False)
    blocked_tools = Column(JSON, default=list, nullable=False)

    agent = relationship("Agent", back_populates="policy")


class ToolCall(Base):
    __tablename__ = "tool_calls"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(String, ForeignKey("workspaces.id"), default="default", nullable=False)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False)
    tool = Column(String, nullable=False)
    input = Column(JSON, nullable=False)
    status = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    agent = relationship("Agent", back_populates="tool_calls")
    approval = relationship("Approval", back_populates="tool_call", uselist=False)


class Approval(Base):
    __tablename__ = "approvals"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(String, ForeignKey("workspaces.id"), default="default", nullable=False)
    tool_call_id = Column(Integer, ForeignKey("tool_calls.id"), unique=True, nullable=False)
    agent_id = Column(String, nullable=True)
    approval_type = Column(String, default="tool", nullable=False)
    action_name = Column(String, nullable=True)
    action_input = Column(JSON, nullable=True)
    original_input = Column(JSON, nullable=True)
    current_input = Column(JSON, nullable=True)
    risk_level = Column(String, nullable=True)
    approved_by_user_id = Column(String, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejected_by_user_id = Column(String, nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    execution_result = Column(JSON, nullable=True)
    status = Column(String, default="pending", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    decided_at = Column(DateTime, nullable=True)

    tool_call = relationship("ToolCall", back_populates="approval")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(String, ForeignKey("workspaces.id"), default="default", nullable=False)
    agent_id = Column(String, nullable=False)
    tool = Column(String, nullable=False)
    action_name = Column(String, nullable=True)
    input = Column(JSON, nullable=False)
    original_input = Column(JSON, nullable=True)
    final_input = Column(JSON, nullable=True)
    status = Column(String, nullable=False)
    risk_level = Column(String, nullable=True)
    approved_by_user_id = Column(String, nullable=True)
    rejected_by_user_id = Column(String, nullable=True)
    execution_result = Column(JSON, nullable=True)
    policy_match = Column(JSON, nullable=True)
    policy_effect = Column(String, nullable=True)
    matched_policy_id = Column(Integer, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
