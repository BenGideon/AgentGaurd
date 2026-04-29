from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app_backend.models.models import Action, ActionSecretPolicy, Agent, Secret
from app_backend.schemas.policies import ActionSecretPolicyCreate
from app_backend.services.workspace_service import ensure_workspace


def action_secret_policy_to_dict(policy: ActionSecretPolicy) -> dict[str, Any]:
    return {
        "id": policy.id,
        "workspace_id": policy.workspace_id,
        "agent_id": policy.agent_id,
        "action_name": policy.action_name,
        "allowed_secrets": policy.allowed_secrets or [],
        "created_at": policy.created_at,
    }


def create_secret_policy(db: Session, workspace_id: str, policy: ActionSecretPolicyCreate) -> dict[str, Any]:
    ensure_workspace(db, workspace_id)
    if not db.query(Agent).filter(Agent.id == policy.agent_id, Agent.workspace_id == workspace_id).first():
        raise HTTPException(status_code=404, detail="Agent not found")
    if not db.query(Action).filter(Action.name == policy.action_name, Action.workspace_id == workspace_id).first():
        raise HTTPException(status_code=404, detail="Action not found")

    existing_secret_names = {
        secret.name
        for secret in db.query(Secret)
        .filter(Secret.name.in_(policy.allowed_secrets), Secret.workspace_id == workspace_id)
        .all()
    }
    missing_secret_names = [name for name in policy.allowed_secrets if name not in existing_secret_names]
    if missing_secret_names:
        raise HTTPException(status_code=404, detail=f"Secret not found: {', '.join(missing_secret_names)}")

    allowed_secrets = sorted(set(policy.allowed_secrets))
    db_policy = (
        db.query(ActionSecretPolicy)
        .filter(
            ActionSecretPolicy.agent_id == policy.agent_id,
            ActionSecretPolicy.action_name == policy.action_name,
            ActionSecretPolicy.workspace_id == workspace_id,
        )
        .first()
    )
    if db_policy:
        db_policy.allowed_secrets = allowed_secrets
    else:
        db_policy = ActionSecretPolicy(
            agent_id=policy.agent_id,
            workspace_id=workspace_id,
            action_name=policy.action_name,
            allowed_secrets=allowed_secrets,
        )
        db.add(db_policy)

    db.commit()
    db.refresh(db_policy)
    return action_secret_policy_to_dict(db_policy)


def list_secret_policies(db: Session, workspace_id: str) -> list[dict[str, Any]]:
    policies = (
        db.query(ActionSecretPolicy)
        .filter(ActionSecretPolicy.workspace_id == workspace_id)
        .order_by(ActionSecretPolicy.agent_id, ActionSecretPolicy.action_name)
        .all()
    )
    return [action_secret_policy_to_dict(policy) for policy in policies]


def get_secret_policies_by_agent(db: Session, workspace_id: str, agent_id: str) -> list[dict[str, Any]]:
    if not db.query(Agent).filter(Agent.id == agent_id, Agent.workspace_id == workspace_id).first():
        raise HTTPException(status_code=404, detail="Agent not found")

    policies = (
        db.query(ActionSecretPolicy)
        .filter(ActionSecretPolicy.agent_id == agent_id, ActionSecretPolicy.workspace_id == workspace_id)
        .order_by(ActionSecretPolicy.action_name)
        .all()
    )
    return [action_secret_policy_to_dict(policy) for policy in policies]
