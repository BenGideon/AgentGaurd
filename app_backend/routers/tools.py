from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app_backend.core.database import get_db
from app_backend.core.security import get_current_agent, get_workspace_id
from app_backend.models.models import Agent
from app_backend.schemas.tools import ToolCallCreate, ToolCreate
from app_backend.services import tools_service
from app_backend.services.tool_service import get_available_tools_for_agent, process_tool_call

router = APIRouter(tags=["tools"])


@router.post("/tools")
def register_tool(
    tool: ToolCreate,
    workspace_id: str = Depends(get_workspace_id),
    db: Session = Depends(get_db),
):
    return tools_service.create_tool(db, workspace_id, tool)


@router.get("/tools")
def list_tools(workspace_id: str = Depends(get_workspace_id), db: Session = Depends(get_db)):
    return tools_service.list_tools(db, workspace_id)


@router.get("/agent/tools")
def discover_agent_tools(
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db),
):
    return get_available_tools_for_agent(current_agent, db)


@router.post("/tool-call")
def call_tool(
    request: ToolCallCreate,
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db),
):
    return process_tool_call(current_agent, request.tool, request.input, db)
