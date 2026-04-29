from fastapi import HTTPException
from sqlalchemy.orm import Session

from app_backend.models.models import Tool
from app_backend.schemas.tools import ToolCreate
from app_backend.services.workspace_service import ensure_workspace


def create_tool(db: Session, workspace_id: str, tool: ToolCreate) -> Tool:
    ensure_workspace(db, workspace_id)
    if db.query(Tool).filter(Tool.name == tool.name, Tool.workspace_id == workspace_id).first():
        raise HTTPException(status_code=400, detail="Tool already exists")

    db_tool = Tool(
        name=tool.name,
        workspace_id=workspace_id,
        description=tool.description,
        input_schema=tool.input_schema,
    )
    db.add(db_tool)
    db.commit()
    db.refresh(db_tool)
    return db_tool


def list_tools(db: Session, workspace_id: str) -> list[Tool]:
    return db.query(Tool).filter(Tool.workspace_id == workspace_id).order_by(Tool.name).all()
