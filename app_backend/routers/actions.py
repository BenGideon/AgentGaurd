from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app_backend.core.database import get_db
from app_backend.models.models import Agent
from app_backend.schemas.actions import ActionCallCreate, ActionCreate
from app_backend.services import actions_service
from app_backend.services.workspace_service import ensure_workspace

router = APIRouter(prefix="/actions", tags=["actions"])


def get_workspace_id(x_workspace_id: str | None = Header(default=None, alias="x-workspace-id")) -> str:
    return x_workspace_id or "default"


def get_current_agent(
    x_agent_key: str | None = Header(default=None, alias="x-agent-key"),
    workspace_id: str = Depends(get_workspace_id),
    db: Session = Depends(get_db),
) -> Agent:
    if not x_agent_key:
        raise HTTPException(status_code=401, detail="Missing x-agent-key header")

    ensure_workspace(db, workspace_id)
    agent = (
        db.query(Agent)
        .filter(Agent.api_key == x_agent_key, Agent.workspace_id == workspace_id)
        .first()
    )
    if not agent:
        raise HTTPException(status_code=401, detail="Invalid x-agent-key header")

    return agent


@router.post("")
@router.post("/", include_in_schema=False)
def create_action(
    action: ActionCreate,
    workspace_id: str = Depends(get_workspace_id),
    db: Session = Depends(get_db),
):
    return actions_service.create_action(db, workspace_id, action)


@router.get("")
@router.get("/", include_in_schema=False)
def list_actions(workspace_id: str = Depends(get_workspace_id), db: Session = Depends(get_db)):
    return actions_service.list_actions(db, workspace_id)


@router.post("/call")
def call_action(
    request: ActionCallCreate,
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db),
):
    return actions_service.process_action_call(current_agent, request.action, request.input, db)


@router.get("/{action_name}")
def get_action(
    action_name: str,
    workspace_id: str = Depends(get_workspace_id),
    db: Session = Depends(get_db),
):
    return actions_service.get_action(db, workspace_id, action_name)
