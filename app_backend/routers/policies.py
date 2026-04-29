from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app_backend.core.database import get_db
from app_backend.core.security import get_workspace_id
from app_backend.schemas.policies import PolicyCreate, PolicyUpdate
from app_backend.services import policies_service

router = APIRouter(prefix="/policies", tags=["policies"])


@router.post("")
@router.post("/", include_in_schema=False)
def create_or_replace_policy(
    policy: PolicyCreate,
    workspace_id: str = Depends(get_workspace_id),
    db: Session = Depends(get_db),
):
    return policies_service.create_or_replace_policy(db, workspace_id, policy)


@router.get("")
@router.get("/", include_in_schema=False)
def list_policies(workspace_id: str = Depends(get_workspace_id), db: Session = Depends(get_db)):
    return policies_service.list_policies(db, workspace_id)


@router.get("/{agent_id}")
def get_policy(agent_id: str, workspace_id: str = Depends(get_workspace_id), db: Session = Depends(get_db)):
    return policies_service.get_policy(db, workspace_id, agent_id)


@router.put("/{agent_id}")
def update_policy(
    agent_id: str,
    policy: PolicyUpdate,
    workspace_id: str = Depends(get_workspace_id),
    db: Session = Depends(get_db),
):
    return policies_service.update_policy(db, workspace_id, agent_id, policy)
