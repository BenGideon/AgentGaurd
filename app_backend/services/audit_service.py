from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app_backend.core.config import settings
from app_backend.models.models import AuditLog, ToolCall
from app_backend.utils.redaction import redact_sensitive_data


def add_audit_log(db: Session, **fields: Any) -> AuditLog:
    log = AuditLog(**fields)
    db.add(log)
    return log


def create_audit_log(
    db: Session,
    tool_call: ToolCall,
    action_name: str | None = None,
    risk_level: str | None = None,
    status: str | None = None,
    approved_by_user_id: str | None = None,
    rejected_by_user_id: str | None = None,
    original_input: dict[str, Any] | None = None,
    final_input: dict[str, Any] | None = None,
    execution_result: dict[str, Any] | None = None,
    policy_match: dict[str, Any] | None = None,
    policy_effect: str | None = None,
    approved_at: datetime | None = None,
    rejected_at: datetime | None = None,
) -> AuditLog:
    audit_log = AuditLog(
        workspace_id=tool_call.workspace_id,
        agent_id=tool_call.agent_id,
        tool=tool_call.tool,
        action_name=action_name,
        input=redact_sensitive_data(tool_call.input),
        original_input=redact_sensitive_data(original_input if original_input is not None else tool_call.input),
        final_input=redact_sensitive_data(final_input if final_input is not None else tool_call.input),
        status=status or tool_call.status,
        risk_level=risk_level,
        approved_by_user_id=approved_by_user_id,
        rejected_by_user_id=rejected_by_user_id,
        execution_result=redact_sensitive_data(execution_result),
        policy_match=policy_match,
        policy_effect=policy_effect,
        matched_policy_id=policy_match.get("policy_id") if policy_match else None,
        approved_at=approved_at,
        rejected_at=rejected_at,
    )
    db.add(audit_log)
    return audit_log


def inferred_tool_result(log: AuditLog) -> dict[str, Any] | None:
    log_name = log.action_name or log.tool
    if log.status != "completed":
        return None
    if log.tool != "create_gmail_draft" and "gmail" not in log_name:
        return None

    if settings.GMAIL_CONNECTOR_MODE.lower() == "mock":
        return {
            "status": "success",
            "message": "Mock Gmail draft created",
            "draft": log.input,
        }

    return {
        "status": "success",
        "message": "Gmail draft created",
    }


def audit_log_to_dict(log: AuditLog) -> dict[str, Any]:
    return {
        "id": log.id,
        "workspace_id": log.workspace_id,
        "agent_id": log.agent_id,
        "tool": log.tool,
        "action_name": log.action_name,
        "input": log.input,
        "original_input": log.original_input,
        "final_input": log.final_input,
        "status": log.status,
        "risk_level": log.risk_level,
        "approved_by_user_id": log.approved_by_user_id,
        "rejected_by_user_id": log.rejected_by_user_id,
        "execution_result": log.execution_result,
        "policy_match": log.policy_match,
        "policy_effect": log.policy_effect,
        "matched_policy_id": log.matched_policy_id,
        "approved_at": log.approved_at,
        "rejected_at": log.rejected_at,
        "timestamp": log.timestamp,
        "tool_result": log.execution_result or inferred_tool_result(log),
    }


def list_logs(db: Session, workspace_id: str) -> list[dict[str, Any]]:
    logs = (
        db.query(AuditLog)
        .filter(AuditLog.workspace_id == workspace_id)
        .order_by(AuditLog.timestamp.desc())
        .all()
    )
    return [audit_log_to_dict(log) for log in logs]
