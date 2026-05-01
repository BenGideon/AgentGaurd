from datetime import datetime
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app_backend.core.security import APPROVER_ROLES
from app_backend.models.models import Action, Approval, ToolCall
from app_backend.services.action_executor import ensure_tool_result_success, execute_action, execute_tool
from app_backend.services.alert_service import trigger_alert
from app_backend.services.audit_service import create_audit_log
from app_backend.utils.redaction import redact_sensitive_data
from app_backend.utils.schema import validate_input_against_schema


def ensure_pending_approval(approval: Approval) -> None:
    if approval.status != "pending":
        raise HTTPException(status_code=400, detail="Approval is not pending")


def approval_to_dict(approval: Approval) -> dict[str, Any]:
    display_input = approval.current_input or approval.action_input or approval.tool_call.input
    original_input = approval.original_input or approval.tool_call.input
    return {
        "id": approval.id,
        "workspace_id": approval.workspace_id,
        "status": approval.status,
        "agent_id": approval.agent_id or approval.tool_call.agent_id,
        "tool": approval.tool_call.tool,
        "action_name": approval.action_name,
        "input": redact_sensitive_data(display_input),
        "original_input": redact_sensitive_data(original_input),
        "current_input": redact_sensitive_data(display_input),
        "timestamp": approval.tool_call.timestamp,
        "created_at": approval.created_at,
        "tool_call_id": approval.tool_call_id,
        "approval_type": approval.approval_type,
        "risk_level": approval.risk_level,
        "approved_by_user_id": approval.approved_by_user_id,
        "approved_at": approval.approved_at,
        "rejected_by_user_id": approval.rejected_by_user_id,
        "rejected_at": approval.rejected_at,
        "execution_result": redact_sensitive_data(approval.execution_result),
    }


def require_approver_role(current: dict[str, Any], action: str) -> None:
    if current["role"] not in APPROVER_ROLES:
        raise HTTPException(status_code=403, detail=f"Only admin or reviewer can {action}")


