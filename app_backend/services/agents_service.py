import secrets

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app_backend.models.models import Agent
from app_backend.schemas.agents import AgentCreate
from app_backend.services.workspace_service import ensure_workspace


def generate_agent_api_key() -> str:
    return f"ag_test_{secrets.token_urlsafe(24)}"


def create_agent(db: Session, workspace_id: str, agent: AgentCreate) -> Agent:
    ensure_workspace(db, workspace_id)
    if db.query(Agent).filter(Agent.id == agent.id, Agent.workspace_id == workspace_id).first():
        raise HTTPException(status_code=400, detail="Agent already exists")

    api_key = agent.api_key or generate_agent_api_key()
    if db.query(Agent).filter(Agent.api_key == api_key, Agent.workspace_id == workspace_id).first():
        raise HTTPException(status_code=400, detail="Agent API key already exists")

    db_agent = Agent(id=agent.id, workspace_id=workspace_id, name=agent.name, api_key=api_key)
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)
    return db_agent


def list_agents(db: Session, workspace_id: str) -> list[Agent]:
    return db.query(Agent).filter(Agent.workspace_id == workspace_id).order_by(Agent.id).all()
