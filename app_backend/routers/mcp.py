from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app_backend.core.database import get_db
from app_backend.core.security import get_current_agent
from app_backend.models.models import Agent
from app_backend.schemas.mcp import MCPToolCallCreate
from app_backend.services import mcp_service

router = APIRouter(prefix="/mcp", tags=["mcp"])


@router.post("/tools/list")
def mcp_list_tools(
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db),
):
    return mcp_service.list_mcp_tools(db, current_agent)


@router.post("/tools/call")
def mcp_call_tool(
    request: MCPToolCallCreate,
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db),
):
    return mcp_service.call_mcp_tool(db, current_agent, request.name, request.arguments)