def get_approval_or_404(db: Session, workspace_id: str, approval_id: int) -> Approval:
    approval = db.query(Approval).filter(Approval.id == approval_id, Approval.workspace_id == workspace_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    return approval


def list_approvals(db: Session, workspace_id: str, status: str | None = "pending") -> list[dict[str, Any]]:
    query = db.query(Approval).join(ToolCall).filter(Approval.workspace_id == workspace_id)
    if status:
        query = query.filter(Approval.status == status)

    approvals = query.order_by(Approval.created_at.desc()).all()
    return [approval_to_dict(approval) for approval in approvals]


def update_approval_input(
    db: Session,
    workspace_id: str,
    approval_id: int,
    input_data: dict[str, Any],
    current: dict[str, Any],
) -> dict[str, Any]:
    require_approver_role(current, "edit approvals")
    approval = get_approval_or_404(db, workspace_id, approval_id)
    if approval.status != "pending":
        raise HTTPException(status_code=400, detail="Only pending approvals can be edited")

    if approval.approval_type == "action" and approval.action_name:
        action = (
            db.query(Action)
            .filter(Action.name == approval.action_name, Action.workspace_id == workspace_id)
            .first()
        )
        if not action:
            raise HTTPException(status_code=404, detail="Action not found")
        validate_input_against_schema(input_data, action.input_schema)

    approval.current_input = input_data
    approval.action_input = input_data
    db.commit()
    db.refresh(approval)
    return approval_to_dict(approval)


def approve_approval(
    db: Session,
    workspace_id: str,
    approval_id: int,
    current: dict[str, Any],
) -> dict[str, Any]:
    require_approver_role(current, "approve")
    approval = get_approval_or_404(db, workspace_id, approval_id)
    if approval.status != "pending":
        raise HTTPException(status_code=400, detail="Approval already decided")

    tool_call = approval.tool_call
    final_input = approval.current_input or approval.action_input or tool_call.input
    original_input = approval.original_input or approval.action_input or tool_call.input

    if approval.approval_type == "action":
        action = (
            db.query(Action)
            .filter(Action.name == approval.action_name, Action.workspace_id == workspace_id)
            .first()
        )
        if not action:
            raise HTTPException(status_code=404, detail="Action not found")
        tool_result = execute_action(
            action,
            final_input,
            db,
            agent_id=tool_call.agent_id,
            workspace_id=workspace_id,
        )
        if isinstance(tool_result, dict) and tool_result.get("status") == "blocked":
            approval.status = "blocked"
            approval.decided_at = datetime.utcnow()
            tool_call.status = "blocked"
            create_audit_log(
                db,
                tool_call,
                action_name=action.name,
                risk_level=approval.risk_level,
                status="blocked",
            )
            db.commit()
            return {
                "status": "blocked",
                "approval_type": "action",
                "action_call_id": tool_call.id,
                "risk_level": approval.risk_level,
                "message": tool_result.get("message"),
                "result": tool_result,
                "tool_result": tool_result,
            }
        ensure_tool_result_success(tool_result)

        approved_at = datetime.utcnow()
        approval.status = "completed"
        approval.approved_by_user_id = current["user"].id
        approval.approved_at = approved_at
        approval.decided_at = approved_at
        approval.execution_result = redact_sensitive_data(tool_result)
        approval.current_input = final_input
        tool_call.status = "completed"
        create_audit_log(
            db,
            tool_call,
            action_name=action.name,
            risk_level=approval.risk_level,
            status="completed",
            approved_by_user_id=current["user"].id,
            original_input=original_input,
            final_input=final_input,
            execution_result=tool_result,
            approved_at=approved_at,
        )

        db.commit()
        trigger_alert(
            "approved",
            {
                "agent_id": tool_call.agent_id,
                "action": action.name,
                "approval_id": approval.id,
                "risk_level": approval.risk_level,
                "input": final_input,
                "result": tool_result,
                "approved_by_user_id": current["user"].id,
            },
            workspace_id,
        )
        return {
            "status": "completed",
            "approval_type": "action",
            "action_call_id": tool_call.id,
            "risk_level": approval.risk_level,
            "result": tool_result,
            "tool_result": tool_result,
        }

    tool_result = execute_tool(tool_call.tool, final_input)
    ensure_tool_result_success(tool_result)

    approved_at = datetime.utcnow()
    approval.status = "completed"
    approval.approved_by_user_id = current["user"].id
    approval.approved_at = approved_at
    approval.decided_at = approved_at
    approval.execution_result = redact_sensitive_data(tool_result)
    tool_call.status = "completed"
    create_audit_log(
        db,
        tool_call,
        approved_by_user_id=current["user"].id,
        original_input=original_input,
        final_input=final_input,
        execution_result=tool_result,
        approved_at=approved_at,
    )

    db.commit()
    trigger_alert(
        "approved",
        {
            "agent_id": tool_call.agent_id,
            "action": tool_call.tool,
            "approval_id": approval.id,
            "risk_level": approval.risk_level,
            "input": final_input,
            "result": tool_result,
            "approved_by_user_id": current["user"].id,
        },
        workspace_id,
    )
    return {
        "status": "completed",
        "tool_call_id": tool_call.id,
        "tool_result": tool_result,
    }


def reject_approval(
    db: Session,
    workspace_id: str,
    approval_id: int,
    current: dict[str, Any],
) -> dict[str, Any]:
    require_approver_role(current, "reject")
    approval = get_approval_or_404(db, workspace_id, approval_id)
    if approval.status != "pending":
        raise HTTPException(status_code=400, detail="Approval already decided")

    rejected_at = datetime.utcnow()
    approval.status = "rejected"
    approval.rejected_by_user_id = current["user"].id
    approval.rejected_at = rejected_at
    approval.decided_at = rejected_at
    approval.tool_call.status = "rejected"
    create_audit_log(
        db,
        approval.tool_call,
        action_name=approval.action_name if approval.approval_type == "action" else None,
        risk_level=approval.risk_level,
        status="rejected",
        rejected_by_user_id=current["user"].id,
        original_input=approval.original_input or approval.tool_call.input,
        final_input=approval.current_input or approval.tool_call.input,
        rejected_at=rejected_at,
    )

    db.commit()
    return {"status": "rejected", "tool_call_id": approval.tool_call.id}
