from fastapi import HTTPException
from sqlalchemy.orm import Session

from app_backend.models.models import ActionSecretPolicy, Secret
from app_backend.schemas.secrets import SecretCreate


def secret_to_dict(secret: Secret) -> dict:
    return {
        "id": secret.id,
        "workspace_id": secret.workspace_id,
        "name": secret.name,
        "description": secret.description,
        "created_at": secret.created_at,
    }


def create_secret(db: Session, workspace_id: str, payload: SecretCreate) -> dict:
    if db.query(Secret).filter(Secret.name == payload.name, Secret.workspace_id == workspace_id).first():
        raise HTTPException(status_code=400, detail="Secret already exists")

    db_secret = Secret(
        name=payload.name,
        workspace_id=workspace_id,
        value=payload.value,
        description=payload.description,
    )
    db.add(db_secret)
    db.commit()
    db.refresh(db_secret)
    return secret_to_dict(db_secret)


def list_secrets(db: Session, workspace_id: str) -> list[dict]:
    secrets = db.query(Secret).filter(Secret.workspace_id == workspace_id).order_by(Secret.name).all()
    return [secret_to_dict(secret) for secret in secrets]


def delete_secret(db: Session, workspace_id: str, name: str) -> dict:
    secret = db.query(Secret).filter(Secret.name == name, Secret.workspace_id == workspace_id).first()
    if not secret:
        raise HTTPException(status_code=404, detail="Secret not found")

    db.delete(secret)
    db.commit()
    return {"status": "deleted", "name": name}


def get_secret_value(db: Session, workspace_id: str, name: str) -> str | None:
    secret = get_secret(db, name, workspace_id)
    return secret.value if secret else None


def get_secret(db: Session, name: str, workspace_id: str) -> Secret | None:
    return db.query(Secret).filter(Secret.workspace_id == workspace_id, Secret.name == name).first()


def get_action_secret_policy(
    db: Session,
    workspace_id: str,
    agent_id: str,
    action_name: str,
) -> ActionSecretPolicy | None:
    return (
        db.query(ActionSecretPolicy)
        .filter(
            ActionSecretPolicy.workspace_id == workspace_id,
            ActionSecretPolicy.agent_id == agent_id,
            ActionSecretPolicy.action_name == action_name,
        )
        .first()
    )


def secret_is_allowed(policy: ActionSecretPolicy | None, secret_name: str) -> bool:
    return bool(policy and secret_name in (policy.allowed_secrets or []))
