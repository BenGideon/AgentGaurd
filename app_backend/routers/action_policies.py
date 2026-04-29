from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app_backend.core.database import get_db
from app_backend.schemas.policies import ActionPolicyCreate
from app_backend.services import policy_service

router = APIRouter(prefix="/action-policies", tags=["action-policies"])


def get_workspace_id(x_workspace_id: str | None = Header(default=None, alias="x-workspace-id")) -> str:
    return x_workspace_id or "default"


@router.post("")
@router.post("/", include_in_schema=False)
def create_or_replace_action_policy(
    policy: ActionPolicyCreate,
    workspace_id: str = Depends(get_workspace_id),
    db: Session = Depends(get_db),
):
    return policy_service.create_policy(db, workspace_id, policy)


@router.get("")
@router.get("/", include_in_schema=False)
def list_action_policies(workspace_id: str = Depends(get_workspace_id), db: Session = Depends(get_db)):
    return policy_service.list_policies(db, workspace_id)


@router.get("/{agent_id}")
def get_action_policies_for_agent(
    agent_id: str,
    workspace_id: str = Depends(get_workspace_id),
    db: Session = Depends(get_db),
):
    return policy_service.get_policies_by_agent(db, workspace_id, agent_id)
