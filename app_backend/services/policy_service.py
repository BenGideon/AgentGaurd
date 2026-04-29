from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app_backend.models.models import Action, ActionPolicy, Agent
from app_backend.schemas.policies import ActionPolicyCreate
from app_backend.services.workspace_service import ensure_workspace


def action_policy_to_dict(policy: ActionPolicy) -> dict[str, Any]:
    return {
        "id": policy.id,
        "workspace_id": policy.workspace_id,
        "agent_id": policy.agent_id,
        "action_name": policy.action_name,
        "effect": policy.effect,
        "conditions": policy.conditions,
        "priority": policy.priority,
        "created_at": policy.created_at,
    }


def create_policy(db: Session, workspace_id: str, policy: ActionPolicyCreate) -> dict[str, Any]:
    if policy.effect not in ["allow", "approval_required", "block"]:
        raise HTTPException(status_code=400, detail="Invalid policy effect")
    ensure_workspace(db, workspace_id)
    if not db.query(Agent).filter(Agent.id == policy.agent_id, Agent.workspace_id == workspace_id).first():
        raise HTTPException(status_code=404, detail="Agent not found")
    if not db.query(Action).filter(Action.name == policy.action_name, Action.workspace_id == workspace_id).first():
        raise HTTPException(status_code=404, detail="Action not found")

    db_policy = ActionPolicy(
        agent_id=policy.agent_id,
        workspace_id=workspace_id,
        action_name=policy.action_name,
        effect=policy.effect,
        conditions=policy.conditions,
        priority=policy.priority,
    )
    db.add(db_policy)
    db.commit()
    db.refresh(db_policy)
    return action_policy_to_dict(db_policy)


def list_policies(db: Session, workspace_id: str) -> list[dict[str, Any]]:
    policies = (
        db.query(ActionPolicy)
        .filter(ActionPolicy.workspace_id == workspace_id)
        .order_by(ActionPolicy.agent_id, ActionPolicy.action_name, ActionPolicy.priority.desc())
        .all()
    )
    return [action_policy_to_dict(policy) for policy in policies]


def get_policies_by_agent(db: Session, workspace_id: str, agent_id: str) -> list[dict[str, Any]]:
    if not db.query(Agent).filter(Agent.id == agent_id, Agent.workspace_id == workspace_id).first():
        raise HTTPException(status_code=404, detail="Agent not found")

    policies = (
        db.query(ActionPolicy)
        .filter(ActionPolicy.agent_id == agent_id, ActionPolicy.workspace_id == workspace_id)
        .order_by(ActionPolicy.action_name, ActionPolicy.priority.desc())
        .all()
    )
    return [action_policy_to_dict(policy) for policy in policies]
