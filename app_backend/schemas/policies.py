from typing import Any

from pydantic import BaseModel


class ActionPolicyCreate(BaseModel):
    agent_id: str
    action_name: str
    effect: str
    conditions: dict[str, Any] | None = None
    priority: int = 0


class ActionSecretPolicyCreate(BaseModel):
    agent_id: str
    action_name: str
    allowed_secrets: list[str]


class PolicyCreate(BaseModel):
    agent_id: str
    allowed_tools: list[str] = []
    approval_required_tools: list[str] = []
    blocked_tools: list[str] = []


class PolicyUpdate(BaseModel):
    agent_id: str | None = None
    allowed_tools: list[str] = []
    approval_required_tools: list[str] = []
    blocked_tools: list[str] = []
