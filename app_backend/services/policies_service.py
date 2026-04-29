from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app_backend.models.models import Agent, Policy
from app_backend.schemas.policies import PolicyCreate, PolicyUpdate
from app_backend.services.workspace_service import ensure_workspace


def policy_to_dict(policy: Policy) -> dict[str, Any]:
    return {
        "agent_id": policy.agent_id,
        "workspace_id": policy.workspace_id,
        "allowed_tools": policy.allowed_tools or [],
        "approval_required_tools": policy.approval_required_tools or [],
        "blocked_tools": policy.blocked_tools or [],
    }


def create_or_replace_policy(db: Session, workspace_id: str, policy: PolicyCreate) -> Policy:
    ensure_workspace(db, workspace_id)
    if not db.query(Agent).filter(Agent.id == policy.agent_id, Agent.workspace_id == workspace_id).first():
        raise HTTPException(status_code=404, detail="Agent not found")

    db_policy = (
        db.query(Policy)
        .filter(Policy.agent_id == policy.agent_id, Policy.workspace_id == workspace_id)
        .first()
    )
    if db_policy:
        db_policy.allowed_tools = policy.allowed_tools
        db_policy.approval_required_tools = policy.approval_required_tools
        db_policy.blocked_tools = policy.blocked_tools
    else:
        db_policy = Policy(**policy.dict(), workspace_id=workspace_id)
        db.add(db_policy)

    db.commit()
    db.refresh(db_policy)
    return db_policy


def list_policies(db: Session, workspace_id: str) -> list[dict[str, Any]]:
    policies = db.query(Policy).filter(Policy.workspace_id == workspace_id).order_by(Policy.agent_id).all()
    return [policy_to_dict(policy) for policy in policies]


def get_policy(db: Session, workspace_id: str, agent_id: str) -> dict[str, Any]:
    if not db.query(Agent).filter(Agent.id == agent_id, Agent.workspace_id == workspace_id).first():
        raise HTTPException(status_code=404, detail="Agent not found")

    policy = db.query(Policy).filter(Policy.agent_id == agent_id, Policy.workspace_id == workspace_id).first()
    if not policy:
        return {
            "agent_id": agent_id,
            "workspace_id": workspace_id,
            "allowed_tools": [],
            "approval_required_tools": [],
            "blocked_tools": [],
        }

    return policy_to_dict(policy)


def update_policy(db: Session, workspace_id: str, agent_id: str, policy: PolicyUpdate) -> dict[str, Any]:
    if policy.agent_id and policy.agent_id != agent_id:
        raise HTTPException(status_code=400, detail="Policy agent_id does not match URL")
    if not db.query(Agent).filter(Agent.id == agent_id, Agent.workspace_id == workspace_id).first():
        raise HTTPException(status_code=404, detail="Agent not found")

    db_policy = db.query(Policy).filter(Policy.agent_id == agent_id, Policy.workspace_id == workspace_id).first()
    if db_policy:
        db_policy.allowed_tools = policy.allowed_tools
        db_policy.approval_required_tools = policy.approval_required_tools
        db_policy.blocked_tools = policy.blocked_tools
    else:
        db_policy = Policy(
            agent_id=agent_id,
            workspace_id=workspace_id,
            allowed_tools=policy.allowed_tools,
            approval_required_tools=policy.approval_required_tools,
            blocked_tools=policy.blocked_tools,
        )
        db.add(db_policy)

    db.commit()
    db.refresh(db_policy)
    return policy_to_dict(db_policy)
