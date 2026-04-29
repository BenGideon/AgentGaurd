from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app_backend.core.database import get_db
from app_backend.core.security import get_workspace_id
from app_backend.schemas.agents import AgentCreate
from app_backend.services import agents_service

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("")
@router.post("/", include_in_schema=False)
def register_agent(
    agent: AgentCreate,
    workspace_id: str = Depends(get_workspace_id),
    db: Session = Depends(get_db),
):
    return agents_service.create_agent(db, workspace_id, agent)


@router.get("")
@router.get("/", include_in_schema=False)
def list_agents(workspace_id: str = Depends(get_workspace_id), db: Session = Depends(get_db)):
    return agents_service.list_agents(db, workspace_id)
