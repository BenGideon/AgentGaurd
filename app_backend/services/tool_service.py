from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app_backend.models.models import Agent, Approval, Policy, Tool, ToolCall
from app_backend.services.action_executor import ensure_tool_result_success, execute_tool
from app_backend.services.audit_service import create_audit_log


def ensure_agent_and_tool_exist(db: Session, agent_id: str, tool_name: str, workspace_id: str) -> None:
    if not db.query(Agent).filter(Agent.id == agent_id, Agent.workspace_id == workspace_id).first():
        raise HTTPException(status_code=404, detail="Agent not found")
    if not db.query(Tool).filter(Tool.name == tool_name, Tool.workspace_id == workspace_id).first():
        raise HTTPException(status_code=404, detail="Tool not found")


def get_available_tools_for_agent(agent: Agent, db: Session) -> list[dict[str, Any]]:
    policy = (
        db.query(Policy)
        .filter(Policy.agent_id == agent.id, Policy.workspace_id == agent.workspace_id)
        .first()
    )
    if not policy:
        return []

    allowed_names = set(policy.allowed_tools or [])
    approval_required_names = set(policy.approval_required_tools or [])
    blocked_names = set(policy.blocked_tools or [])
    visible_names = (allowed_names | approval_required_names) - blocked_names

    if not visible_names:
        return []

    tools = (
        db.query(Tool)
        .filter(Tool.workspace_id == agent.workspace_id, Tool.name.in_(visible_names))
        .order_by(Tool.name)
        .all()
    )
    return [
        {
            "name": tool.name,
            "description": tool.description,
            "access": "approval_required" if tool.name in approval_required_names else "allowed",
            "input_schema": tool.input_schema,
        }
        for tool in tools
    ]


def process_tool_call(
    agent: Agent,
    tool_name: str,
    input_data: dict[str, Any],
    db: Session,
) -> dict[str, Any]:
    ensure_agent_and_tool_exist(db, agent.id, tool_name, agent.workspace_id)

    policy = (
        db.query(Policy)
        .filter(Policy.agent_id == agent.id, Policy.workspace_id == agent.workspace_id)
        .first()
    )

    status = "blocked"
    if policy:
        if tool_name in policy.blocked_tools:
            status = "blocked"
        elif tool_name in policy.approval_required_tools:
            status = "pending"
        elif tool_name in policy.allowed_tools:
            status = "completed"

    tool_call = ToolCall(
        agent_id=agent.id,
        workspace_id=agent.workspace_id,
        tool=tool_name,
        input=input_data,
        status=status,
    )
    db.add(tool_call)
    db.flush()

    if status == "blocked":
        create_audit_log(db, tool_call)
        db.commit()
        return {"status": "blocked", "tool_call_id": tool_call.id}

    if status == "pending":
        approval = Approval(
            tool_call_id=tool_call.id,
            workspace_id=agent.workspace_id,
            agent_id=agent.id,
            action_name=tool_name,
            original_input=input_data,
            current_input=input_data,
            status="pending",
        )
        db.add(approval)
        create_audit_log(db, tool_call)
        db.commit()
        db.refresh(approval)
        return {
            "status": "pending_approval",
            "tool_call_id": tool_call.id,
            "approval_id": approval.id,
        }

    tool_result = execute_tool(tool_name, input_data)
    ensure_tool_result_success(tool_result)
    create_audit_log(db, tool_call, execution_result=tool_result)
    db.commit()
    return {
        "status": "completed",
        "tool_call_id": tool_call.id,
        "tool_result": tool_result,
    }
