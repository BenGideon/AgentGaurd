from sqlalchemy import func
from sqlalchemy.orm import Session

from app_backend.models.models import Approval, ToolCall


def compute_stats(db: Session, workspace_id: str) -> dict:
    status_counts = dict(
        db.query(ToolCall.status, func.count(ToolCall.id))
        .filter(ToolCall.workspace_id == workspace_id)
        .group_by(ToolCall.status)
        .all()
    )
    pending_approvals = (
        db.query(Approval)
        .filter(Approval.status == "pending", Approval.workspace_id == workspace_id)
        .count()
    )

    return {
        "total_tool_calls": db.query(ToolCall).filter(ToolCall.workspace_id == workspace_id).count(),
        "pending_approvals": pending_approvals,
        "completed_calls": status_counts.get("completed", 0),
        "blocked_calls": status_counts.get("blocked", 0),
    }
