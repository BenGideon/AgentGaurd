from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app_backend.models.models import Action, Agent, Approval, ToolCall
from app_backend.schemas.actions import ActionCreate
from app_backend.services.action_executor import ensure_tool_result_success, execute_action
from app_backend.services.api_proxy import validate_action_secret_access
from app_backend.services.audit_service import create_audit_log
from app_backend.services.policy_engine import evaluate_policy
from app_backend.services.risk_engine import calculate_risk
from app_backend.services.workspace_service import ensure_workspace


VALID_EXECUTOR_TYPES = ["gmail_draft", "mock", "webhook", "api_proxy"]


def action_to_dict(action: Action) -> dict[str, Any]:
    return {
        "id": action.id,
        "workspace_id": action.workspace_id,
        "name": action.name,
        "description": action.description,
        "input_schema": action.input_schema,
        "executor_type": action.executor_type,
        "risk_level": action.risk_level,
        "created_at": action.created_at,
    }


def create_action(db: Session, workspace_id: str, action: ActionCreate) -> dict[str, Any]:
    ensure_workspace(db, workspace_id)
    if db.query(Action).filter(Action.name == action.name, Action.workspace_id == workspace_id).first():
        raise HTTPException(status_code=400, detail="Action already exists")
    if action.executor_type not in VALID_EXECUTOR_TYPES:
        raise HTTPException(status_code=400, detail="Invalid executor_type")

    db_action = Action(
        name=action.name,
        workspace_id=workspace_id,
        description=action.description,
        input_schema=action.input_schema,
        executor_type=action.executor_type,
        risk_level=action.risk_level or "medium",
    )
    db.add(db_action)
    db.commit()
    db.refresh(db_action)
    return action_to_dict(db_action)


def list_actions(db: Session, workspace_id: str) -> list[dict[str, Any]]:
    actions = db.query(Action).filter(Action.workspace_id == workspace_id).order_by(Action.name).all()
    return [action_to_dict(action) for action in actions]


def get_action(db: Session, workspace_id: str, action_name: str) -> dict[str, Any]:
    action = db.query(Action).filter(Action.name == action_name, Action.workspace_id == workspace_id).first()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    return action_to_dict(action)


def process_action_call(
    agent: Agent,
    action_name: str,
    input_data: dict[str, Any],
    db: Session,
) -> dict[str, Any]:
    action = (
        db.query(Action)
        .filter(Action.name == action_name, Action.workspace_id == agent.workspace_id)
        .first()
    )
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    risk_level = calculate_risk(action, input_data)
    effect, policy_match = evaluate_policy(agent, action, input_data, risk_level, db)
    secret_violation = None
    if effect != "block" and action.executor_type == "api_proxy":
        secret_violation = validate_action_secret_access(
            agent.id,
            action.name,
            input_data,
            agent.workspace_id,
            db,
        )

    tool_call = ToolCall(
        agent_id=agent.id,
        workspace_id=agent.workspace_id,
        tool=action.name,
        input=input_data,
        status=(
            "blocked"
            if effect == "block" or secret_violation
            else "pending"
            if effect == "approval_required"
            else "completed"
        ),
    )
    db.add(tool_call)
    db.flush()

    if secret_violation:
        create_audit_log(
            db,
            tool_call,
            action_name=action.name,
            risk_level=risk_level,
            status="blocked",
            policy_match=policy_match,
            policy_effect=effect,
        )
        db.commit()
        return {
            "status": "blocked",
            "message": secret_violation["message"],
            "action_call_id": tool_call.id,
            "risk_level": risk_level,
            "policy_match": policy_match,
        }

    if effect == "block":
        create_audit_log(
            db,
            tool_call,
            action_name=action.name,
            risk_level=risk_level,
            status="blocked",
            policy_match=policy_match,
            policy_effect=effect,
        )
        db.commit()
        return {
            "status": "blocked",
            "action_call_id": tool_call.id,
            "risk_level": risk_level,
            "policy_match": policy_match,
        }

    if effect == "approval_required":
        approval = Approval(
            tool_call_id=tool_call.id,
            workspace_id=agent.workspace_id,
            agent_id=agent.id,
            approval_type="action",
            action_name=action.name,
            action_input=input_data,
            original_input=input_data,
            current_input=input_data,
            risk_level=risk_level,
            status="pending",
        )
        db.add(approval)
        create_audit_log(
            db,
            tool_call,
            action_name=action.name,
            risk_level=risk_level,
            status="pending_approval",
            policy_match=policy_match,
            policy_effect=effect,
        )
        db.commit()
        db.refresh(approval)
        return {
            "status": "pending_approval",
            "action_call_id": tool_call.id,
            "approval_id": approval.id,
            "risk_level": risk_level,
            "policy_match": policy_match,
        }

    if effect == "allow":
        result = execute_action(
            action,
            input_data,
            db,
            agent_id=agent.id,
            workspace_id=agent.workspace_id,
        )
        if isinstance(result, dict) and result.get("status") == "blocked":
            tool_call.status = "blocked"
            create_audit_log(
                db,
                tool_call,
                action_name=action.name,
                risk_level=risk_level,
                status="blocked",
                policy_match=policy_match,
                policy_effect=effect,
            )
            db.commit()
            return {
                "status": "blocked",
                "message": result.get("message"),
                "action_call_id": tool_call.id,
                "risk_level": risk_level,
                "policy_match": policy_match,
            }
        ensure_tool_result_success(result)
        create_audit_log(
            db,
            tool_call,
            action_name=action.name,
            risk_level=risk_level,
            status="completed",
            execution_result=result,
            policy_match=policy_match,
            policy_effect=effect,
        )
        db.commit()
        return {
            "status": "completed",
            "action_call_id": tool_call.id,
            "risk_level": risk_level,
            "policy_match": policy_match,
            "result": result,
        }

    create_audit_log(
        db,
        tool_call,
        action_name=action.name,
        risk_level=risk_level,
        status="blocked",
        policy_match=policy_match,
        policy_effect=effect,
    )
    db.commit()
    return {
        "status": "blocked",
        "action_call_id": tool_call.id,
        "risk_level": risk_level,
        "policy_match": policy_match,
    }
